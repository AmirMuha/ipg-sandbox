"""GET /api/v1/analytics/overview integration tests (T011, US2).

The regression these guard is FR-004: the cards used to sum whichever page of transactions
the list endpoint returned, so a project with 200 rows showed the totals of the newest 50.
"""

import time

from fastapi.testclient import TestClient


def _overview(client: TestClient) -> dict:
    resp = client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _seed(client: TestClient, count: int, **overrides) -> None:
    for _ in range(count):
        resp = client.post(
            "/api/v1/transactions/simulate",
            json={"adapter": "zarinpal", "amount_rial": 1_000_000, **overrides},
        )
        assert resp.status_code == 201, resp.text


def test_empty_project_reports_zeros_not_errors(client: TestClient):
    """An unused sandbox must render, not blow up on a division by zero."""
    data = _overview(client)

    assert data["total_transactions"] == 0
    assert data["total_volume_rial"] == 0
    assert data["success_rate_percent"] == 0.0
    assert data["funnel"] == {"initiated": 0, "hosted": 0, "callback": 0, "settled": 0}


def test_aggregates_span_all_rows_not_just_the_listed_page(client: TestClient):
    """FR-004: 30 rows exist but the list endpoint only ever returns 20 at a time."""
    _seed(client, 30)

    data = _overview(client)
    listed = client.get("/api/v1/transactions", params={"page_size": 20}).json()

    assert len(listed["items"]) == 20
    assert data["total_transactions"] == 30
    assert data["total_volume_rial"] == 30_000_000


def test_volume_sums_actual_amounts(client: TestClient):
    client.post(
        "/api/v1/transactions/simulate", json={"adapter": "zarinpal", "amount_rial": 2_500_000}
    )
    client.post(
        "/api/v1/transactions/simulate", json={"adapter": "zarinpal", "amount_rial": 7_500_000}
    )

    assert _overview(client)["total_volume_rial"] == 10_000_000


def test_status_and_scenario_breakdowns(client: TestClient):
    _seed(client, 2, forced_scenario="approve", auto_complete=True)
    _seed(client, 1, forced_scenario="decline", auto_complete=True)
    _seed(client, 1, forced_scenario="approve")  # left in `initiated`

    data = _overview(client)
    assert data["status_breakdown"]["settled"] == 2
    assert data["status_breakdown"]["declined"] == 1
    assert data["status_breakdown"]["initiated"] == 1
    assert data["scenario_distribution"]["approve"] == 3
    assert data["scenario_distribution"]["decline"] == 1


def test_success_rate_is_settled_over_total(client: TestClient):
    """Contract example: 139 settled of 148 -> 93.9."""
    _seed(client, 3, forced_scenario="approve", auto_complete=True)
    _seed(client, 1, forced_scenario="decline", auto_complete=True)

    assert _overview(client)["success_rate_percent"] == 75.0


def test_funnel_is_monotonic(client: TestClient):
    """Initiated -> Hosted -> Callback -> Settled can only ever lose people, never gain."""
    _seed(client, 2, forced_scenario="approve", auto_complete=True)
    _seed(client, 1, forced_scenario="decline", auto_complete=True)
    _seed(client, 1, forced_scenario="approve")  # still `initiated` — never reached checkout

    funnel = _overview(client)["funnel"]
    assert funnel["initiated"] == 4
    assert funnel["hosted"] == 3
    assert funnel["callback"] == 2
    assert funnel["settled"] == 2
    assert funnel["initiated"] >= funnel["hosted"] >= funnel["callback"] >= funnel["settled"]


def test_gateway_rollup_counts_configured_and_exercised(client: TestClient):
    """`active_total` is gateways actually used, not the number installed."""
    assert _overview(client)["gateways"] == {"configured_total": 3, "active_total": 0}

    _seed(client, 1, adapter="zarinpal", auto_complete=True)
    _seed(client, 1, adapter="idpay", auto_complete=True)

    assert _overview(client)["gateways"] == {"configured_total": 3, "active_total": 2}


def test_webhook_rollup_reflects_delivery_attempts(client: TestClient):
    assert _overview(client)["webhooks"]["total_deliveries"] == 0

    _seed(
        client,
        1,
        forced_scenario="approve",
        auto_complete=True,
        callback_url="http://localhost:9/hook",
    )

    # Delivery is fire-and-forget; poll rather than assert against a race.
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        total = _overview(client)["webhooks"]["total_deliveries"]
        if total:
            break
        time.sleep(0.05)
    assert total >= 1
