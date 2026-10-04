"""Contract tests for Specialized Bank and Institutional PSPs (T019) — US2 (Pardakht Novin, IranKish, Fanava, Sarmayeh)."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_pardakht_novin_lifecycle(client: TestClient):
    # 1. GenerateToken
    resp = client.post(
        "/pardakht_novin/GenerateToken",
        json={
            "WSContext": "test-context",
            "TransType": "EN_GOODS",
            "Amount": 600000,
            "OrderId": "PNA-9001",
            "CallbackUrl": "http://localhost:3000/callback",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["Status"] == "0"
    token = data["Token"]
    assert token

    # 2. Checkout view
    view_resp = client.get(f"/pardakht_novin/checkout/{token}")
    assert view_resp.status_code == 200
    assert "پرداخت نوین" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/pardakht_novin/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="State" value="OK"' in action_resp.text

    # 4. Verify REST
    verify_resp = client.post(
        "/pardakht_novin/Verify",
        json={"WSContext": "test-context", "Token": token, "RefNum": token},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["Result"] == "0"
    assert verify_data["Amount"] == 600000

    # 5. Duplicate verify returns -6
    dup_resp = client.post(
        "/pardakht_novin/Verify",
        json={"WSContext": "test-context", "Token": token, "RefNum": token},
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["Result"] == "-6"


def test_irankish_lifecycle(client: TestClient):
    # 1. Token
    resp = client.post(
        "/irankish/api/v1/token",
        json={
            "terminalId": "sandbox-terminal_id",
            "acceptorId": "sandbox-acceptor_id",
            "amount": 800000,
            "revertURL": "http://localhost:3000/callback",
            "requestUniqueId": "IK-REQ-101",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] is True
    assert data["resultCode"] == "00"
    token = data["token"]
    assert token

    # 2. Checkout view
    view_resp = client.get(f"/irankish/checkout/{token}")
    assert view_resp.status_code == 200
    assert "ایران‌کیش" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/irankish/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="resultCode" value="00"' in action_resp.text

    # 4. Verify
    verify_resp = client.post(
        "/irankish/api/v1/verify",
        json={
            "terminalId": "sandbox-terminal_id",
            "token": token,
            "retrievalReferenceNumber": "123456789012",
        },
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] is True
    assert verify_data["resultCode"] == "00"
    assert verify_data["amount"] == 800000

    # 5. Duplicate verify returns 94
    dup_resp = client.post(
        "/irankish/api/v1/verify",
        json={
            "terminalId": "sandbox-terminal_id",
            "token": token,
            "retrievalReferenceNumber": "123456789012",
        },
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["resultCode"] == "94"


def test_fanava_lifecycle(client: TestClient):
    # 1. Payment initiation
    resp = client.post(
        "/fanava/payment",
        json={
            "Amount": 350000,
            "OrderId": "FAN-2233",
            "ReturnUrl": "http://localhost:3000/callback",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["Status"] == 0
    token = data["Token"]
    assert token

    # 2. Checkout view
    view_resp = client.get(f"/fanava/checkout/{token}")
    assert view_resp.status_code == 200
    assert "فن‌آوا" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/fanava/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="Status" value="0"' in action_resp.text

    # 4. Verify REST
    verify_resp = client.post(
        "/fanava/verify",
        json={"Token": token},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["Status"] == 0
    assert verify_data["Amount"] == 350000

    # 5. Duplicate verify returns -6
    dup_resp = client.post(
        "/fanava/verify",
        json={"Token": token},
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["Status"] == -6


def test_sarmayeh_lifecycle(client: TestClient):
    # 1. Payment initiation
    resp = client.post(
        "/sarmayeh/payment",
        json={
            "Amount": 200000,
            "OrderId": "SAR-8899",
            "ReturnUrl": "http://localhost:3000/callback",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["Status"] == 0
    token = data["Token"]
    assert token

    # 2. Checkout view
    view_resp = client.get(f"/sarmayeh/checkout/{token}")
    assert view_resp.status_code == 200
    assert "سرمایه" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/sarmayeh/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="Status" value="0"' in action_resp.text

    # 4. Verify REST
    verify_resp = client.post(
        "/sarmayeh/verify",
        json={"Token": token},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["Status"] == 0
    assert verify_data["Amount"] == 200000

    # 5. Duplicate verify returns -6
    dup_resp = client.post(
        "/sarmayeh/verify",
        json={"Token": token},
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["Status"] == -6
