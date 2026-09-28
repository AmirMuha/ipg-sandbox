"""Contract tests for Zarinpal emulated surface (T017) — contracts/adapter-surfaces.md §1."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_zarinpal_initiate_success_and_errors(client: TestClient):
    # 1. Success initiation
    resp = client.post(
        "/zarinpal/request/payment",
        json={
            "amount": 250000,
            "currency": "IRR",
            "callback_url": "http://localhost:3000/callback",
            "return_url": "http://localhost:3000/return",
            "description": "Test order #1",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 100
    assert data["message"] == "Operation was successful"
    assert data["authority"].startswith("A")
    assert f"/zarinpal/checkout/{data['authority']}" in data["payment_url"]

    # 2. Invalid merchant credentials (empty string passed explicitly)
    bad_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "",
            "amount": 10000,
        },
    )
    assert bad_resp.status_code == 401
    bad_data = bad_resp.json()
    assert bad_data["code"] == "invalid_credentials"

    # 3. Missing required amount
    missing_resp = client.post(
        "/zarinpal/request/payment",
        json={"description": "No amount"},
    )
    assert missing_resp.status_code == 422
    assert missing_resp.json()["code"] == "validation_error"


def test_zarinpal_checkout_and_callback(client: TestClient):
    # Initiate first
    init_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "amount": 100000,
            "return_url": "http://localhost:3000/return",
        },
    )
    authority = init_resp.json()["authority"]

    # GET checkout page
    checkout_resp = client.get(f"/zarinpal/checkout/{authority}")
    assert checkout_resp.status_code == 200
    assert "text/html" in checkout_resp.headers["content-type"]
    assert 'dir="rtl"' in checkout_resp.text
    assert "100,000" in checkout_resp.text
    assert "<input" not in checkout_resp.text.lower()

    # POST confirm -> 302 redirect with Status=OK
    confirm_resp = client.post(
        f"/zarinpal/checkout/{authority}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302
    location = confirm_resp.headers["location"]
    assert "http://localhost:3000/return" in location
    assert f"Authority={authority}" in location
    assert "Status=OK" in location

    # GET callback redirect
    cb_resp = client.get(
        f"/zarinpal/callback/{authority}?Status=OK",
        follow_redirects=False,
    )
    assert cb_resp.status_code == 302
    assert f"Authority={authority}" in cb_resp.headers["location"]
    assert "Status=OK" in cb_resp.headers["location"]


def test_zarinpal_verification_and_refund(client: TestClient):
    # 1. Initiate with scenario refund
    init_resp = client.post(
        "/zarinpal/request/payment",
        headers={"X-Sandbox-Scenario": "refund"},
        json={
            "amount": 50000,
            "return_url": "http://localhost:3000/return",
        },
    )
    authority = init_resp.json()["authority"]
    client.post(f"/zarinpal/checkout/{authority}", data={"action": "confirm"})

    # 2. Verify moves to approved
    verify_resp = client.post(
        "/zarinpal/payment/verification",
        json={"authority": authority, "amount": 50000},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["code"] == 100
    assert "ref_id" in verify_data
    assert "card_pan" in verify_data

    # 3. Refund approved transaction
    refund_resp = client.post(
        "/zarinpal/payment/refund",
        json={"authority": authority},
    )
    assert refund_resp.status_code == 200
    assert refund_resp.json()["code"] == 100

    # 4. Refund again on already refunded fails
    re_refund = client.post(
        "/zarinpal/payment/refund",
        json={"authority": authority},
    )
    assert re_refund.status_code == 200
    assert re_refund.json()["code"] == -50


def test_zarinpal_decline_scenario(client: TestClient):
    # Force decline via header
    init_resp = client.post(
        "/zarinpal/request/payment",
        headers={"X-Sandbox-Scenario": "decline"},
        json={
            "amount": 75000,
            "return_url": "http://localhost:3000/return",
        },
    )
    authority = init_resp.json()["authority"]

    # Verify fails per decline scenario
    verify_resp = client.post(
        "/zarinpal/payment/verification",
        json={"authority": authority},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["code"] == -51


def test_zarinpal_unsupported_operation_envelope(client: TestClient):
    # Unsupported HTTP method on defined route -> 405 -> unsupported_operation envelope
    resp = client.get("/zarinpal/request/payment")
    assert resp.status_code == 405
    data = resp.json()
    assert data["code"] == "unsupported_operation"
