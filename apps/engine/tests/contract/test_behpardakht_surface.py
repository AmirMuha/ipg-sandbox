"""Contract tests for Behpardakht SOAP emulated surface (T019).

contracts/adapter-surfaces.md §3.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from requests import Response
from zeep import Client

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
WSDL_PATH = Path(__file__).parents[2] / "src" / "adapters" / "behpardakht" / "behpardakht.wsdl"


class ClientTransport:
    """Zeep transport delegating requests to FastAPI TestClient without socket I/O."""

    def __init__(self, client: TestClient, extra_headers: dict[str, str] | None = None):
        self.client = client
        self.extra_headers = extra_headers or {}

    def load(self, url: str) -> bytes:
        if "wsdl" in url.lower():
            # Load via TestClient to verify WSDL endpoint
            resp = self.client.get("/behpardakht/MellatPaymentGateway?wsdl")
            return resp.content
        return WSDL_PATH.read_bytes()

    def post_xml(self, address: str, envelope, headers: dict) -> Response:
        from zeep.wsdl.utils import etree_to_string

        body = etree_to_string(envelope)
        req_headers = dict(headers or {})
        req_headers.update(self.extra_headers)
        r = self.client.post("/behpardakht/MellatPaymentGateway", content=body, headers=req_headers)
        response = Response()
        response.status_code = r.status_code
        response._content = r.content
        for k, v in r.headers.items():
            response.headers[k] = v
        return response


def _get_zeep_client(client: TestClient, extra_headers: dict[str, str] | None = None) -> Client:
    transport = ClientTransport(client, extra_headers=extra_headers)
    c = Client(str(WSDL_PATH), transport=transport)
    c.settings.raw_response = False
    return c


def test_behpardakht_wsdl_endpoint(client: TestClient):
    resp = client.get("/behpardakht/MellatPaymentGateway?wsdl")
    assert resp.status_code == 200
    assert "text/xml" in resp.headers["content-type"]
    assert "PaymentGatewayImplService" in resp.text


def test_behpardakht_initiate_and_checkout(client: TestClient):
    zeep_client = _get_zeep_client(client)

    # 1. bpPaymentRequest
    req_data = {
        "terminalId": 123456,
        "userName": "sandbox",
        "userPassword": "sandbox",
        "orderId": 2001,
        "amount": 750000,  # 750,000 Rial canonical
        "localDate": "20260928",
        "localTime": "120000",
        "additionalData": "order-2001",
        "callBackUrl": "http://localhost:3000/callback",
        "payerId": 0,
    }
    result = zeep_client.service.bpPaymentRequest(**req_data)
    assert result.ResCode == 0
    ref_id = result.RefId
    assert ref_id
    assert f"/behpardakht/checkout/{ref_id}" in result.RedirectUrl

    # Check transaction in control API
    tx_resp = client.get("/api/v1/transactions")
    assert tx_resp.status_code == 200
    txs = tx_resp.json()["items"]
    assert any(t["authority"] == ref_id and t["amount_rial"] == 750000 for t in txs)

    # 2. Checkout view
    checkout_resp = client.get(f"/behpardakht/checkout/{ref_id}")
    assert checkout_resp.status_code == 200
    assert "750,000" in checkout_resp.text
    assert "<input" not in checkout_resp.text.lower()

    # 3. Checkout confirm -> 302 redirect
    confirm_resp = client.post(
        f"/behpardakht/checkout/{ref_id}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302
    location = confirm_resp.headers["location"]
    assert "ResCode=0" in location
    assert f"RefId={ref_id}" in location
    assert "SaleOrderId=2001" in location

    # 4. bpPaymentVerification
    verify_result = zeep_client.service.bpPaymentVerification(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=2001,
        saleOrderId=2001,
        saleReferenceId=int(ref_id),
    )
    assert verify_result == 0


def test_behpardakht_decline_and_reverse(client: TestClient):
    # 1. Decline scenario via X-Sandbox-Scenario header
    zeep_decline = _get_zeep_client(client, extra_headers={"X-Sandbox-Scenario": "decline"})

    res = zeep_decline.service.bpPaymentRequest(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=3001,
        amount=100000,
        localDate="20260928",
        localTime="120000",
        additionalData="",
        callBackUrl="http://localhost:3000/callback",
        payerId=0,
    )
    assert res.ResCode == 0
    ref_id = res.RefId

    # Verify fails per decline scenario
    verify_res = zeep_decline.service.bpPaymentVerification(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=3001,
        saleOrderId=3001,
        saleReferenceId=int(ref_id),
    )
    assert verify_res == 11

    # 2. Refund scenario
    zeep_refund = _get_zeep_client(client, extra_headers={"X-Sandbox-Scenario": "refund"})
    refund_init = zeep_refund.service.bpPaymentRequest(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=4001,
        amount=200000,
        localDate="20260928",
        localTime="120000",
        additionalData="",
        callBackUrl="http://localhost:3000/callback",
        payerId=0,
    )
    refund_ref_id = refund_init.RefId

    # Confirm checkout
    client.post(
        f"/behpardakht/checkout/{refund_ref_id}",
        data={"action": "confirm"},
        follow_redirects=False,
    )

    # Verify moves to approved
    v_res = zeep_refund.service.bpPaymentVerification(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=4001,
        saleOrderId=4001,
        saleReferenceId=int(refund_ref_id),
    )
    assert v_res == 0

    # Reverse transaction
    rev_res = zeep_refund.service.bpReverseTransaction(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=4001,
        saleOrderId=4001,
        saleReferenceId=int(refund_ref_id),
    )
    assert rev_res == 0


def test_behpardakht_unsupported_operation_envelope(client: TestClient):
    # Post raw SOAP with an unsupported operation tag
    raw_soap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">\n'
        "  <soapenv:Body>\n"
        '    <bpInquiryRequest xmlns="http://interfaces.core.sw.bps.com/">\n'
        "      <orderId>999</orderId>\n"
        "    </bpInquiryRequest>\n"
        "  </soapenv:Body>\n"
        "</soapenv:Envelope>"
    )
    resp = client.post(
        "/behpardakht/MellatPaymentGateway",
        content=raw_soap,
        headers={"Content-Type": "text/xml"},
    )
    assert resp.status_code == 500
    assert "sandbox:UnsupportedOperation" in resp.text
    assert "bpInquiryRequest" in resp.text


def test_behpardakht_malformed_xml_fault(client: TestClient):
    """A completely broken request body must return a SOAP Fault, not a 500 stack trace."""
    resp = client.post(
        "/behpardakht/MellatPaymentGateway",
        content=b"<not-even-xml",
        headers={"Content-Type": "text/xml"},
    )
    assert resp.status_code == 500
    assert "Fault" in resp.text
    assert "MalformedXml" in resp.text
