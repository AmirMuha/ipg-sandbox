"""T069/T070/T071/T072: demo signup gate, rate limiting, token expiry and visitor isolation.

`tests/integration/test_demo_gate.py` left `test_visitor_isolation` as a bare `pass`, so the
central FR-014 isolation claim was unverified, and its `demo_client` fixture pointed at a real
Postgres host that does not exist in the test process — so it always skipped.

The demo now accepts a SQLite `DATABASE_URL` (see `apps/demo/src/main.py`), which is what lets
these run hermetically. Postgres stays the production path.
"""

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

DEMO_SRC = Path(__file__).parents[4] / "apps" / "demo" / "src"
pytestmark = pytest.mark.skipif(not DEMO_SRC.exists(), reason="apps/demo removed in 0c1672d")

_SCHEMA = """
CREATE TABLE projects (
    id TEXT PRIMARY KEY, name TEXT, kind TEXT, default_scenario TEXT,
    history_cap INTEGER, webhook_retry_max INTEGER, pending_settle_delay_s INTEGER,
    timeout_delay_s INTEGER, created_at TEXT
);
CREATE TABLE adapter_configs (
    id TEXT PRIMARY KEY, project_id TEXT, provider TEXT, endpoint_path_prefix TEXT,
    api_unit TEXT, credentials TEXT
);
CREATE TABLE visitor_sessions (
    id TEXT PRIMARY KEY, project_id TEXT, email TEXT, magic_link_token_hash TEXT,
    expires_at TEXT, verified_at TEXT, created_at TEXT
);
"""


@pytest.fixture
def demo_app(tmp_path, monkeypatch):
    """Import `apps.demo.src.main` against a throwaway SQLite database."""
    db_path = tmp_path / "demo.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MAGIC_LINK_TTL_MINUTES", "30")
    for module in ("main",):
        sys.modules.pop(module, None)
    sys.path.insert(0, str(DEMO_SRC))
    try:
        import main as demo_main

        demo_main.signup_limits.clear()
        yield demo_main
    finally:
        sys.path.remove(str(DEMO_SRC))
        sys.modules.pop("main", None)


def _signup(app, email):
    """POST /demo/signup, returning the response.

    Every test hits the same client IP, which is what makes the per-IP limit observable here.
    """
    from fastapi.testclient import TestClient

    with TestClient(app.app) as client:
        return client.post("/demo/signup", json={"email": email})


# --- T070: rate limiting keyed on the IP, not the submitted email ------------------------


def test_rate_limit_survives_changing_the_email(demo_app):
    """Varying the address must not reset the limit — that was the whole bug.

    The limiter used to be keyed on `req.email`, which is attacker-chosen and unverified, so
    `a1@x.com, a2@x.com, ...` was never throttled and each one minted a fresh project.
    """
    codes = [_signup(demo_app, f"unique{i}@example.com").status_code for i in range(5)]

    assert codes[:3] == [200, 200, 200]
    assert codes[3:] == [429, 429], f"IP limit did not hold across distinct emails: {codes}"


def test_rate_limit_also_applies_per_email(demo_app):
    """One address cannot be sprayed either."""
    codes = [_signup(demo_app, "same@example.com").status_code for _ in range(5)]

    assert codes[:3] == [200, 200, 200]
    assert codes[3:] == [429, 429]


# --- T069: the token is only echoed when there is no SMTP transport ------------------------


def test_signup_returns_a_dev_token_without_smtp(demo_app):
    """Dev transport (no SMTP configured) keeps the token in the response for convenience."""
    body = _signup(demo_app, "dev@example.com").json()

    assert body["status"] == "magic_link_sent"
    assert body.get("dev_token")


def test_signup_never_returns_the_token_when_smtp_is_configured(demo_app, monkeypatch):
    """With a mail transport configured the response must not carry the token.

    Returning it there would let anyone bypass the email gate by reading the response body,
    which is what FR-014's "require free email signup before simulating" rules out.
    """
    sent: list[str] = []

    monkeypatch.setattr(
        demo_app,
        "deliver_magic_link",
        lambda email, token: sent.append(token),
    )
    # SMTP_HOST is read at import time, so patch the module attribute it branches on.
    monkeypatch.setattr(demo_app, "SMTP_HOST", "mail.example.com")

    body = _signup(demo_app, "prod@example.com").json()

    assert sent, "the magic link was never delivered"
    assert "dev_token" not in body, f"token leaked in a configured deployment: {body}"


# --- T071: the magic link expires -----------------------------------------------------------


def _expire_token(app, token: str) -> None:
    """Backdate the row's `expires_at` so the link is in the past."""
    import hashlib

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    # Same shape the demo writes, so this is a like-for-like comparison rather than a
    # string compare of two different timestamp formats.
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    with app.SessionLocal() as db:
        from sqlalchemy import text

        db.execute(
            text("UPDATE visitor_sessions SET expires_at = :p WHERE magic_link_token_hash = :h"),
            {"p": past, "h": token_hash},
        )
        db.commit()


def test_expired_magic_link_is_rejected(demo_app):
    """A token past its TTL must not sign anyone in."""
    from fastapi.testclient import TestClient

    token = _signup(demo_app, "expiry@example.com").json()["dev_token"]
    _expire_token(demo_app, token)

    with TestClient(demo_app.app) as client:
        resp = client.post("/demo/verify", json={"token": token})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "invalid_token"


def test_fresh_magic_link_is_accepted_and_single_use(demo_app):
    """Single-use still holds: the first verify wins, the second is refused."""
    from fastapi.testclient import TestClient

    token = _signup(demo_app, "single-use@example.com").json()["dev_token"]

    with TestClient(demo_app.app) as client:
        first = client.post("/demo/verify", json={"token": token})
        second = client.post("/demo/verify", json={"token": token})

    assert first.status_code == 200
    assert first.json()["status"] == "verified"
    assert second.status_code == 400


# --- T072: visitor isolation -----------------------------------------------------------------


def _verify_and_get_session(app, email):
    """Sign a visitor up, verify them, and return (TestClient, demo_session cookie)."""
    from fastapi.testclient import TestClient

    token = _signup(app, email).json()["dev_token"]
    with TestClient(app.app) as client:
        resp = client.post("/demo/verify", json={"token": token})
        assert resp.status_code == 200, resp.text
        return client.cookies.get("demo_session")


def test_each_visitor_gets_their_own_project(demo_app):
    """FR-014: two signups are two isolated projects, not one shared row."""
    _verify_and_get_session(demo_app, "alice@example.com")
    _verify_and_get_session(demo_app, "bob@example.com")

    from sqlalchemy import text

    with demo_app.SessionLocal() as db:
        projects = db.execute(text("SELECT id, email FROM visitor_sessions")).fetchall()
        names = db.execute(text("SELECT name FROM projects")).fetchall()

    assert len(projects) == 2
    assert {row[1] for row in projects} == {"alice@example.com", "bob@example.com"}
    assert len({row[0] for row in projects}) == 2, "sessions share a project id"
    assert len(names) == 2, "two visitors must not share one project"


def test_each_new_visitor_project_is_seeded_with_adapters(demo_app):
    """A visitor project with no AdapterConfig cannot run a payment at all."""
    _verify_and_get_session(demo_app, "seeded@example.com")

    from sqlalchemy import text

    with demo_app.SessionLocal() as db:
        rows = db.execute(text("SELECT provider FROM adapter_configs ORDER BY provider")).fetchall()

    assert {row[0] for row in rows} == {"zarinpal", "idpay", "behpardakht"}


def test_one_visitor_cannot_read_another_visitors_session(demo_app):
    """The engine resolves the project from the cookie alone, so the ids must not collide."""
    a = _verify_and_get_session(demo_app, "iso-a@example.com")
    b = _verify_and_get_session(demo_app, "iso-b@example.com")

    assert a and b
    assert a != b, "two visitors were handed the same session id"

    from sqlalchemy import text

    with demo_app.SessionLocal() as db:
        rows = db.execute(
            text("SELECT id, project_id FROM visitor_sessions ORDER BY email")
        ).fetchall()

    assert len({row[0] for row in rows}) == 2
    assert len({row[1] for row in rows}) == 2


def test_signup_stores_only_the_token_hash(demo_app):
    """The raw token must never be persisted — only its SHA-256."""
    token = _signup(demo_app, "hashed@example.com").json()["dev_token"]

    import hashlib

    from sqlalchemy import text

    with demo_app.SessionLocal() as db:
        stored = db.execute(
            text("SELECT magic_link_token_hash FROM visitor_sessions WHERE email = :e"),
            {"e": "hashed@example.com"},
        ).scalar_one()

    assert stored == hashlib.sha256(token.encode()).hexdigest()
    assert stored != token
