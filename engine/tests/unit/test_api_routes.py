"""T011/T015 guards: the read-only control API and the machine-readable error envelope.

Runs the real FastAPI app over `TestClient` against a real SQLite database. The Postgres-only
column types are compiled down by the shims in `conftest.py` (auto-loaded for this directory),
which is what lets `Base.metadata.create_all` run here at all.

A file-backed SQLite DB is used rather than `:memory:` because the schema is built on a sync
engine while the app talks to it through asyncpg-style async SQLAlchemy — two engines cannot
share an in-memory database.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

import src.api.routes as routes_module
from src.api.app import create_app
from src.models import AdapterConfig, Base, Project, Provider, Transaction, UsageMeter

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

_BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _seed(session: Session) -> dict:
    """One local project, one zarinpal adapter, three transactions oldest -> newest.

    Returns plain ids, not ORM instances: the seeding session closes before the requests run, and
    a detached instance raises on attribute access.
    """
    project = Project(
        id=uuid.uuid4(),
        name="default",
        history_cap=1000,
        webhook_retry_max=3,
        webhook_retry_backoff_s=[1, 2, 4],
    )
    session.add(project)
    adapter = AdapterConfig(
        id=uuid.uuid4(),
        project_id=project.id,
        provider=Provider.zarinpal,
        credentials={"merchant_id": "test-merchant"},
        endpoint_path_prefix="/zarinpal",
    )
    session.add(adapter)
    session.flush()

    txs = [
        Transaction(
            id=uuid.uuid4(),
            project_id=project.id,
            adapter_id=adapter.id,
            amount_rial=1_000 * (i + 1),
            authority=f"A-{i}",
            created_at=_BASE_TIME + timedelta(minutes=i),
            raw_request={"stage": "initiate", "seq": i},
            raw_response={"code": 100, "seq": i},
        )
        for i in range(3)
    ]
    session.add_all(txs)
    session.add(
        UsageMeter(
            project_id=project.id, requests_total=7, transactions_total=3, history_retained=3
        )
    )
    session.commit()
    return {"project_id": project.id, "adapter_id": adapter.id, "tx_ids": [tx.id for tx in txs]}


@pytest.fixture
def client(tmp_path):
    """Real app + real schema + real HTTP, one throwaway database per test."""
    url = f"sqlite:///{tmp_path / 'test.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    with Session(sync_engine) as session:
        seeded = _seed(session)
    sync_engine.dispose()

    app = create_app()
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    with TestClient(app) as test_client:
        test_client.seeded = seeded
        yield test_client

    asyncio.run(async_engine.dispose())


# --- GET /api/v1/project ------------------------------------------------------


def test_get_project_returns_the_seeded_default(client):
    body = client.get("/api/v1/project").json()

    assert body["name"] == "default"
    assert body["kind"] == "local"
    assert body["default_scenario"] == "approve"
    assert body["pending_settle_delay_s"] == 5
    assert body["webhook_retry_backoff_s"] == [1, 2, 4]
    assert uuid.UUID(body["id"]) == client.seeded["project_id"]


# --- GET /api/v1/adapters -----------------------------------------------------


def test_get_adapters_lists_configured_adapters(client):
    body = client.get("/api/v1/adapters").json()

    assert len(body) == 1
    assert body[0]["provider"] == "zarinpal"
    assert body[0]["api_unit"] == "rial"
    assert body[0]["endpoint_path_prefix"] == "/zarinpal"
    assert body[0]["credentials"] == {"merchant_id": "test-merchant"}


# --- GET /api/v1/transactions -------------------------------------------------


def test_transactions_are_newest_first(client):
    body = client.get("/api/v1/transactions").json()

    amounts = [item["amount_rial"] for item in body["items"]]
    assert amounts == [3_000, 2_000, 1_000]
    assert body["total"] == 3


def test_transactions_pagination_is_safe(client):
    first = client.get("/api/v1/transactions", params={"page": 1, "page_size": 2}).json()
    second = client.get("/api/v1/transactions", params={"page": 2, "page_size": 2}).json()

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    ids = [item["id"] for item in first["items"]] + [item["id"] for item in second["items"]]
    assert len(set(ids)) == 3, "a page boundary repeated or skipped a row"


def test_transactions_list_omits_raw_payloads(client):
    """US4.4 detail: raw_request/raw_response belong to the detail view, not the list."""
    item = client.get("/api/v1/transactions").json()["items"][0]

    assert "raw_request" not in item
    assert "raw_response" not in item


def test_transaction_detail_includes_raw_payloads(client):
    tx_id = client.seeded["tx_ids"][1]
    body = client.get(f"/api/v1/transactions/{tx_id}").json()

    assert body["id"] == str(tx_id)
    assert body["raw_request"] == {"stage": "initiate", "seq": 1}
    assert body["raw_response"] == {"code": 100, "seq": 1}
    assert body["authority"] == "A-1"
    assert body["effective_scenario"] == "approve"


def test_transaction_filter_by_status(client):
    body = client.get("/api/v1/transactions", params={"status": "settled"}).json()

    assert body["items"] == []
    assert body["total"] == 0


def test_unknown_transaction_id_is_not_found_envelope(client):
    response = client.get(f"/api/v1/transactions/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert "detail" not in response.json(), "FastAPI's default shape leaked"


def test_unknown_route_uses_the_envelope_not_fastapi_default(client):
    response = client.get("/api/v1/nope")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_bad_query_param_is_validation_error_envelope(client):
    response = client.get("/api/v1/transactions", params={"page": 0})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert "details" in response.json()


# --- GET /api/v1/meters -------------------------------------------------------


def test_meters_returns_exactly_the_counter_fields(client):
    """FR-011: counters only. The key set is the contract — assert it exactly, both ways."""
    body = client.get("/api/v1/meters").json()

    assert set(body) == set(routes_module.METER_FIELDS)
    assert body == {
        "requests_total": 7,
        "transactions_total": 3,
        "history_retained": 3,
        "webhook_attempts": 0,
    }


def test_meters_has_no_billing_fields(client):
    """Guards against a future `add billing column` leaking through the endpoint."""
    keys = set(client.get("/api/v1/meters").json())

    forbidden = {
        "amount",
        "amount_rial",
        "balance",
        "billing",
        "cost",
        "credits",
        "currency",
        "invoice",
        "invoices",
        "paid",
        "plan",
        "price",
        "revenue",
        "spend",
        "total_amount",
        "tier",
    }
    assert keys & forbidden == set()


def test_meters_reports_zeros_for_a_fresh_project(tmp_path):
    """No UsageMeter row yet must read as zeros, not 404 or null."""
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    with Session(sync_engine) as session:
        session.add(Project(id=uuid.uuid4(), name="default"))
        session.commit()
    sync_engine.dispose()

    app = create_app()
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'fresh.db'}")
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    with TestClient(app) as fresh:
        assert fresh.get("/api/v1/meters").json() == dict.fromkeys(routes_module.METER_FIELDS, 0)

    asyncio.run(async_engine.dispose())
