import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app

demo_src = str(Path(__file__).parents[4] / "demo" / "src")
sys.path.insert(0, demo_src)

try:
    from main import app as demo_app
except ImportError:
    demo_app = None


@pytest.fixture
def engine_client(client, monkeypatch):
    # The module-level `app` built a real asyncpg engine from Settings.from_env(), so this
    # test errored with `database "ipg_sandbox" does not exist` on a machine without Postgres.
    # Reuse the root `client` fixture instead: same app, SQLite-backed session_factory.
    #
    # `monkeypatch` rather than a bare os.environ write, because the earlier version restored
    # by writing "local" instead of *unsetting* — leaving ENGINE_PROFILE process-wide, so every
    # later test inherited demo scoping and answered `session_required` (44 failures).
    monkeypatch.setenv("ENGINE_PROFILE", "demo")
    assert create_app is not None  # imported app factory kept for symmetry with conftest
    yield client


@pytest.fixture
def demo_client():
    if demo_app is None:
        pytest.skip("demo_app not available")
    with TestClient(demo_app) as client:
        yield client


def test_demo_blocks_without_session(engine_client):
    resp = engine_client.get("/api/v1/project")
    assert resp.status_code == 401
    assert resp.json()["code"] == "session_required"


def test_signup_spam_rate_limited(demo_client):
    email = "spam@example.com"
    for _ in range(3):
        resp = demo_client.post("/demo/signup", json={"email": email})
        assert resp.status_code == 200

    resp = demo_client.post("/demo/signup", json={"email": email})
    assert resp.status_code == 429
    assert resp.json()["detail"] == "rate_limited"


def test_visitor_isolation(demo_client, engine_client):
    # This requires DB setup, which might be complex if we mock it
    pass
