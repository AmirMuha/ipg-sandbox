"""Contract tests for Payment Facilitators (T029) — US3 (SizPay, ZarinPal, IDPay)."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_sizpay_lifecycle(client: TestClient):
    # 1. Initiate
    resp = client.post(
        "/sizpay/api/Payment/Token",
        json={
            "MerchantID": "sandbox-merchant_id",
            "TerminalID": "sandbox-terminal_id",
            "UserName": "sandbox-username",
            "Password": "sandbox-password",
            "Amount": 250000,
            "InvoiceNo": "SIZ-101",
            "ReturnURL": "http://localhost:3000/callback",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ResCode"] == 0
    token = data["Token"]
    assert token

    # 2. Checkout view
    view_resp = client.get(f"/sizpay/checkout/{token}")
    assert view_resp.status_code == 200
    assert "سیزپی" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/sizpay/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="ResCode" value="0"' in action_resp.text
    assert f'name="Token" value="{token}"' in action_resp.text

    # 4. Confirm / Verify
    confirm_resp = client.post(
        "/sizpay/api/Payment/Confirm",
        json={
            "MerchantID": "sandbox-merchant_id",
            "TerminalID": "sandbox-terminal_id",
            "Token": token,
        },
    )
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["ResCode"] == 0
    assert confirm_data["Amount"] == 250000

    # 5. Duplicate confirm returns -6
    dup_resp = client.post(
        "/sizpay/api/Payment/Confirm",
        json={
            "MerchantID": "sandbox-merchant_id",
            "TerminalID": "sandbox-terminal_id",
            "Token": token,
        },
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["ResCode"] == -6


def test_zarinpal_and_idpay_multi_status(client: TestClient):
    # ZarinPal multi-status
    resp_zp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "test-merchant",
            "amount": 100000,
            "callback_url": "http://localhost:3000/callback",
        },
    )
    assert resp_zp.status_code == 200
    auth_zp = resp_zp.json()["authority"]

    client.post(
        f"/zarinpal/checkout/{auth_zp}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # First verify -> 100
    v1_zp = client.post(
        "/zarinpal/payment/verification",
        json={"merchant_id": "test-merchant", "authority": auth_zp, "amount": 100000},
    )
    assert v1_zp.status_code == 200
    assert v1_zp.json()["code"] == 100

    # Second verify -> 101 (already verified)
    v2_zp = client.post(
        "/zarinpal/payment/verification",
        json={"merchant_id": "test-merchant", "authority": auth_zp, "amount": 100000},
    )
    assert v2_zp.status_code == 200
    assert v2_zp.json()["code"] == 101

    # IDPay multi-status
    resp_id = client.post(
        "/idpay/payment",
        headers={"X-API-KEY": "test-idpay-key"},
        json={
            "order_id": "ID-ORDER-1",
            "amount": 10000,
            "callback": "http://localhost:3000/callback",
        },
    )
    assert resp_id.status_code == 200
    id_id = resp_id.json()["id"]

    client.post(
        f"/idpay/payment/start/{id_id}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # First verify -> 100
    v1_id = client.post(
        "/idpay/payment/verify",
        headers={"X-API-KEY": "test-idpay-key"},
        json={"id": id_id, "order_id": "ID-ORDER-1"},
    )
    assert v1_id.status_code == 200
    assert v1_id.json()["status"] == 100

    # Second verify -> 101
    v2_id = client.post(
        "/idpay/payment/verify",
        headers={"X-API-KEY": "test-idpay-key"},
        json={"id": id_id, "order_id": "ID-ORDER-1"},
    )
    assert v2_id.status_code == 200
    assert v2_id.json()["status"] == 101
