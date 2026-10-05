"""`require_admin` authorisation (T008).

The security property this whole feature rests on: only an allowlisted account may change which
gateways are offered. Three outcomes are distinct on purpose — 401 (not signed in), 403 (signed in,
not an admin), 200 (admin) — because a merchant hitting a 401 would be bounced to a login page
that will not help them.
"""

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.adapters.registry import seed_configs
from src.api.app import create_app
from src.models import AdapterConfig, Base, Project, Provider, User, UserSession, utcnow
from src.services.auth import generate_session_token, hash_session_token


def _app_with_users(db_file, emails):
    """App plus one signed-in-able user per email, each with a session token."""
    sync_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sync_engine)
    tokens = {}
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
        for email in emails:
            user = User(id=uuid.uuid4(), email=email, password_hash="x")
            s.add(user)
            s.flush()
            token = generate_session_token()
            s.add(
                UserSession(
                    user_id=user.id,
                    token_hash=hash_session_token(token),
                    expires_at=utcnow() + __import__("datetime").timedelta(days=1),
                )
            )
            tokens[email] = token
        s.commit()
    sync_engine.dispose()

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    app = create_app()
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return app, engine, tokens


def _patch(client, provider, enabled, token=None):
    headers = {"Content-Type": "application/json"}
    cookies = {"ipg_session": token} if token else None
    return client.patch(
        f"/api/v1/admin/providers/{provider}",
        json={"enabled": enabled},
        headers=headers,
        cookies=cookies,
    )


def test_allowlisted_admin_may_change_state(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens = _app_with_users(
            tmp_path / "ok.db", ["ops@example.com", "merchant@example.com"]
        )
        with TestClient(app) as c:
            r = _patch(c, "idpay", True, tokens["ops@example.com"])
            assert r.status_code == 200, r.text
        await engine.dispose()

    asyncio.run(_test())


def test_signed_in_non_admin_is_forbidden_and_state_unchanged(monkeypatch, tmp_path):
    """FR-002: refused *and* nothing altered — a 403 that still wrote would be worse than none."""
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, tokens = _app_with_users(
            tmp_path / "no.db", ["ops@example.com", "merchant@example.com"]
        )
        with TestClient(app) as c:
            before = c.get("/api/v1/providers").json()
            r = _patch(c, "idpay", True, tokens["merchant@example.com"])
            assert r.status_code == 403, r.text
            assert r.json()["code"] == "forbidden"
            assert c.get("/api/v1/providers").json() == before
        await engine.dispose()

    asyncio.run(_test())


def test_anonymous_is_unauthorized(monkeypatch, tmp_path):
    """FR-003."""
    monkeypatch.setenv("ADMIN_EMAILS", "ops@example.com")

    async def _test():
        app, engine, _ = _app_with_users(tmp_path / "anon.db", ["ops@example.com"])
        with TestClient(app) as c:
            r = _patch(c, "idpay", True, None)
            assert r.status_code == 401, r.text
            assert r.json()["code"] == "session_required"
        await engine.dispose()

    asyncio.run(_test())


def test_empty_allowlist_denies_everyone(monkeypatch, tmp_path):
    """Fail closed: unset ADMIN_EMAILS means no admin, never open access."""
    monkeypatch.setenv("ADMIN_EMAILS", "")

    async def _test():
        app, engine, tokens = _app_with_users(tmp_path / "empty.db", ["anyone@example.com"])
        with TestClient(app) as c:
            r = _patch(c, "idpay", True, tokens["anyone@example.com"])
            assert r.status_code == 403, r.text
        await engine.dispose()

    asyncio.run(_test())


def test_allowlist_matching_is_case_insensitive(monkeypatch, tmp_path):
    """FR-014: a differing capitalisation must not deny access."""
    monkeypatch.setenv("ADMIN_EMAILS", "Ops@Example.COM")

    async def _test():
        app, engine, tokens = _app_with_users(tmp_path / "case.db", ["ops@example.com"])
        with TestClient(app) as c:
            r = _patch(c, "idpay", True, tokens["ops@example.com"])
            assert r.status_code == 200, r.text
        await engine.dispose()

    asyncio.run(_test())
