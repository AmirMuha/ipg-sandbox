"""Contract tests for Admin Provider Availability & Visibility (006-admin-ipg-visibility).

Tests:
- T009: Admin write path (200 / 404 / 422 / 403 / 401)
- T010: Last-gateway guard (422 when attempting to disable the only active gateway)
- T011: Public read (GET /api/v1/providers unauthenticated, uncached)
- T028: GET /api/v1/adapters reports derived `withdrawn_by_operator` boolean
- T035: Concurrent admin writes (last write wins)
"""

import asyncio
import uuid
from datetime import timedelta

import pytest
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
    User,
    UserSession,
    utcnow,
)
from src.services.auth import generate_session_token, hash_session_token

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _setup_test_env(db_file, admin_emails=("admin@example.com",)):
    sync_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sync_engine)

    tokens = {}
    with Session(sync_engine) as session:
        # 1. Platform project (user_id IS NULL) with only zarinpal enabled by default
        platform = Project(id=uuid.uuid4(), name="default")
        session.add(platform)
        session.flush()
        session.add_all(
            [
                AdapterConfig(
                    id=uuid.uuid4(),
                    **{**kw, "enabled": kw["provider"] is Provider.zarinpal},
                )
                for kw in seed_configs(platform.id)
            ]
        )

        # 2. Admin user
        for email in admin_emails:
            admin_user = User(id=uuid.uuid4(), email=email, password_hash="hash")
            session.add(admin_user)
            session.flush()
            t = generate_session_token()
            session.add(
                UserSession(
                    user_id=admin_user.id,
                    token_hash=hash_session_token(t),
                    expires_at=utcnow() + timedelta(days=7),
                )
            )
            tokens[email] = t

        # 3. Regular merchant user with their own project
        merchant = User(id=uuid.uuid4(), email="merchant@example.com", password_hash="hash")
        session.add(merchant)
        session.flush()
        m_proj = Project(id=uuid.uuid4(), name="merchant_proj", user_id=merchant.id)
        session.add(m_proj)
        session.flush()
        session.add_all(
            [
                AdapterConfig(id=uuid.uuid4(), **{**kw, "enabled": True})
                for kw in seed_configs(m_proj.id)
            ]
        )
        m_token = generate_session_token()
        session.add(
            UserSession(
                user_id=merchant.id,
                token_hash=hash_session_token(m_token),
                expires_at=utcnow() + timedelta(days=7),
            )
        )
        tokens["merchant@example.com"] = m_token

        session.commit()
    sync_engine.dispose()

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    app = create_app()
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return app, engine, tokens


def test_public_read_unauthenticated(monkeypatch, tmp_path):
    """T011: GET /api/v1/providers returns offered providers without authentication."""
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    app, engine, _ = _setup_test_env(tmp_path / "public.db")

    with TestClient(app) as client:
        res = client.get("/api/v1/providers")
        assert res.status_code == 200
        data = res.json()
        assert "providers" in data
        assert data["providers"] == ["zarinpal"]
        assert data["count"] == 1

    asyncio.run(engine.dispose())


def test_admin_write_path_and_authorizations(monkeypatch, tmp_path):
    """T009: Admin can toggle, non-admin gets 403, anonymous gets 401."""
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    app, engine, tokens = _setup_test_env(tmp_path / "admin_write.db")

    with TestClient(app) as client:
        # Anonymous -> 401
        res = client.patch("/api/v1/admin/providers/idpay", json={"enabled": True})
        assert res.status_code == 401

        # Non-admin merchant -> 403
        client.cookies.set("ipg_session", tokens["merchant@example.com"])
        res = client.patch("/api/v1/admin/providers/idpay", json={"enabled": True})
        assert res.status_code == 403
        assert res.json()["code"] == "forbidden"

        # Allowlisted Admin -> 200 (enable idpay)
        client.cookies.set("ipg_session", tokens["admin@example.com"])
        res = client.patch("/api/v1/admin/providers/idpay", json={"enabled": True})
        assert res.status_code == 200
        data = res.json()
        assert "idpay" in data["providers"]
        assert "zarinpal" in data["providers"]
        assert data["count"] == 2

        # Public read immediately reflects update
        pub = client.get("/api/v1/providers")
        assert "idpay" in pub.json()["providers"]

        # Unknown provider -> 404
        bad_prov = client.patch("/api/v1/admin/providers/nonexistent", json={"enabled": True})
        assert bad_prov.status_code == 404

        # Non-boolean enabled -> 422
        bad_val = client.patch("/api/v1/admin/providers/idpay", json={"enabled": "yes"})
        assert bad_val.status_code == 422

    asyncio.run(engine.dispose())


def test_last_gateway_guard(monkeypatch, tmp_path):
    """T010: With only one gateway offered, disabling it is refused with 422."""
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    app, engine, tokens = _setup_test_env(tmp_path / "guard.db")

    with TestClient(app) as client:
        client.cookies.set("ipg_session", tokens["admin@example.com"])

        # Initially only zarinpal is enabled
        res = client.patch("/api/v1/admin/providers/zarinpal", json={"enabled": False})
        assert res.status_code == 422
        assert "At least one payment gateway must remain available" in res.json()["message"]

        # zarinpal still remains enabled
        pub = client.get("/api/v1/providers").json()
        assert pub["providers"] == ["zarinpal"]

    asyncio.run(engine.dispose())


def test_adapters_list_reports_withdrawn_by_operator(monkeypatch, tmp_path):
    """T028: GET /api/v1/adapters reports derived `withdrawn_by_operator` boolean."""
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    app, engine, tokens = _setup_test_env(tmp_path / "derived.db")

    with TestClient(app) as client:
        client.cookies.set("ipg_session", tokens["merchant@example.com"])
        res = client.get("/api/v1/adapters")
        assert res.status_code == 200
        adapters = {a["provider"]: a for a in res.json()}

        # zarinpal is offered on platform -> withdrawn_by_operator == False
        assert adapters["zarinpal"]["withdrawn_by_operator"] is False

        # idpay is disabled on platform -> withdrawn_by_operator == True
        assert adapters["idpay"]["withdrawn_by_operator"] is True

        # Now admin enables idpay
        client.cookies.set("ipg_session", tokens["admin@example.com"])
        client.patch("/api/v1/admin/providers/idpay", json={"enabled": True})

        # Merchant refreshes adapters list -> idpay is no longer withdrawn_by_operator
        client.cookies.set("ipg_session", tokens["merchant@example.com"])
        refreshed = {a["provider"]: a for a in client.get("/api/v1/adapters").json()}
        assert refreshed["idpay"]["withdrawn_by_operator"] is False

    asyncio.run(engine.dispose())


def test_concurrent_admin_writes_last_write_wins(monkeypatch, tmp_path):
    """T035: Two admins writing the same gateway: last write wins."""
    monkeypatch.setenv("ADMIN_EMAILS", "admin1@example.com,admin2@example.com")
    app, engine, tokens = _setup_test_env(
        tmp_path / "concurrent.db", admin_emails=("admin1@example.com", "admin2@example.com")
    )

    with TestClient(app) as client:
        # Admin 1 enables idpay
        client.cookies.set("ipg_session", tokens["admin1@example.com"])
        r1 = client.patch("/api/v1/admin/providers/idpay", json={"enabled": True})
        assert r1.status_code == 200
        assert "idpay" in r1.json()["providers"]

        # Admin 2 disables idpay
        client.cookies.set("ipg_session", tokens["admin2@example.com"])
        r2 = client.patch("/api/v1/admin/providers/idpay", json={"enabled": False})
        assert r2.status_code == 200
        assert "idpay" not in r2.json()["providers"]

        # Admin 1 checks state again -> sees idpay is withdrawn
        client.cookies.set("ipg_session", tokens["admin1@example.com"])
        r3 = client.get("/api/v1/providers")
        assert "idpay" not in r3.json()["providers"]

    asyncio.run(engine.dispose())
