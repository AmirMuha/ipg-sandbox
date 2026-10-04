"""Universal gateway scenario mapping matrix (FR-008, T034).

Maps universal sandbox scenario outcomes to authentic gateway status codes and messages.
"""

from typing import Any, TypedDict
from src.models import Provider, ScenarioOutcome


class ScenarioResponse(TypedDict):
    code: Any
    message: str


# Scenario mappings per provider: outcome -> ScenarioResponse
SCENARIO_MAPPINGS: dict[Provider, dict[ScenarioOutcome, ScenarioResponse]] = {
    Provider.behpardakht: {
        ScenarioOutcome.approve: {"code": 0, "message": "Transaction Successful"},
        ScenarioOutcome.decline: {"code": 11, "message": "Card number is invalid"},
        ScenarioOutcome.timeout: {"code": 42, "message": "Transaction Timed Out"},
        ScenarioOutcome.refund: {"code": 0, "message": "Reversal Successful"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Transaction Authorized"},
        ScenarioOutcome.verify_fail: {"code": 45, "message": "Transaction Verification Failed"},
    },
    Provider.saman: {
        ScenarioOutcome.approve: {"code": 0, "message": "Success"},
        ScenarioOutcome.decline: {"code": -1, "message": "Transaction Failed or Canceled"},
        ScenarioOutcome.timeout: {"code": -3, "message": "Connection Timeout"},
        ScenarioOutcome.refund: {"code": 0, "message": "Reversed"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Pending Settlement"},
        ScenarioOutcome.verify_fail: {"code": -4, "message": "Verification Failed"},
    },
    Provider.sadad: {
        ScenarioOutcome.approve: {"code": 0, "message": "Success"},
        ScenarioOutcome.decline: {"code": 101, "message": "Transaction Declined"},
        ScenarioOutcome.timeout: {"code": 103, "message": "Timeout in Payment Process"},
        ScenarioOutcome.refund: {"code": 0, "message": "Refunded Successfully"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": -1, "message": "Invalid Transaction For Verification"},
    },
    Provider.parsian: {
        ScenarioOutcome.approve: {"code": 0, "message": "Successful"},
        ScenarioOutcome.decline: {"code": -1, "message": "Transaction Canceled by User"},
        ScenarioOutcome.timeout: {"code": -138, "message": "Timeout Exceeded"},
        ScenarioOutcome.refund: {"code": 0, "message": "Reversal Succeeded"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Awaiting Settlement"},
        ScenarioOutcome.verify_fail: {"code": -1, "message": "Confirm Failed"},
    },
    Provider.pasargad: {
        ScenarioOutcome.approve: {"code": 0, "message": "Success"},
        ScenarioOutcome.decline: {"code": 1, "message": "Declined by Customer or Bank"},
        ScenarioOutcome.timeout: {"code": -2, "message": "Session Expired"},
        ScenarioOutcome.refund: {"code": 0, "message": "Refund Succeeded"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": 1, "message": "Verification Not Allowed"},
    },
    Provider.asan_pardakht: {
        ScenarioOutcome.approve: {"code": 0, "message": "Success"},
        ScenarioOutcome.decline: {"code": -1, "message": "Payment Declined"},
        ScenarioOutcome.timeout: {"code": -2, "message": "Payment Timed Out"},
        ScenarioOutcome.refund: {"code": 0, "message": "Reverse Succeeded"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": -1, "message": "Verify Failed"},
    },
    Provider.pardakht_novin: {
        ScenarioOutcome.approve: {"code": "0", "message": "OK"},
        ScenarioOutcome.decline: {"code": "-1", "message": "Canceled"},
        ScenarioOutcome.timeout: {"code": "-2", "message": "Expired"},
        ScenarioOutcome.refund: {"code": "0", "message": "Reversed"},
        ScenarioOutcome.pending_settle: {"code": "0", "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": "-1", "message": "Verify Failed"},
    },
    Provider.irankish: {
        ScenarioOutcome.approve: {"code": "00", "message": "Success"},
        ScenarioOutcome.decline: {"code": "05", "message": "Do not honor"},
        ScenarioOutcome.timeout: {"code": "91", "message": "System error or timeout"},
        ScenarioOutcome.refund: {"code": "00", "message": "Refunded"},
        ScenarioOutcome.pending_settle: {"code": "00", "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": "12", "message": "Invalid transaction"},
    },
    Provider.sizpay: {
        ScenarioOutcome.approve: {"code": 0, "message": "Confirmed"},
        ScenarioOutcome.decline: {"code": -1, "message": "Declined"},
        ScenarioOutcome.timeout: {"code": -2, "message": "Timed out"},
        ScenarioOutcome.refund: {"code": 0, "message": "Refunded"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": -1, "message": "Verification failed"},
    },
    Provider.fanava: {
        ScenarioOutcome.approve: {"code": 0, "message": "Success"},
        ScenarioOutcome.decline: {"code": -1, "message": "Declined"},
        ScenarioOutcome.timeout: {"code": -2, "message": "Timeout"},
        ScenarioOutcome.refund: {"code": 0, "message": "Refunded"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": -1, "message": "Failed"},
    },
    Provider.sarmayeh: {
        ScenarioOutcome.approve: {"code": 0, "message": "Success"},
        ScenarioOutcome.decline: {"code": -1, "message": "Declined"},
        ScenarioOutcome.timeout: {"code": -2, "message": "Timeout"},
        ScenarioOutcome.refund: {"code": 0, "message": "Refunded"},
        ScenarioOutcome.pending_settle: {"code": 0, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": -1, "message": "Failed"},
    },
    Provider.zarinpal: {
        ScenarioOutcome.approve: {"code": 100, "message": "Verified"},
        ScenarioOutcome.decline: {"code": -9, "message": "Validation error or declined"},
        ScenarioOutcome.timeout: {"code": -10, "message": "IP or merchant invalid or timeout"},
        ScenarioOutcome.refund: {"code": 100, "message": "Refunded"},
        ScenarioOutcome.pending_settle: {"code": 100, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": -12, "message": "Payment not found or failed"},
    },
    Provider.idpay: {
        ScenarioOutcome.approve: {"code": 100, "message": "Payment confirmed"},
        ScenarioOutcome.decline: {"code": 10, "message": "Payment failed or canceled"},
        ScenarioOutcome.timeout: {"code": 3, "message": "Payment timed out"},
        ScenarioOutcome.refund: {"code": 100, "message": "Refunded"},
        ScenarioOutcome.pending_settle: {"code": 100, "message": "Authorized"},
        ScenarioOutcome.verify_fail: {"code": 10, "message": "Payment not verified"},
    },
}

# Native duplicate verification code per provider (FR-011, SC-006)
DUPLICATE_VERIFY_CODES: dict[Provider, Any] = {
    Provider.behpardakht: 43,
    Provider.saman: -6,
    Provider.sadad: 102,
    Provider.parsian: -1529,
    Provider.pasargad: -100,
    Provider.asan_pardakht: -6,
    Provider.pardakht_novin: "-6",
    Provider.irankish: "94",
    Provider.sizpay: -6,
    Provider.fanava: -6,
    Provider.sarmayeh: -6,
    Provider.zarinpal: 101,
    Provider.idpay: 101,
}


def get_scenario_response(provider: Provider, outcome: ScenarioOutcome) -> ScenarioResponse:
    """Return authentic code and message for `provider` and `outcome`."""
    mapping = SCENARIO_MAPPINGS.get(provider, {})
    return mapping.get(
        outcome,
        {"code": 0, "message": "Success"} if outcome == ScenarioOutcome.approve else {"code": -1, "message": "Failed"},
    )


def get_duplicate_verify_code(provider: Provider) -> Any:
    """Return native duplicate verification code for `provider`."""
    return DUPLICATE_VERIFY_CODES.get(provider, 101)
