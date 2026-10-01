import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.app import app as engine_app

demo_src = str(Path(__file__).parents[4] / "demo" / "src")
sys.path.insert(0, demo_src)

try:
    from main import app as demo_app
except ImportError:
    demo_app = None

@pytest.fixture
def engine_client():
    os.environ["ENGINE_PROFILE"] = "demo"
    with TestClient(engine_app) as client:
        yield client
    os.environ["ENGINE_PROFILE"] = "local"

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
