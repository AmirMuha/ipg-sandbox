"""A payment link must open in a browser that carries no session cookie and no API key.

Regression: `{authority}` was resolved inside the request's project, and an unauthenticated
browser falls back to the seeded "default" project — so a link created by any workspace answered
{"code":"not_found","message":"transaction not found"} on the live stack.
"""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.adapters.registry import seed_configs
from src.config import public_base_url
from src.models import AdapterConfig, Project, Provider, Transaction


def _seed_other_project(client: TestClient) -> str:
    """A second project holding an initiated Zarinpal payment; returns its authority."""
    authority = uuid.uuid4().hex
    async_url = str(client.app.state.session_factory.kw["bind"].url)
    engine = create_engine(async_url.replace("sqlite+aiosqlite:///", "sqlite:///"))

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


def test_checkout_link_opens_without_a_session(client: TestClient):
    authority = _seed_other_project(client)

    resp = client.get(f"/zarinpal/checkout/{authority}")

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
