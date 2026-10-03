"""POST /api/v1/transactions/simulate integration tests (T006, US1).

The dashboard's primary action. Two modes share one endpoint: `interactive` returns a
hosted checkout URL, `auto_complete` runs the same confirm + verify edges a browser would
take so a webhook can be checked without one.
"""

import pytest
from fastapi.testclient import TestClient


def _simulate(client: TestClient, **overrides) -> dict:
    body = {"adapter": "zarinpal", "amount_rial": 2_500_000, **overrides}
    resp = client.post("/api/v1/transactions/simulate", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_interactive_returns_hosted_checkout_url(client: TestClient):
    """US1.2: an initiated simulation carries an accessible hosted checkout URL."""
    data = _simulate(client, description="Order #9401", app_reference="ORD-9401")

    tx = data["transaction"]
    assert tx["status"] == "initiated"
    assert tx["description"] == "Order #9401"
    assert tx["app_reference"] == "ORD-9401"
    assert data["execution_mode"] == "interactive"
    assert data["callback_dispatched"] is False

    # The authority is the last path segment, so the link is actually openable.
    assert data["checkout_url"] == f"http://localhost:8080/zarinpal/checkout/{tx['authority']}"
    assert tx["checkout_url"] == data["checkout_url"]

    page = client.get(data["checkout_url"].replace("localhost:8080", ""))
    assert page.status_code == 200


@pytest.mark.parametrize(
    ("provider", "expected_path"),
    [
        ("zarinpal", "/zarinpal/checkout/"),
        ("idpay", "/idpay/payment/start/"),
        ("behpardakht", "/behpardakht/checkout/"),
    ],
)
def test_checkout_url_uses_each_gateways_real_mount_path(
    client: TestClient, provider: str, expected_path: str
):
    """Each gateway hosts its page at a different suffix; guessing `/checkout/` 404s on IDPay."""
    data = _simulate(client, adapter=provider)
    assert expected_path in data["checkout_url"]


def test_auto_complete_settles_and_reports_mode(client: TestClient):
    """US1.3 + FR-011: one click walks initiate -> checkout -> verify."""
    data = _simulate(client, forced_scenario="approve", auto_complete=True)

    assert data["execution_mode"] == "auto_completed"
    assert data["transaction"]["status"] == "settled"
    # Settling is a verify-stage event; a settle callback is dispatched when one is configured.
    assert data["callback_dispatched"] is False


def test_auto_complete_honours_forced_decline(client: TestClient):
    data = _simulate(client, forced_scenario="decline", auto_complete=True)

    assert data["transaction"]["status"] == "declined"
    assert data["transaction"]["effective_scenario"] == "decline"


def test_callback_dispatched_when_callback_url_set(client: TestClient):
    data = _simulate(
        client,
        forced_scenario="approve",
        auto_complete=True,
        callback_url="http://localhost:9/hook",
    )
    assert data["callback_dispatched"] is True


def test_simulation_appears_in_the_transaction_list(client: TestClient):
    """US1 independent test: created, listed, and linked to its checkout page."""
    data = _simulate(client, app_reference="ORD-SMOKE")
    listed = client.get("/api/v1/transactions", params={"q": "ORD-SMOKE"}).json()

    assert listed["total"] == 1
    row = listed["items"][0]
    assert row["id"] == data["transaction"]["id"]
    assert row["checkout_url"] == data["checkout_url"]


@pytest.mark.parametrize(
    "body",
    [
        {"amount_rial": 1000},  # adapter missing
        {"adapter": "zarinpal"},  # amount missing
        {"adapter": "zarinpal", "amount_rial": "not-a-number"},
        {"adapter": "no-such-gateway", "amount_rial": 1000},
    ],
)
def test_invalid_input_is_rejected(client: TestClient, body: dict):
    resp = client.post("/api/v1/transactions/simulate", json=body)
    assert resp.status_code in (404, 422), resp.text


def test_invalid_forced_scenario_is_rejected(client: TestClient):
    resp = client.post(
        "/api/v1/transactions/simulate",
        json={"adapter": "zarinpal", "amount_rial": 1000, "forced_scenario": "explode"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "scenario_invalid"
