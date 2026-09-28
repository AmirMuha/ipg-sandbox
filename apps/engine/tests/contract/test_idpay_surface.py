"""Contract tests for IDPay emulated surface (T018) — contracts/adapter-surfaces.md §2."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_idpay_initiate_success_and_errors(client: TestClient):
    # 1. Success initiation
    resp = client.post(
        "/idpay/payment",
        headers={"X-API-KEY": "test-key"},
        json={
            "order_id": "order-101",
            "amount": 25000,  # 25,000 Toman -> 250,000 Rial
            "callback": "http://localhost:3000/callback",
            "desc": "IDPay test payment",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert f"/idpay/payment/start/{data['id']}" in data["link"]

    # Check transaction in control API: amount is canonical Rial (250,000)
    tx_resp = client.get("/api/v1/transactions")
    assert tx_resp.status_code == 200
    txs = tx_resp.json()["items"]
    assert any(t["authority"] == data["id"] and t["amount_rial"] == 250000 for t in txs)

    # 2. Empty api-key -> 401
    bad_resp = client.post(
        "/idpay/payment",
        headers={"X-API-KEY": ""},
        json={"amount": 1000},
    )
    assert bad_resp.status_code == 401
    assert bad_resp.json()["code"] == "invalid_credentials"

    # 3. Missing amount -> 422
    missing_resp = client.post(
        "/idpay/payment",
        headers={"X-API-KEY": "test-key"},
        json={"order_id": "bad"},
    )
    assert missing_resp.status_code == 422
    assert missing_resp.json()["code"] == "validation_error"


def test_idpay_checkout_and_verify(client: TestClient):
    # 1. Initiate
    init_resp = client.post(
        "/idpay/payment",
        headers={"X-API-KEY": "test-key"},
        json={
            "order_id": "order-102",
            "amount": 50000,  # Toman
            "callback": "http://localhost:3000/callback",
        },
    )
    pay_id = init_resp.json()["id"]

    # 2. Checkout view
    checkout_resp = client.get(f"/idpay/payment/start/{pay_id}")
    assert checkout_resp.status_code == 200
    assert "500,000" in checkout_resp.text  # displayed in Rial
    assert "<input" not in checkout_resp.text.lower()

    # 3. Checkout confirm -> 302 redirect to callback
    confirm_resp = client.post(
        f"/idpay/payment/start/{pay_id}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302
    location = confirm_resp.headers["location"]
    assert "status=10" in location
    assert f"id={pay_id}" in location
    assert "order_id=order-102" in location

    # 4. Verify payment
    verify_resp = client.post(
        "/idpay/payment/verify",
        json={"id": pay_id, "order_id": "order-102"},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] == 100
    assert verify_data["amount"] == 50000  # returned in Toman!
    assert "track_id" in verify_data
    assert "card_no" in verify_data

    # 5. Re-verify -> status 101
    reverify_resp = client.post(
        "/idpay/payment/verify",
        json={"id": pay_id, "order_id": "order-102"},
    )
    assert reverify_resp.status_code == 200
    assert reverify_resp.json()["status"] == 101


def test_idpay_decline_and_refund(client: TestClient):
    # 1. Decline scenario
    init_resp = client.post(
        "/idpay/payment",
        headers={"X-Sandbox-Scenario": "decline", "X-API-KEY": "test-key"},
        json={"amount": 10000},
    )
    pay_id = init_resp.json()["id"]

    verify_resp = client.post(
        "/idpay/payment/verify",
        json={"id": pay_id},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == 50

    # 2. Refund scenario
    refund_init = client.post(
        "/idpay/payment",
        headers={"X-Sandbox-Scenario": "refund", "X-API-KEY": "test-key"},
        json={"amount": 20000},
    )
    refund_id = refund_init.json()["id"]

    # Checkout confirm advances initiated -> pending
    client.post(
        f"/idpay/payment/start/{refund_id}",
        data={"action": "confirm"},
        follow_redirects=False,
    )

    # Verify moves pending -> approved
    client.post("/idpay/payment/verify", json={"id": refund_id})

    # Refund
    refund_resp = client.post(
        "/idpay/payment/refund",
        json={"id": refund_id},
    )
    assert refund_resp.status_code == 200
    assert refund_resp.json()["status"] == 200


def test_idpay_unsupported_operation_envelope(client: TestClient):
    resp = client.get("/idpay/payment")
    assert resp.status_code == 405
    assert resp.json()["code"] == "unsupported_operation"
