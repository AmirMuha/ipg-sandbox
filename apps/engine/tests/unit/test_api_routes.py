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
from src.models import (
    AdapterConfig,
    Base,
    Project,
    ProjectKind,
    Provider,
    Transaction,
    UsageMeter,
)

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
    # Local self-host: the operator typed these test values in, so reading them back is how the
    # stack gets configured and debugged (FR-014 only restricts the visitor-scoped demo path).
    assert body[0]["credentials"] == {"merchant_id": "test-merchant"}


def test_get_adapters_omits_credentials_for_a_demo_project(tmp_path):
    """FR-014: a visitor-scoped project must not read its adapter credentials back.

    The route is reachable by that visitor, so echoing them turns the endpoint into a
    credential-display surface.
    """
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    with Session(sync_engine) as session:
        project = Project(id=uuid.uuid4(), name="visitor", kind=ProjectKind.demo)
        session.add(project)
        session.add(
            AdapterConfig(
                id=uuid.uuid4(),
                project_id=project.id,
                provider=Provider.zarinpal,
                credentials={"merchant_id": "SECRET-MERCHANT"},
                endpoint_path_prefix="/zarinpal",
            )
        )
        session.commit()
    sync_engine.dispose()

    app = create_app()
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'demo.db'}")
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/adapters")

    asyncio.run(async_engine.dispose())

    body = response.json()
    assert len(body) == 1
    assert "credentials" not in body[0], "demo project leaked adapter credentials"
    assert "SECRET-MERCHANT" not in response.text
    # The non-secret fields still describe the adapter, so config views keep working.
    assert body[0]["provider"] == "zarinpal"
    assert body[0]["endpoint_path_prefix"] == "/zarinpal"


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


# --- unhandled errors still emit the envelope --------------------------------


def test_unhandled_exception_returns_the_envelope_not_plain_text(tmp_path):
    """A server bug must still be machine-readable (FR-010).

    Regression: without an `Exception` handler this returned FastAPI's default
    `Internal Server Error` as text/plain, which no CI client can parse.

    Builds its own client so the throwing route is registered on the very app under test.
    """
    url = f"sqlite:///{tmp_path / 'boom.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    app = create_app()

    @app.get("/_boom_for_test")
    async def _boom():  # pragma: no cover - raised, never returned
        raise RuntimeError("simulated internal failure")

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'boom.db'}")
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/_boom_for_test")

    asyncio.run(async_engine.dispose())

    assert response.status_code == 500
    body = response.json()  # raises if the body is not JSON
    assert body["code"] == "internal_error"
    assert "message" in body
    assert "RuntimeError" not in response.text, "traceback leaked to the client"


def test_documented_error_codes_are_unchanged():
    """The seven contract codes must stay exactly as contracts/control-api.md lists them."""
    from src.api import errors

    assert {
        errors.VALIDATION_ERROR,
        errors.UNSUPPORTED_OPERATION,
        errors.INVALID_CREDENTIALS,
        errors.NOT_FOUND,
        errors.RATE_LIMITED,
        errors.SCENARIO_INVALID,
        errors.SESSION_REQUIRED,
    } == {
        "validation_error",
        "unsupported_operation",
        "invalid_credentials",
        "not_found",
        "rate_limited",
        "scenario_invalid",
        "session_required",
    }
    # The 500 code is deliberately outside that set; it is not a caller-error code.
    assert errors.INTERNAL_ERROR not in {m.value for m in errors.ErrorCode}


# --- POST & DELETE /api/v1/transactions ---------------------------------------


def test_pre_seed_transaction_success_and_delete(client):
    """T026: pre-seed transaction with forced_scenario, then delete it."""
    # 1. Pre-seed
    resp = client.post(
        "/api/v1/transactions",
        json={
            "adapter": "zarinpal",
            "amount_rial": 350000,
            "forced_scenario": "decline",
            "app_reference": "order-pre-1",
            "description": "Pre-seeded test tx",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount_rial"] == 350000
    assert body["forced_scenario"] == "decline"
    assert body["effective_scenario"] == "decline"
    assert body["status"] == "initiated"
    assert body["authority"] is not None
    assert body["raw_request"] is not None
    tx_id = body["id"]

    # 2. Appears in GET /transactions
    list_body = client.get("/api/v1/transactions").json()
    assert any(item["id"] == tx_id for item in list_body["items"])

    # 3. DELETE /transactions/{id}
    del_resp = client.delete(f"/api/v1/transactions/{tx_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["id"] == tx_id

    # 4. Subsequent GET returns 404
    get_resp = client.get(f"/api/v1/transactions/{tx_id}")
    assert get_resp.status_code == 404
    assert get_resp.json()["code"] == "not_found"


def test_pre_seed_transaction_validation_errors(client):
    """T026: validation errors on pre-seed endpoint."""
    # Missing adapter -> 422
    r1 = client.post("/api/v1/transactions", json={"amount_rial": 1000})
    assert r1.status_code == 422
    assert r1.json()["code"] == "validation_error"

    # Unknown adapter -> 404
    r2 = client.post("/api/v1/transactions", json={"adapter": "unknown_gw", "amount_rial": 1000})
    assert r2.status_code == 404
    assert r2.json()["code"] == "not_found"

    # Negative amount -> 422
    r3 = client.post("/api/v1/transactions", json={"adapter": "zarinpal", "amount_rial": -50})
    assert r3.status_code == 422
    assert r3.json()["code"] == "validation_error"

    # Invalid scenario -> 422
    r4 = client.post(
        "/api/v1/transactions",
        json={"adapter": "zarinpal", "amount_rial": 1000, "forced_scenario": "non_existent"},
    )
    assert r4.status_code == 422
    assert r4.json()["code"] == "scenario_invalid"


# --- PATCH /api/v1/transactions/{id} & PATCH /api/v1/project ------------------


def test_patch_transaction_forced_scenario(client):
    """T032: PATCH /api/v1/transactions/{id} updates forced_scenario and re-resolves."""
    resp = client.post(
        "/api/v1/transactions",
        json={"adapter": "zarinpal", "amount_rial": 10000},
    )
    assert resp.status_code == 201
    tx_id = resp.json()["id"]

    # 1. Force decline
    patch_resp = client.patch(
        f"/api/v1/transactions/{tx_id}",
        json={"forced_scenario": "decline"},
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["forced_scenario"] == "decline"
    assert body["effective_scenario"] == "decline"

    # 2. Clear force with null
    clear_resp = client.patch(
        f"/api/v1/transactions/{tx_id}",
        json={"forced_scenario": None},
    )
    assert clear_resp.status_code == 200
    assert clear_resp.json()["forced_scenario"] is None
    assert clear_resp.json()["effective_scenario"] == "approve"

    # 3. Invalid scenario -> 422
    inv_resp = client.patch(
        f"/api/v1/transactions/{tx_id}",
        json={"forced_scenario": "bogus"},
    )
    assert inv_resp.status_code == 422
    assert inv_resp.json()["code"] == "scenario_invalid"

    # 4. Missing key -> 422
    miss_resp = client.patch(
        f"/api/v1/transactions/{tx_id}",
        json={},
    )
    assert miss_resp.status_code == 422
    assert miss_resp.json()["code"] == "validation_error"

    # 5. Non-existent id -> 404
    missing_id = "00000000-0000-0000-0000-000000000000"
    notfound_resp = client.patch(
        f"/api/v1/transactions/{missing_id}",
        json={"forced_scenario": "decline"},
    )
    assert notfound_resp.status_code == 404
    assert notfound_resp.json()["code"] == "not_found"


def test_patch_project_settings(client):
    """T032: PATCH /api/v1/project updates project defaults and bounds."""
    # 1. Update valid fields
    patch_resp = client.patch(
        "/api/v1/project",
        json={
            "default_scenario": "decline",
            "pending_settle_delay_s": 3,
            "timeout_delay_s": 15,
            "history_cap": 500,
            "webhook_retry_max": 5,
        },
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["default_scenario"] == "decline"
    assert body["pending_settle_delay_s"] == 3
    assert body["timeout_delay_s"] == 15
    assert body["history_cap"] == 500
    assert body["webhook_retry_max"] == 5

    # Verify GET reflects changes
    get_body = client.get("/api/v1/project").json()
    assert get_body["default_scenario"] == "decline"
    assert get_body["pending_settle_delay_s"] == 3

    # Reset default_scenario to approve
    client.patch(
        "/api/v1/project",
        json={"default_scenario": "approve", "pending_settle_delay_s": 5},
    )

    # 2. Out of range delays -> 422
    for bad_delay in (-1, 300, 1000):
        r = client.patch("/api/v1/project", json={"pending_settle_delay_s": bad_delay})
        assert r.status_code == 422
        assert r.json()["code"] == "validation_error"

    # 3. History cap < 1 -> 422
    r_cap = client.patch("/api/v1/project", json={"history_cap": 0})
    assert r_cap.status_code == 422
    assert r_cap.json()["code"] == "validation_error"

    # 4. Unknown field -> 422
    r_unk = client.patch("/api/v1/project", json={"not_a_real_field": 123})
    assert r_unk.status_code == 422
    assert r_unk.json()["code"] == "validation_error"

    # 5. Invalid default scenario -> 422
    r_scen = client.patch("/api/v1/project", json={"default_scenario": "bogus_scenario"})
    assert r_scen.status_code == 422
    assert r_scen.json()["code"] == "scenario_invalid"


def test_patch_and_test_adapter(client):
    """T048: PATCH /api/v1/adapters/{id} and POST /api/v1/adapters/{id}/test."""
    adapter_id = client.seeded["adapter_id"]

    # 1. Test credentials with seeded valid credentials
    t_resp = client.post(f"/api/v1/adapters/{adapter_id}/test")
    assert t_resp.status_code == 200
    assert t_resp.json()["ok"] is True

    # 2. Patch credentials to empty -> test fails
    p_resp = client.patch(
        f"/api/v1/adapters/{adapter_id}",
        json={"credentials": {"merchant_id": ""}},
    )
    assert p_resp.status_code == 200
    assert p_resp.json()["credentials"]["merchant_id"] == ""

    # Test now fails with 401 invalid_credentials
    t_bad = client.post(f"/api/v1/adapters/{adapter_id}/test")
    assert t_bad.status_code == 401
    assert t_bad.json()["code"] == "invalid_credentials"

    # 3. Patch back to valid credentials
    p_resp2 = client.patch(
        f"/api/v1/adapters/{adapter_id}",
        json={"credentials": {"merchant_id": "test-merchant"}},
    )
    assert p_resp2.status_code == 200
    assert p_resp2.json()["credentials"]["merchant_id"] == "test-merchant"

    # 3b. `enabled` is no longer merchant-writable (006-admin-ipg-visibility, FR-017):
    # availability is administrators' alone, via /api/v1/admin/providers/{provider}.
    p_enabled = client.patch(
        f"/api/v1/adapters/{adapter_id}", json={"enabled": False}
    )
    assert p_enabled.status_code == 422
    assert p_enabled.json()["code"] == "validation_error"
    assert p_enabled.json()["details"]["allowed"] == ["credentials"]

    # 4. Unknown fields -> 422
    p_unk = client.patch(f"/api/v1/adapters/{adapter_id}", json={"bogus": 123})
    assert p_unk.status_code == 422
    assert p_unk.json()["code"] == "validation_error"


# --- T075: per-adapter status (FR-008 "configuration and status") ---------------------------


def test_adapters_carry_a_status_object(client):
    """Every adapter answers with a status block; FR-008 asks for status, not just config."""
    adapters = client.get("/api/v1/adapters").json()

    assert adapters, "expected the seeded adapters"
    for adapter in adapters:
        status = adapter["status"]
        assert set(status) == {
            "state",
            "transactions_total",
            "transactions_settled",
            "failed_deliveries",
            "last_activity_at",
        }
        assert status["state"] in {"healthy", "degraded", "idle", "disabled"}


def test_unused_adapter_reports_idle_not_broken(client):
    """Never exercised is `idle`, not `degraded` — no activity is not a failure.

    Asserted over every adapter rather than a named one, because this file's fixture seeds a
    different set than the root conftest does.
    """
    adapters = client.get("/api/v1/adapters").json()

    assert adapters
    for adapter in adapters:
        if adapter["status"]["transactions_total"] == 0:
            assert adapter["status"]["state"] == "idle", adapter
            assert adapter["status"]["last_activity_at"] is None, adapter


def test_adapter_status_counts_settled_transactions(client):
    """Status is derived from real rows, so an approved payment moves the counters."""
    before = {
        a["provider"]: a["status"]["transactions_total"]
        for a in client.get("/api/v1/adapters").json()
    }

    init = client.post(
        "/zarinpal/request/payment",
        json={"merchant_id": "test-merchant", "amount": 5000, "currency": "IRR"},
    )
    authority = init.json()["authority"]
    client.post(f"/zarinpal/checkout/{authority}", data={"action": "confirm"})
    client.post("/zarinpal/payment/verification", json={"authority": authority})

    after = {a["provider"]: a["status"] for a in client.get("/api/v1/adapters").json()}

    assert after["zarinpal"]["transactions_total"] == before["zarinpal"] + 1
    assert after["zarinpal"]["transactions_settled"] >= 1
    assert after["zarinpal"]["last_activity_at"] is not None


def test_disabled_adapter_reports_disabled(client):
    """A gateway withdrawn by an operator reads as disabled, not just unchecked in the UI.

    006-admin-ipg-visibility removed the merchant toggle, so this now drives the row through the
    admin path (or the seeded default) rather than PATCHing `enabled` as a merchant.
    """
    adapters = client.get("/api/v1/adapters").json()
    target = adapters[0]

    # The platform project's own row is what `enabled` reflects for a bare local stack.
    assert target["provider"] == "zarinpal"
    withdrawn = client.get("/api/v1/providers").json()
    assert withdrawn["providers"] == ["zarinpal"]

    # This fixture has no session at all, so the anonymous guard fires first (401). The 403
    # "signed in but not an admin" path is covered in tests/unit/test_admin_guard.py.
    resp = client.patch(
        f"/api/v1/admin/providers/{target['provider']}",
        json={"enabled": False},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "session_required"
    assert client.get("/api/v1/providers").json()["providers"] == ["zarinpal"]
