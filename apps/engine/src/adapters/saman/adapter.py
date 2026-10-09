"""Saman Electronic Payment (SEP) emulated adapter (T008) — contracts/adapter-surfaces.md §1.1."""

import uuid
from typing import Any

from src.adapters.base import (
    TRANSPORT_FORM_POST,
    CallbackStage,
    PaymentAdapter,
)
from src.adapters.metadata import card_metadata
from src.api.errors import ApiError, ErrorCode
from src.checkout.page import render_checkout_page
from src.models import (
    ApiUnit,
    Provider,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
)
from src.scenarios.adapter_mappings import get_duplicate_verify_code, get_scenario_response
from src.scenarios.outcomes import apply_verify_outcome
from src.services.transactions import is_already_verified


class SamanAdapter(PaymentAdapter):
    """Saman Electronic Payment (SEP) emulated gateway."""

    provider = Provider.saman
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/saman"
    credential_scheme = ("terminal_id",)
    callback_transport = TRANSPORT_FORM_POST

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        has_term = creds.get("terminal_id") or creds.get("TerminalId")
        if not has_term:
            raise ApiError(
                ErrorCode.invalid_credentials,
                f"Missing required credentials: {self.credential_scheme}",
                status=401,
            )

    async def create_payment(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Initiate payment and return token + checkout URL."""
        self.check_credentials()
        token = str(uuid.uuid4())
        tx.authority = token
        return {
            "status": 1,
            "token": token,
            "errorCode": 0,
            "url": f"{self.endpoint_path_prefix}/checkout/{token}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        if is_already_verified(tx):
            return {
                "ResultCode": get_duplicate_verify_code(self.provider),
                "Status": get_duplicate_verify_code(self.provider),
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            code = get_scenario_response(self.provider, tx.effective_scenario)["code"]
            return {"ResultCode": code, "Status": code}

        return {
            "ResultCode": 0,
            "Status": 0,
            "TransactionDetail": {
                "Rrn": card_metadata(self.provider, tx)["rrn"],
                "RefNum": tx.authority,
                "MaskedPan": card_metadata(self.provider, tx)["card_pan"],
                "Amount": tx.amount_rial,
            },
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"ResultCode": 0, "Status": 0}
        return {"ResultCode": -1, "Status": -1}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="سامان کیش (SEP)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
            provider=self.provider,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return callback payload matching real SEP fields."""
        is_ok = tx.status in (
            TransactionStatus.settled,
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.refunded,
        )
        meta = card_metadata(self.provider, tx)
        return {
            "State": "OK" if is_ok else "Canceled",
            "Status": 0 if is_ok else -1,
            "RefNum": tx.authority,
            "ResNum": tx.app_reference or "",
            "MID": self.config.credentials.get("terminal_id", "12345678") if self.config.credentials else "12345678",
            "TraceNo": meta["trace_no"],
            "Rrn": meta["rrn"],
            "SecurePan": meta["card_pan"],
            "Amount": tx.amount_rial,
        }
