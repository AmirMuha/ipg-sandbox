"""Contract tests for Authentication API (004-launch-readiness-flows)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.app import create_app
from src.models import Base

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def auth_client(tmp_path):
    url = f"sqlite:///{tmp_path / 'auth_test.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    async_url = f"sqlite+aiosqlite:///{tmp_path / 'auth_test.db'}"
    async_engine = create_async_engine(async_url)
    app = create_app()
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    with TestClient(app) as test_client:
        yield test_client


def test_register_and_login_flow(auth_client: TestClient):
    # 1. Validation errors
    bad_email = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "invalid-email", "password": "Password123!"},
    )
    assert bad_email.status_code == 422

    short_pw = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "password": "short"},
    )
    assert short_pw.status_code == 422

    # 2. Successful registration
    reg_resp = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "Password123!",
            "full_name": "Test User",
        },
    )
    assert reg_resp.status_code == 201
    body = reg_resp.json()
    assert body["user"]["email"] == "user@example.com"
    assert body["project"]["tier"] == "developer"
    assert body["project"]["daily_requests_cap"] == 100
    assert "token" in body
    assert "ipg_session" in reg_resp.cookies

    # 3. Duplicate registration rejected
    dup_resp = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    assert dup_resp.status_code == 400

    # 4. Login with bad password
    bad_login = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 5. Successful login
    login_resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()

    # 6. GET /api/v1/auth/me
    me_resp = auth_client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["email"] == "user@example.com"

    # 7. Logout
    logout_resp = auth_client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200
