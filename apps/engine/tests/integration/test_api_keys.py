"""API key lifecycle + authentication (007-api-key-auth).

Runs on the root `client` fixture's SQLite database, where `Base.metadata.create_all`
builds `api_keys` from the model — so these tests cover the route logic, not the
Alembic migration (that is applied against Postgres in the deploy path).
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("client")


def _register(client: TestClient, email: str) -> str:
    """Register a fresh user and return the session token."""
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "password_confirmation": "Password123!",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["token"]


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_register(client, 'api-keys@example.com')}"}


def test_create_api_key(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.post("/api/v1/auth/api-keys", json={"name": "My Prod Key"}, headers=auth_headers)
    assert resp.status_code == 201, resp.text

    data = resp.json()["data"]
    assert data["token"].startswith("ipg_key_")
    assert data["token"][-4:] == data["last_four"]
    assert data["name"] == "My Prod Key"


def test_create_rejects_blank_name(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.post("/api/v1/auth/api-keys", json={"name": "   "}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_enforces_ten_key_limit(client: TestClient, auth_headers: dict[str, str]) -> None:
    for i in range(10):
        resp = client.post(
            "/api/v1/auth/api-keys", json={"name": f"Key {i}"}, headers=auth_headers
        )
        assert resp.status_code == 201, resp.text

    resp = client.post("/api/v1/auth/api-keys", json={"name": "Key 11"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "limit" in resp.text.lower()


def test_list_never_leaks_the_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post("/api/v1/auth/api-keys", json={"name": "Key 1"}, headers=auth_headers)
    client.post("/api/v1/auth/api-keys", json={"name": "Key 2"}, headers=auth_headers)

    resp = client.get("/api/v1/auth/api-keys", headers=auth_headers)
    assert resp.status_code == 200

    rows = resp.json()["data"]
    assert len(rows) == 2
    for row in rows:
        assert "token" not in row
        assert row["last_four"]


def test_api_key_authenticates(client: TestClient, auth_headers: dict[str, str]) -> None:
    token = client.post(
        "/api/v1/auth/api-keys", json={"name": "Auth Key"}, headers=auth_headers
    ).json()["data"]["token"]

    client.cookies.clear()  # force the header path instead of the session cookie

    ok = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200


def test_invalid_api_key_is_rejected(client: TestClient) -> None:
    client.cookies.clear()

    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer ipg_key_not_a_real_key"}
    )
    assert resp.status_code == 401


def test_revoked_key_stops_working(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/api/v1/auth/api-keys", json={"name": "To Revoke"}, headers=auth_headers
    ).json()["data"]

    resp = client.delete(f"/api/v1/auth/api-keys/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    client.cookies.clear()
    after = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {created['token']}"})
    assert after.status_code == 401

    remaining = client.get("/api/v1/auth/api-keys", headers=auth_headers).json()["data"]
    assert all(row["id"] != created["id"] for row in remaining)
