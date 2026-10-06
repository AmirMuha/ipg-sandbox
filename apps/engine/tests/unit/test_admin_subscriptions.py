"""Admin subscription listing and deactivation (007-plan-deactivation-no-downgrade).

The security property: only an allowlisted account may cancel someone's paid plan, and a
cancelled plan actually drops the project back to free — a 200 that left entitlements intact
would be worse than a refusal, because the admin would believe the workspace was capped.
"""

import asyncio
import uuid
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.adapters.registry import seed_configs
from src.api.app import create_app
from src.models import (
    AdapterConfig,
    Base,
    Project,
    Provider,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    User,
    UserSession,
    utcnow,
)
from src.services.auth import generate_session_token, hash_session_token


def _app_with_paid_project(db_file, emails, *, extra_active=False, sub_status="active"):
    """App + signed-in users + one team-tier project carrying active paid subscription(s)."""
    sync_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sync_engine)
    tokens: dict[str, str] = {}
    sub_ids: list[uuid.UUID] = []
    with Session(sync_engine) as s:
        platform = Project(id=uuid.uuid4(), name="default")
        s.add(platform)
        s.flush()
        s.add_all(
            [
                AdapterConfig(
                    id=uuid.uuid4(),
                    **{**kw, "enabled": kw["provider"] is Provider.zarinpal},
                )
                for kw in seed_configs(platform.id)
            ]
        )
        users = {}
        for email in emails:
            user = User(id=uuid.uuid4(), email=email, password_hash="x")
            s.add(user)
            s.flush()
            token = generate_session_token()
            s.add(
                UserSession(
                    user_id=user.id,
                    token_hash=hash_session_token(token),
                    expires_at=utcnow() + timedelta(days=1),
                )
            )
            tokens[email] = token
            users[email] = user

        buyer = users[emails[-1]]
        project = Project(
            id=uuid.uuid4(),
            name="paid workspace",
            user_id=buyer.id,
            tier=SubscriptionTier.team.value,
            daily_requests_cap=0,
            max_active_adapters=0,
            history_cap=1000,
            webhook_retry_max=3,
            pending_settle_delay_s=5,
            timeout_delay_s=30,
        )
        s.add(project)
        s.flush()
        for _ in range(2 if extra_active else 1):
            sub = Subscription(
                project_id=project.id,
                user_id=buyer.id,
                tier=SubscriptionTier.team.value,
                status=sub_status,
                amount_rial=1_990_000,
                zarinpal_authority=f"A{uuid.uuid4().hex[:20]}",
                started_at=utcnow(),
                expires_at=utcnow() + timedelta(days=30),
            )
            s.add(sub)
            s.flush()
            sub_ids.append(sub.id)
        project_id = project.id
        s.commit()
    sync_engine.dispose()

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    app = create_app()
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return app, engine, tokens, project_id, sub_ids


async def _deactivate(c, sub_id, token):
    headers = {"Content-Type": "application/json"}
    cookies = {"ipg_session": token} if token else None
    return c.post(
        f"/api/v1/admin/subscriptions/{sub_id}/deactivate", headers=headers, cookies=cookies
    )


async def _row(engine, model, pk):
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        return await session.get(model, pk)


async def _assert_project_free(engine, project_id):
    project = await _row(engine, Project, project_id)
    assert project.tier == SubscriptionTier.developer.value
    assert project.daily_requests_cap == 100
    assert project.max_active_adapters == 2


def test_anonymous_is_unauthorized(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, _, _, sub_ids = _app_with_paid_project(
            tmp_path / "anon.db", ["ops@example.com"]
        )
        with TestClient(app) as c:
            r = await _deactivate(c, sub_ids[0], None)
            assert r.status_code == 401, r.text
            r = c.get("/api/v1/admin/subscriptions")
            assert r.status_code == 401, r.text
        await engine.dispose()

    asyncio.run(_test())


def test_signed_in_non_admin_is_forbidden_and_subscription_unchanged(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens, project_id, sub_ids = _app_with_paid_project(
            tmp_path / "no.db", ["ops@example.com", "merchant@example.com"]
        )
        with TestClient(app) as c:
            r = await _deactivate(c, sub_ids[0], tokens["merchant@example.com"])
            assert r.status_code == 403, r.text
            assert r.json()["code"] == "forbidden"
            sub = await _row(engine, Subscription, sub_ids[0])
            assert sub.status == SubscriptionStatus.active.value
            project = await _row(engine, Project, project_id)
            assert project.tier == SubscriptionTier.team.value
        await engine.dispose()

    asyncio.run(_test())


def test_admin_deactivate_cancels_and_reverts_project(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens, project_id, sub_ids = _app_with_paid_project(
            tmp_path / "ok.db", ["ops@example.com", "merchant@example.com"]
        )
        with TestClient(app) as c:
            r = await _deactivate(c, sub_ids[0], tokens["ops@example.com"])
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["subscription"]["status"] == SubscriptionStatus.cancelled.value
            sub = await _row(engine, Subscription, sub_ids[0])
            assert sub.status == SubscriptionStatus.cancelled.value
            await _assert_project_free(engine, project_id)
        await engine.dispose()

    asyncio.run(_test())


def test_deactivate_non_active_is_rejected(monkeypatch, tmp_path):
    """Only paid-and-running plans are admin-deactivatable; pending/expired are gateway flow."""
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens, project_id, sub_ids = _app_with_paid_project(
            tmp_path / "pending.db", ["ops@example.com"], sub_status="expired"
        )
        with TestClient(app) as c:
            r = await _deactivate(c, sub_ids[0], tokens["ops@example.com"])
            assert r.status_code == 409, r.text
            assert r.json()["code"] == "unsupported_operation"
            sub = await _row(engine, Subscription, sub_ids[0])
            assert sub.status == SubscriptionStatus.expired.value
        await engine.dispose()

    asyncio.run(_test())


def test_deactivate_unknown_id_is_404(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens, _, _ = _app_with_paid_project(tmp_path / "404.db", ["ops@example.com"])
        with TestClient(app) as c:
            r = await _deactivate(c, uuid.uuid4(), tokens["ops@example.com"])
            assert r.status_code == 404, r.text
        await engine.dispose()

    asyncio.run(_test())


def test_second_active_subscription_keeps_project_paid(monkeypatch, tmp_path):
    """Deactivating one of two paid plans must not steal entitlements paid for by the other."""
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens, project_id, sub_ids = _app_with_paid_project(
            tmp_path / "two.db", ["ops@example.com"], extra_active=True
        )
        with TestClient(app) as c:
            r = await _deactivate(c, sub_ids[0], tokens["ops@example.com"])
            assert r.status_code == 200, r.text
            project = await _row(engine, Project, project_id)
            assert project.tier == SubscriptionTier.team.value

            r = await _deactivate(c, sub_ids[1], tokens["ops@example.com"])
            assert r.status_code == 200, r.text
            await _assert_project_free(engine, project_id)
        await engine.dispose()

    asyncio.run(_test())


def test_list_returns_only_admin_visible_rows(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens, _, sub_ids = _app_with_paid_project(
            tmp_path / "list.db", ["ops@example.com", "merchant@example.com"]
        )
        with TestClient(app) as c:
            r = c.get(
                "/api/v1/admin/subscriptions",
                cookies={"ipg_session": tokens["ops@example.com"]},
            )
            assert r.status_code == 200, r.text
            rows = r.json()["subscriptions"]
            assert len(rows) == 1
            assert rows[0]["subscription_id"] == str(sub_ids[0])
            assert rows[0]["project_name"] == "paid workspace"
            assert rows[0]["buyer_email"] == "merchant@example.com"
            assert rows[0]["status"] == SubscriptionStatus.active.value

            # Cancelling removes it from the actionable list.
            await _deactivate(c, sub_ids[0], tokens["ops@example.com"])
            r = c.get(
                "/api/v1/admin/subscriptions",
                cookies={"ipg_session": tokens["ops@example.com"]},
            )
            assert r.json()["subscriptions"] == []
        await engine.dispose()

    asyncio.run(_test())
