"""SC-003: 6 outcomes x 3 adapters, contract-defined response per cell (T028).

quickstart §3 wants 18/18 green and exit 0. The expected wire body and final status live in
`EXPECTED` so a cell's contract is one readable row, and the driver is shared so all 18 walk the
same initiate -> checkout -> verify path an app under test would.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.models import ScenarioOutcome
from tests.contract.test_behpardakht_surface import _get_zeep_client


@dataclass(frozen=True)
class Cell:
    adapter: str
    scenario: str
    expect_verify: Any  # dict for Zarinpal/IDPay or int ResCode for Behpardakht
    expect_status: str
    terminal: str | None = None


# ponytail: decline and verify_fail share the same gateway failure codes because that is what
# real gateways return — the difference is whether checkout succeeded first.
EXPECTED = [
    # Zarinpal (6)
    Cell("zarinpal", "approve", {"code": 100}, "settled"),
    Cell("zarinpal", "decline", {"code": -51}, "declined"),
    Cell("zarinpal", "verify_fail", {"code": -51}, "declined"),
    Cell("zarinpal", "refund", {"code": 100}, "approved", terminal="refunded"),
    Cell("zarinpal", "timeout", {"code": -33}, "failed"),
    Cell("zarinpal", "pending_settle", {"code": 100}, "settled"),
    # IDPay (6)
    Cell("idpay", "approve", {"status": 100}, "settled"),
    Cell("idpay", "decline", {"status": 50}, "declined"),
    Cell("idpay", "verify_fail", {"status": 50}, "declined"),
    Cell("idpay", "refund", {"status": 100}, "approved", terminal="refunded"),
    Cell("idpay", "timeout", {"error_code": 51}, "failed"),
    Cell("idpay", "pending_settle", {"status": 100}, "settled"),
    # Behpardakht (6)
    Cell("behpardakht", "approve", 0, "settled"),
    Cell("behpardakht", "decline", 11, "declined"),
    Cell("behpardakht", "verify_fail", 11, "declined"),
    Cell("behpardakht", "refund", 0, "approved", terminal="refunded"),
    Cell("behpardakht", "timeout", 59, "failed"),
    Cell("behpardakht", "pending_settle", 0, "settled"),
]


def test_matrix_is_6_outcomes_by_3_adapters():
    """Whole-matrix guard: SC-003 requires all 18 cells to be accounted for."""
    assert len(EXPECTED) == 18
    assert {c.adapter for c in EXPECTED} == {"zarinpal", "idpay", "behpardakht"}
    assert {c.scenario for c in EXPECTED} == {s.value for s in ScenarioOutcome}


@pytest.fixture(autouse=True)
def fast_delays(client: TestClient):
    """Set project delays to 0s so the 18-cell matrix runs fast."""
    client.patch(
        "/api/v1/project",
        json={"pending_settle_delay_s": 0, "timeout_delay_s": 0},
    )
    yield
    client.patch(
        "/api/v1/project",
        json={"pending_settle_delay_s": 5, "timeout_delay_s": 30},
    )


@pytest.mark.parametrize("cell", EXPECTED, ids=[f"{c.adapter}-{c.scenario}" for c in EXPECTED])
def test_scenario_matrix_cell(client: TestClient, cell: Cell):
    """Execute lifecycle for one cell of the 18-outcome matrix."""
    final_status = cell.terminal or cell.expect_status

    if cell.adapter == "zarinpal":
        # 1. Initiate
        init_resp = client.post(
            "/zarinpal/request/payment",
            headers={"X-Sandbox-Scenario": cell.scenario},
            json={
                "merchant_id": "test-merchant",
                "amount": 25000,
                "return_url": "http://localhost:3000/return",
                "description": f"matrix-{cell.scenario}",
            },
        )
        assert init_resp.status_code == 200
        init_data = init_resp.json()

        if cell.scenario == "timeout":
            assert init_data["code"] == -33
            # Check transaction status in control API
            txs = client.get("/api/v1/transactions").json()["items"]
            assert txs[0]["status"] == "failed"
            assert txs[0]["effective_scenario"] == "timeout"
            return

        authority = init_data["authority"]

        # 2. Checkout confirm
        confirm_resp = client.post(
            f"/zarinpal/checkout/{authority}",
            data={"action": "confirm"},
            follow_redirects=False,
        )
        assert confirm_resp.status_code == 302

        # 3. Verify
        verify_resp = client.post(
            "/zarinpal/payment/verification",
            json={"authority": authority},
        )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["code"] == cell.expect_verify["code"]

        # 4. Refund if applicable
        if cell.scenario == "refund":
            refund_resp = client.post(
                "/zarinpal/payment/refund",
                json={"authority": authority},
            )
            assert refund_resp.status_code == 200
            assert refund_resp.json()["code"] == 100

        # 5. Check final status
        txs = client.get("/api/v1/transactions").json()["items"]
        matched = next(t for t in txs if t["authority"] == authority)
        assert matched["status"] == final_status

    elif cell.adapter == "idpay":
        # 1. Initiate
        init_resp = client.post(
            "/idpay/payment",
            headers={"X-Sandbox-Scenario": cell.scenario, "X-API-KEY": "test-idpay-key"},
            json={
                "order_id": f"idpay-{cell.scenario}",
                "amount": 5000,
                "callback": "http://localhost:3000/callback",
            },
        )
        assert init_resp.status_code == 200
        init_data = init_resp.json()

        if cell.scenario == "timeout":
            assert init_data["error_code"] == 51
            txs = client.get("/api/v1/transactions").json()["items"]
            assert txs[0]["status"] == "failed"
            return

        pay_id = init_data["id"]

        # 2. Checkout confirm
        confirm_resp = client.post(
            f"/idpay/payment/start/{pay_id}",
            data={"action": "confirm"},
            follow_redirects=False,
        )
        assert confirm_resp.status_code == 302

        # 3. Verify
        verify_resp = client.post(
            "/idpay/payment/verify",
            json={"id": pay_id, "order_id": f"idpay-{cell.scenario}"},
        )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["status"] == cell.expect_verify["status"]

        # 4. Refund if applicable
        if cell.scenario == "refund":
            refund_resp = client.post(
                "/idpay/payment/refund",
                json={"id": pay_id},
            )
            assert refund_resp.status_code == 200
            assert refund_resp.json()["status"] == 200

        # 5. Check final status
        txs = client.get("/api/v1/transactions").json()["items"]
        matched = next(t for t in txs if t["authority"] == pay_id)
        assert matched["status"] == final_status

    elif cell.adapter == "behpardakht":
        zeep = _get_zeep_client(client, extra_headers={"X-Sandbox-Scenario": cell.scenario})
        order_num = 5000 + EXPECTED.index(cell)
        init_res = zeep.service.bpPaymentRequest(
            terminalId=123456,
            userName="sandbox",
            userPassword="sandbox",
            orderId=order_num,
            amount=500000,
            localDate="20260929",
            localTime="120000",
            additionalData="behpardakht-matrix",
            callBackUrl="http://localhost:3000/callback",
            payerId=0,
        )

        if cell.scenario == "timeout":
            assert init_res.ResCode == 59
            txs = client.get("/api/v1/transactions").json()["items"]
            assert txs[0]["status"] == "failed"
            return

        assert init_res.ResCode == 0
        ref_id = init_res.RefId

        # 2. Checkout confirm
        confirm_resp = client.post(
            f"/behpardakht/checkout/{ref_id}",
            data={"action": "confirm"},
            follow_redirects=False,
        )
        assert confirm_resp.status_code == 302

        # 3. Verify
        v_res = zeep.service.bpPaymentVerification(
            terminalId=123456,
            userName="sandbox",
            userPassword="sandbox",
            orderId=order_num,
            saleOrderId=order_num,
            saleReferenceId=int(ref_id),
        )
        assert v_res == cell.expect_verify

        # 4. Reverse if applicable
        if cell.scenario == "refund":
            rev_res = zeep.service.bpReverseTransaction(
                terminalId=123456,
                userName="sandbox",
                userPassword="sandbox",
                orderId=order_num,
                saleOrderId=order_num,
                saleReferenceId=int(ref_id),
            )
            assert rev_res == 0

        # 5. Check final status
        txs = client.get("/api/v1/transactions").json()["items"]
        matched = next(t for t in txs if t["authority"] == ref_id)
        assert matched["status"] == final_status
