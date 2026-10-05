"""Integration test: first approved payment end-to-end (T020) — quickstart.md §2."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from requests import Response
from zeep import Client

from src.models import TransactionStatus

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
WSDL_PATH = Path(__file__).parents[2] / "src" / "adapters" / "behpardakht" / "behpardakht.wsdl"


class ClientTransport:
    def __init__(self, client: TestClient):
        self.client = client

    def load(self, url: str) -> bytes:
        if "wsdl" in url.lower():
            resp = self.client.get("/behpardakht/MellatPaymentGateway?wsdl")
            return resp.content
        return WSDL_PATH.read_bytes()

    def post_xml(self, address: str, envelope, headers: dict) -> Response:
        from zeep.wsdl.utils import etree_to_string

        body = etree_to_string(envelope)
        r = self.client.post("/behpardakht/MellatPaymentGateway", content=body, headers=headers)
        response = Response()
        response.status_code = r.status_code
        response._content = r.content
        for k, v in r.headers.items():
            response.headers[k] = v
        return response


def test_first_payment_zarinpal_approved_flow(client: TestClient):
    """Quickstart §2: Zarinpal approved payment drop-in flow."""
    # 1. Initiate
    init_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "test-merchant",
            "amount": 10000,
            "currency": "IRR",
            "callback_url": "http://localhost:3000/callback",
            "description": "First test payment",
        },
    )
    assert init_resp.status_code == 200
    authority = init_resp.json()["authority"]
    assert authority

    # 2. Open hosted checkout view (FR-012: no card input fields)
    checkout_view = client.get(f"/zarinpal/checkout/{authority}")
    assert checkout_view.status_code == 200
    assert "10,000" in checkout_view.text
    assert "<input" not in checkout_view.text.lower()

    # 3. Press confirm on checkout -> redirect to callback URL with success params
    confirm_resp = client.post(
        f"/zarinpal/checkout/{authority}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302
    assert "Status=OK" in confirm_resp.headers["location"]
    assert f"Authority={authority}" in confirm_resp.headers["location"]

    # 4. Verify payment
    verify_resp = client.post(
        "/zarinpal/payment/verification",
        json={"merchant_id": "test-merchant", "authority": authority, "amount": 10000},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["code"] == 100

    # 5. Check control API: transaction settled, Rial canonical
    txs_resp = client.get("/api/v1/transactions")
    assert txs_resp.status_code == 200
    tx = next(t for t in txs_resp.json()["items"] if t["authority"] == authority)
    assert tx["status"] == TransactionStatus.settled.value
    assert tx["amount_rial"] == 10000


def test_first_payment_idpay_approved_flow(client: TestClient):
    """Quickstart §2: IDPay approved payment drop-in flow (Toman boundary conversion)."""
    # 1. Initiate with 1,000 Toman -> stored as 10,000 Rial canonical
    init_resp = client.post(
        "/idpay/payment",
        headers={"X-API-KEY": "test-idpay-key"},
        json={
            "order_id": "first-idpay-order",
            "amount": 1000,
            "callback": "http://localhost:3000/callback",
        },
    )
    assert init_resp.status_code == 200
    pay_id = init_resp.json()["id"]

    # 2. Checkout view
    checkout_resp = client.get(f"/idpay/payment/start/{pay_id}")
    assert checkout_resp.status_code == 200
    assert "10,000" in checkout_resp.text
    assert "<input" not in checkout_resp.text.lower()

    # 3. Confirm checkout -> 302 redirect
    confirm_resp = client.post(
        f"/idpay/payment/start/{pay_id}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302
    assert "status=10" in confirm_resp.headers["location"]

    # 4. Verify payment -> returned in Toman (1,000)
    verify_resp = client.post("/idpay/payment/verify", json={"id": pay_id})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == 100
    assert verify_resp.json()["amount"] == 1000

    # 5. Check control API
    txs_resp = client.get("/api/v1/transactions")
    assert txs_resp.status_code == 200
    tx = next(t for t in txs_resp.json()["items"] if t["authority"] == pay_id)
    assert tx["status"] == TransactionStatus.settled.value
    assert tx["amount_rial"] == 10000


def test_first_payment_behpardakht_approved_flow(client: TestClient):
    """Quickstart §2: Behpardakht SOAP approved payment drop-in flow."""
    zeep_client = Client(str(WSDL_PATH), transport=ClientTransport(client))
    zeep_client.settings.raw_response = False

    # 1. Initiate via SOAP bpPaymentRequest
    pay_req = zeep_client.service.bpPaymentRequest(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=5001,
        amount=10000,
        localDate="20260928",
        localTime="120000",
        additionalData="",
        callBackUrl="http://localhost:3000/callback",
        payerId=0,
    )
    assert pay_req.ResCode == 0
    ref_id = pay_req.RefId
    assert ref_id

    # 2. Checkout view
    checkout_view = client.get(f"/behpardakht/checkout/{ref_id}")
    assert checkout_view.status_code == 200
    assert "10,000" in checkout_view.text
    assert "<input" not in checkout_view.text.lower()

    # 3. Confirm checkout -> 302 redirect
    confirm_resp = client.post(
        f"/behpardakht/checkout/{ref_id}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302
    assert "ResCode=0" in confirm_resp.headers["location"]

    # 4. Verify via SOAP bpPaymentVerification
    verify_res = zeep_client.service.bpPaymentVerification(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=5001,
        saleOrderId=5001,
        saleReferenceId=int(ref_id),
    )
    assert verify_res == 0

    # 5. Check control API
    txs_resp = client.get("/api/v1/transactions")
    assert txs_resp.status_code == 200
    tx = next(t for t in txs_resp.json()["items"] if t["authority"] == ref_id)
    assert tx["status"] == TransactionStatus.settled.value
    assert tx["amount_rial"] == 10000


def test_transaction_lifecycle_when_gateway_withdrawn(client: TestClient, monkeypatch):
    """T034 (FR-011, FR-015, SC-005): in-flight completes after withdrawal; new init refused."""
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")

    # Enable idpay first
    # Using client, we simulate/initiate a transaction on zarinpal
    init_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "test-merchant",
            "amount": 10000,
            "currency": "IRR",
            "callback_url": "http://localhost:3000/callback",
            "description": "In-flight test payment",
        },
    )
    assert init_resp.status_code == 200
    authority = init_resp.json()["authority"]

    import asyncio

    from sqlalchemy import select

    from src.models import AdapterConfig, Provider

    factory = client.app.state.session_factory

    async def _disable_idpay():
        async with factory() as session:
            stmt = select(AdapterConfig).where(AdapterConfig.provider == Provider.idpay)
            adapter = await session.scalar(stmt)
            if adapter:
                adapter.enabled = False
                await session.commit()

    asyncio.run(_disable_idpay())

    # Now verify that simulate with a withdrawn gateway is refused
    bad_init = client.post(
        "/api/v1/transactions/simulate",
        json={
            "adapter": "idpay",
            "amount_rial": 10000,
            "forced_scenario": "approve",
        },
    )
    assert bad_init.status_code == 404

    # Now complete the in-flight zarinpal payment through checkout and verify
    confirm_resp = client.post(
        f"/zarinpal/checkout/{authority}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302

    verify_resp = client.post(
        "/zarinpal/payment/verification",
        json={"merchant_id": "test-merchant", "authority": authority, "amount": 10000},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["code"] == 100
