"""Contract tests for Quota Enforcement (HTTP 429) & Adapter Ceilings (HTTP 403) (004-launch-readiness-flows)."""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.api.app import create_app
from src.models import (
    AdapterConfig,
    Base,
    Project,
    Provider,
    UsageMeter,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def quota_client(tmp_path):
    db_file = tmp_path / "quota_test.db"
    sync_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sync_engine)

    proj_id = uuid.uuid4()
    ad3_id = uuid.uuid4()
    with Session(sync_engine) as session:
        project = Project(
            id=proj_id,
            name="Restricted Project",
            tier="developer",
            daily_requests_cap=3,
            max_active_adapters=2,
            history_cap=1000,
            webhook_retry_max=3,
            pending_settle_delay_s=5,
            timeout_delay_s=30,
        )
        session.add(project)

        # Add 3 adapters (2 enabled, 1 disabled)
        ad1 = AdapterConfig(
            id=uuid.uuid4(),
            project_id=proj_id,
            provider=Provider.zarinpal,
            enabled=True,
            credentials={"merchant_id": "test"},
            endpoint_path_prefix="/zarinpal",
        )
        ad2 = AdapterConfig(
            id=uuid.uuid4(),
            project_id=proj_id,
            provider=Provider.idpay,
            enabled=True,
            credentials={"api_key": "test"},
            endpoint_path_prefix="/idpay",
        )
        ad3 = AdapterConfig(
            id=ad3_id,
            project_id=proj_id,
            provider=Provider.behpardakht,
            enabled=False,
            credentials={"terminal_id": "1"},
            endpoint_path_prefix="/behpardakht",
        )
        session.add_all([ad1, ad2, ad3])
        meter = UsageMeter(project_id=proj_id, requests_total=0, requests_today=0)
        session.add(meter)
        session.commit()
    sync_engine.dispose()

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    app = create_app()
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    with TestClient(app) as client:
        client.project_id = proj_id
        client.ad3_id = ad3_id
        yield client


def test_adapter_ceiling_enforced_with_403(quota_client: TestClient):
    """Enabling a 3rd adapter when max_active_adapters=2 returns HTTP 403 adapter_limit_exceeded."""
    resp = quota_client.patch(
        f"/api/v1/adapters/{quota_client.ad3_id}",
        json={"enabled": True},
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "adapter_limit_exceeded"
    assert "Developer plan is limited to 2 active payment gateways" in body["message"]


def test_daily_request_quota_enforced_with_429(quota_client: TestClient):
    """Transactions past daily_requests_cap return HTTP 429 with rate-limit headers."""
    # 3 allowed requests
    for i in range(3):
        resp = quota_client.post(
            "/api/v1/transactions",
            json={
                "adapter": "zarinpal",
                "amount_rial": 10000 * (i + 1),
                "forced_scenario": "approve",
                "description": f"tx {i}",
            },
        )
        assert resp.status_code == 201

    # 4th request must be blocked with HTTP 429
    blocked = quota_client.post(
        "/api/v1/transactions",
        json={
            "adapter": "zarinpal",
            "amount_rial": 50000,
            "forced_scenario": "approve",
            "description": "blocked tx",
        },
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "daily_quota_exceeded"
    assert "Retry-After" in blocked.headers
    assert blocked.headers["X-RateLimit-Remaining"] == "0"


def test_quota_meters_query(quota_client: TestClient):
    """GET /api/v1/meters?quota=true returns detailed quota metrics."""
    resp = quota_client.get("/api/v1/meters?quota=true")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "developer"
    assert body["daily_requests_cap"] == 3
    assert body["max_active_adapters"] == 2
    assert body["active_adapters_count"] == 2
    assert "window_resets_at" in body
