"""Contract tests for official gateway documentation wire endpoints compatibility."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_behpardakht_real_soap_operations(client: TestClient):
    # bpPayRequest
    soap_init = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
      <soapenv:Body>
        <bpPayRequest xmlns="http://interfaces.core.sw.bps.com/">
          <terminalId>123456</terminalId>
          <userName>sandbox</userName>
          <userPassword>sandbox</userPassword>
          <orderId>7001</orderId>
          <amount>500000</amount>
          <localDate>20261004</localDate>
          <localTime>100000</localTime>
          <additionalData>test</additionalData>
          <callBackUrl>http://localhost:3000/callback</callBackUrl>
          <payerId>0</payerId>
        </bpPayRequest>
      </soapenv:Body>
    </soapenv:Envelope>"""
    resp = client.post(
        "/behpardakht/MellatPaymentGateway",
        content=soap_init,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    assert resp.status_code == 200
    assert "<bpPayRequestResponse" in resp.text
    import re
    match = re.search(r"<return>0,(\d+)</return>", resp.text)
    assert match
    ref_id = match.group(1)

    # checkout
    client.post(
        f"/behpardakht/checkout/{ref_id}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # bpVerifyRequest
    soap_verify = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
      <soapenv:Body>
        <bpVerifyRequest xmlns="http://interfaces.core.sw.bps.com/">
          <terminalId>123456</terminalId>
          <userName>sandbox</userName>
          <userPassword>sandbox</userPassword>
          <orderId>7001</orderId>
          <saleOrderId>7001</saleOrderId>
          <saleReferenceId>{ref_id}</saleReferenceId>
        </bpVerifyRequest>
      </soapenv:Body>
    </soapenv:Envelope>"""
    verify_resp = client.post(
        "/behpardakht/MellatPaymentGateway",
        content=soap_verify,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    assert verify_resp.status_code == 200
    assert "<return>0</return>" in verify_resp.text

    # duplicate verify returns 43
    dup_resp = client.post(
        "/behpardakht/MellatPaymentGateway",
        content=soap_verify,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    assert dup_resp.status_code == 200
    assert "<return>43</return>" in dup_resp.text

    # bpSettleRequest
    soap_settle = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
      <soapenv:Body>
        <bpSettleRequest xmlns="http://interfaces.core.sw.bps.com/">
          <terminalId>123456</terminalId>
          <userName>sandbox</userName>
          <userPassword>sandbox</userPassword>
          <orderId>7001</orderId>
          <saleOrderId>7001</saleOrderId>
          <saleReferenceId>{ref_id}</saleReferenceId>
        </bpSettleRequest>
      </soapenv:Body>
    </soapenv:Envelope>"""
    settle_resp = client.post(
        "/behpardakht/MellatPaymentGateway",
        content=soap_settle,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    assert settle_resp.status_code == 200
    assert "<return>0</return>" in settle_resp.text


def test_zarinpal_v4_compatibility(client: TestClient):
    resp = client.post(
        "/zarinpal/pg/v4/payment/request.json",
        json={
            "merchant_id": "test-merchant",
            "amount": 100000,
            "currency": "IRR",
            "callback_url": "http://localhost:3000/callback",
            "description": "ZarinPal v4 order",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["code"] == 100
    auth = data["data"]["authority"]
    assert auth

    start_resp = client.get(f"/zarinpal/pg/StartPay/{auth}")
    assert start_resp.status_code == 200
    assert "زرین‌پال" in start_resp.text

    client.post(
        f"/zarinpal/checkout/{auth}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    verify_resp = client.post(
        "/zarinpal/pg/v4/payment/verify.json",
        json={"merchant_id": "test-merchant", "authority": auth, "amount": 100000},
    )
    assert verify_resp.status_code == 200
    vdata = verify_resp.json()
    assert vdata["data"]["code"] == 100
    assert vdata["data"]["card_pan"]


def test_idpay_v1_1_compatibility(client: TestClient):
    resp = client.post(
        "/idpay/v1.1/payment",
        json={
            "order_id": "IDP-7788",
            "amount": 20000,
            "callback": "http://localhost:3000/callback",
        },
        headers={"X-API-KEY": "test-idpay-key"},
    )
    assert resp.status_code == 200
    data = resp.json()
    pid = data["id"]
    assert pid

    start_resp = client.get(f"/idpay/v1.1/payment/start/{pid}")
    assert start_resp.status_code == 200
    assert "آیدی پی" in start_resp.text

    client.post(
        f"/idpay/v1.1/payment/start/{pid}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    verify_resp = client.post(
        "/idpay/v1.1/payment/verify",
        json={"id": pid, "order_id": "IDP-7788"},
        headers={"X-API-KEY": "test-idpay-key"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == 100


def test_sadad_get_purchase_redirect(client: TestClient):
    resp = client.post(
        "/sadad/api/v0/Request/PaymentRequest",
        json={
            "TerminalId": "sandbox-terminal_id",
            "MerchantId": "sandbox-merchant_id",
            "Amount": 200000,
            "OrderId": 12345,
            "ReturnUrl": "http://localhost:3000/callback",
            "LocalDateTime": "2026-10-04T10:00:00",
        },
    )
    assert resp.status_code == 200
    token = resp.json()["Token"]

    # Browser GET redirect
    get_resp = client.get(f"/sadad/Purchase?token={token}")
    assert get_resp.status_code == 200
    assert "سداد" in get_resp.text


def test_saman_rest_verify_route(client: TestClient):
    resp = client.post(
        "/saman/onlinepg/onlinepg",
        json={
            "action": "token",
            "TerminalId": "sandbox-terminal_id",
            "Amount": 300000,
            "ResNum": "ORD-555",
            "RedirectUrl": "http://localhost:3000/callback",
        },
    )
    token = resp.json()["token"]
    client.post(
        f"/saman/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    verify_resp = client.post(
        "/saman/verifyTxnRandomSessionkey/ipg/VerifyTransaction",
        json={"RefNum": token, "TerminalNumber": "sandbox-terminal_id"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["ResultCode"] == 0


def test_sizpay_get_token_and_start_get(client: TestClient):
    resp = client.post(
        "/sizpay/api/Payment/GetToken",
        json={
            "MerchantID": "sandbox-merchant_id",
            "TerminalID": "sandbox-terminal_id",
            "Amount": 150000,
            "InvoiceNo": "SIZ-99",
            "ReturnURL": "http://localhost:3000/callback",
        },
    )
    assert resp.status_code == 200
    token = resp.json()["Token"]
    get_resp = client.get(f"/sizpay/api/Payment/Start?Token={token}")
    assert get_resp.status_code == 200
    assert "سیزپی" in get_resp.text


def test_asan_pardakht_v1_routes(client: TestClient):
    resp = client.post(
        "/asan_pardakht/v1/Token",
        json={
            "merchantConfigurationId": "sandbox-merchant_id",
            "serviceTypeId": 1,
            "localDate": "20261004",
            "localTime": "120000",
            "additionalData": "AP-V1-1",
            "callBackUrl": "http://localhost:3000/callback",
            "amountInRials": 350000,
        },
    )
    assert resp.status_code == 200
    token = resp.json()["token"]

    client.post(
        f"/asan_pardakht/checkout/{token}",
        data={"action": "confirm"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    verify_resp = client.post(
        "/asan_pardakht/v1/Verify",
        json={"token": token, "merchantConfigurationId": "sandbox-merchant_id"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "Success"


def test_parsian_get_payment_redirects(client: TestClient):
    soap_init = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
      <soapenv:Body>
        <SalePaymentRequest>
          <Pin>sandbox-pin</Pin>
          <Amount>400000</Amount>
          <OrderId>776655</OrderId>
          <ReffererAddress>http://localhost:3000/callback</ReffererAddress>
        </SalePaymentRequest>
      </soapenv:Body>
    </soapenv:Envelope>"""
    resp = client.post(
        "/parsian/EShopService.asmx",
        content=soap_init,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    import re
    match = re.search(r"<Token>(\d+)</Token>", resp.text)
    assert match
    token = match.group(1)

    get1 = client.get(f"/parsian/payment?Token={token}")
    assert get1.status_code == 200
    assert "پارسیان" in get1.text

    get2 = client.get(f"/parsian/default.aspx?au={token}")
    assert get2.status_code == 200
    assert "پارسیان" in get2.text
