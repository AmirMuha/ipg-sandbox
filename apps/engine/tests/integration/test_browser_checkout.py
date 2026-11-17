"""A payment link must open in any browser, with or without a dashboard session.

Regression: `{authority}` was resolved inside the request's project. An unauthenticated browser
fell back to the seeded "default" project, and a signed-in browser used the session user's
project — so a link created by any other workspace answered
{"code":"not_found","message":"transaction not found"} on the live stack.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.adapters.registry import seed_configs
from src.config import public_base_url
from src.models import AdapterConfig, Project, Provider, Transaction, User, UserSession
from src.services.auth import hash_session_token

SESSION_TOKEN = "test-browser-session-token"


def _sync_engine(client: TestClient):
    async_url = str(client.app.state.session_factory.kw["bind"].url)
    return create_engine(async_url.replace("sqlite+aiosqlite:///", "sqlite:///"))


def _seed_other_project(client: TestClient) -> str:
    """A second project holding an initiated Zarinpal payment; returns its authority."""
    authority = uuid.uuid4().hex
    engine = _sync_engine(client)

    with Session(engine) as session:
        project = Project(name="workspace")
        session.add(project)
        session.flush()
        session.add_all(
            [AdapterConfig(id=uuid.uuid4(), **kw) for kw in seed_configs(project.id)]
        )
        session.flush()
        adapter = session.query(AdapterConfig).filter_by(
            project_id=project.id, provider=Provider.zarinpal
        ).one()
        session.add(
            Transaction(
                project_id=project.id,
                adapter_id=adapter.id,
                amount_rial=10_000,
                authority=authority,
            )
        )
        session.commit()

    engine.dispose()
    return authority


def _sign_in_with_own_project(client: TestClient) -> None:
    """A dashboard user whose session resolves to a different project than the payment's."""
    engine = _sync_engine(client)

    with Session(engine) as session:
        user = User(email="merchant@example.com")
        session.add(user)
        session.flush()
        project = Project(name="merchant-workspace", user_id=user.id)
        session.add(project)
        session.flush()
        session.add_all(
            [
                AdapterConfig(id=uuid.uuid4(), **{**kw, "enabled": True})
                for kw in seed_configs(project.id)
            ]
        )
        session.add(
            UserSession(
                user_id=user.id,
                token_hash=hash_session_token(SESSION_TOKEN),
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
        )
        session.commit()

    engine.dispose()


def test_checkout_link_opens_without_a_session(client: TestClient):
    authority = _seed_other_project(client)

    resp = client.get(f"/zarinpal/checkout/{authority}")

    assert resp.status_code == 200, resp.text
    assert "not_found" not in resp.text
    # A browser must never reuse an earlier 404 (or a stale page) for a live payment link.
    assert resp.headers["cache-control"] == "no-store"


def test_checkout_link_opens_when_signed_in(client: TestClient):
    """A dashboard session for another project must not hide the payment it is paying."""
    _sign_in_with_own_project(client)
    authority = _seed_other_project(client)

    resp = client.get(
        f"/zarinpal/pg/StartPay/{authority}",
        cookies={"ipg_session": SESSION_TOKEN},
    )

    assert resp.status_code == 200, resp.text
    assert "not_found" not in resp.text


def test_unknown_authority_still_404s(client: TestClient):
    resp = client.get(f"/zarinpal/checkout/{uuid.uuid4().hex}")

    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


def test_checkout_url_uses_the_public_origin(monkeypatch):
    monkeypatch.setenv("WEB_URL", "https://ipg.sandboxed.ir/")

    assert public_base_url() == "https://ipg.sandboxed.ir"

    monkeypatch.delenv("WEB_URL")
    monkeypatch.setenv("ENGINE_PORT", "8080")

    assert public_base_url() == "http://localhost:8080"
