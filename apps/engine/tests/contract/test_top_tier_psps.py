"""Contract tests for Top-Tier Banking PSPs (T007) — US1 (Saman, Sadad, Parsian, Pasargad, Asan Pardakht)."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_saman_sep_lifecycle(client: TestClient):
    # 1. Initiate payment
    resp = client.post(
        "/saman/onlinepg/onlinepg",
        json={
            "action": "token",
            "TerminalId": "sandbox-terminal_id",
            "Amount": 500000,
            "ResNum": "ORDER-1001",
            "RedirectUrl": "http://localhost:3000/callback",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 1
    assert data["errorCode"] == 0
    token = data["token"]
    assert token

    # 2. Checkout page
    view_resp = client.get(f"/saman/checkout/{token}")
    assert view_resp.status_code == 200
    assert "سامان" in view_resp.text

    # 3. Checkout action -> auto-submitting POST callback form
    action_resp = client.post(
        f"/saman/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert "document.forms[0].submit()" in action_resp.text
    assert 'name="State" value="OK"' in action_resp.text
    assert f'name="RefNum" value="{token}"' in action_resp.text

    # 4. Verify payment via REST
    verify_resp = client.post(
        "/saman/verifyTxn",
        json={"RefNum": token, "TerminalNumber": "sandbox-terminal_id"},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["ResultCode"] == 0
    assert verify_data["Status"] == 0
    assert verify_data["TransactionDetail"]["Amount"] == 500000

    # 5. Duplicate verify returns -6
    dup_resp = client.post(
        "/saman/verifyTxn",
        json={"RefNum": token, "TerminalNumber": "sandbox-terminal_id"},
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["ResultCode"] == -6

    # 6. WSDL introspection
    wsdl_resp = client.get("/saman/verifyTxn?wsdl")
    assert wsdl_resp.status_code == 200
    assert "definitions" in wsdl_resp.text


def test_sadad_melli_lifecycle(client: TestClient):
    # 1. Initiate
    resp = client.post(
        "/sadad/api/v0/Request/PaymentRequest",
        json={
            "TerminalId": "sandbox-terminal_id",
            "MerchantId": "sandbox-merchant_id",
            "Amount": 1000000,
            "OrderId": 554433,
            "ReturnUrl": "http://localhost:3000/callback",
            "LocalDateTime": "2026-10-03T12:00:00",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ResCode"] == 0
    token = data["Token"]
    assert token

    # 2. Checkout view
    view_resp = client.get(f"/sadad/checkout/{token}")
    assert view_resp.status_code == 200
    assert "سداد" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/sadad/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="ResCode" value="0"' in action_resp.text
    assert f'name="Token" value="{token}"' in action_resp.text

    # 4. Verify
    verify_resp = client.post(
        "/sadad/api/v0/Advice/Verify",
        json={"Token": token},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["ResCode"] == 0
    assert verify_data["Amount"] == 1000000
    assert "RetrivalReferenceNumber" in verify_data

    # 5. Duplicate verify returns 102
    dup_resp = client.post(
        "/sadad/api/v0/Advice/Verify",
        json={"Token": token},
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["ResCode"] == 102


def test_parsian_pec_lifecycle(client: TestClient):
    # 1. Initiate via SOAP
    soap_init = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
      <soapenv:Body>
        <SalePaymentRequest>
          <Pin>sandbox-pin</Pin>
          <Amount>750000</Amount>
          <OrderId>987654</OrderId>
          <ReffererAddress>http://localhost:3000/callback</ReffererAddress>
        </SalePaymentRequest>
      </soapenv:Body>
    </soapenv:Envelope>"""

    resp = client.post(
        "/parsian/EShopService.asmx",
        content=soap_init,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    assert resp.status_code == 200
    assert "<Status>0</Status>" in resp.text
    import re
    token_match = re.search(r"<Token>(\d+)</Token>", resp.text)
    assert token_match
    token = token_match.group(1)

    # 2. Checkout view
    view_resp = client.get(f"/parsian/checkout/{token}")
    assert view_resp.status_code == 200
    assert "پارسیان" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/parsian/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="status" value="0"' in action_resp.text
    assert f'name="Token" value="{token}"' in action_resp.text

    # 4. Confirm Payment (SOAP)
    soap_verify = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
      <soapenv:Body>
        <ConfirmPayment>
          <Pin>sandbox-pin</Pin>
          <Token>{token}</Token>
        </ConfirmPayment>
      </soapenv:Body>
    </soapenv:Envelope>"""

    verify_resp = client.post(
        "/parsian/EShopService.asmx",
        content=soap_verify,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    assert verify_resp.status_code == 200
    assert "<Status>0</Status>" in verify_resp.text
    assert "<RRN>" in verify_resp.text

    # 5. Duplicate verify returns -1529
    dup_resp = client.post(
        "/parsian/EShopService.asmx",
        content=soap_verify,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    assert dup_resp.status_code == 200
    assert "<Status>-1529</Status>" in dup_resp.text


def test_pasargad_pep_lifecycle(client: TestClient):
    # 1. Purchase initiation
    resp = client.post(
        "/pasargad/api/payment/purchase",
        json={
            "invoiceNumber": "INV-7788",
            "invoiceDate": "2026-10-03",
            "amount": 300000,
            "terminalCode": "sandbox-terminal_code",
            "merchantCode": "sandbox-merchant_code",
            "redirectAddress": "http://localhost:3000/callback",
            "timestamp": "2026-10-03T10:00:00",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resultCode"] == 0
    token = data["token"]
    assert token

    # 2. Checkout
    view_resp = client.get(f"/pasargad/checkout/{token}")
    assert view_resp.status_code == 200
    assert "پاسارگاد" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/pasargad/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="status" value="0"' in action_resp.text
    assert 'name="invoiceNumber" value="INV-7788"' in action_resp.text

    # 4. Verify
    verify_resp = client.post(
        "/pasargad/api/payment/verify",
        json={
            "invoiceNumber": "INV-7788",
            "invoiceDate": "2026-10-03",
            "amount": 300000,
            "terminalCode": "sandbox-terminal_code",
            "merchantCode": "sandbox-merchant_code",
            "timeStamp": "2026-10-03T10:05:00",
        },
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["resultCode"] == 0
    assert verify_data["amount"] == 300000

    # 5. Duplicate verify returns -100
    dup_resp = client.post(
        "/pasargad/api/payment/verify",
        json={
            "invoiceNumber": "INV-7788",
            "invoiceDate": "2026-10-03",
            "amount": 300000,
            "terminalCode": "sandbox-terminal_code",
            "merchantCode": "sandbox-merchant_code",
            "timeStamp": "2026-10-03T10:05:00",
        },
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["resultCode"] == -100


def test_asan_pardakht_lifecycle(client: TestClient):
    # 1. Token initiation
    resp = client.post(
        "/asan_pardakht/Token",
        json={
            "merchantConfigurationId": "sandbox-merchant_id",
            "serviceTypeId": 1,
            "localDate": "20261003",
            "localTime": "120000",
            "additionalData": "AP-ORDER-44",
            "callBackUrl": "http://localhost:3000/callback",
            "amountInRials": 450000,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Success"
    token = data["token"]
    assert token

    # 2. Checkout view
    view_resp = client.get(f"/asan_pardakht/checkout/{token}")
    assert view_resp.status_code == 200
    assert "آسان پرداخت" in view_resp.text

    # 3. Checkout action
    action_resp = client.post(
        f"/asan_pardakht/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert action_resp.status_code == 200
    assert 'name="PayResult" value="0"' in action_resp.text
    assert 'name="InvoiceNumber" value="AP-ORDER-44"' in action_resp.text

    # 4. Verify REST
    verify_resp = client.post(
        "/asan_pardakht/Verify",
        json={"token": token, "merchantConfigurationId": "sandbox-merchant_id"},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] == "Success"
    assert verify_data["amount"] == 450000

    # 5. Duplicate verify
    dup_resp = client.post(
        "/asan_pardakht/Verify",
        json={"token": token, "merchantConfigurationId": "sandbox-merchant_id"},
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["PayResult"] == -6
