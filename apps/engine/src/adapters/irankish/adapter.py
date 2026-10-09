"""IranKish emulated adapter (T022) — contracts/adapter-surfaces.md §2.3."""

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


class IranKishAdapter(PaymentAdapter):
    """IranKish emulated gateway."""

    provider = Provider.irankish
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/irankish"
    credential_scheme = ("terminal_id", "acceptor_id", "pass_phrase")
    callback_transport = TRANSPORT_FORM_POST

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        has_term = creds.get("terminal_id") or creds.get("terminalId")
        if not has_term:
            raise ApiError(
                ErrorCode.invalid_credentials,
                f"Missing required credentials: {self.credential_scheme}",
                status=401,
            )

    async def create_payment(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Initiate payment and return token + checkout URL."""
        self.check_credentials()
        token = str(uuid.uuid4().hex)
        tx.authority = token
        return {
            "status": True,
            "resultCode": "00",
            "token": token,
            "url": f"{self.endpoint_path_prefix}/checkout/{token}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        if is_already_verified(tx):
            return {
                "status": False,
                "resultCode": get_duplicate_verify_code(self.provider),
                "description": "Duplicate verification",
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            code = get_scenario_response(self.provider, tx.effective_scenario)["code"]
            return {
                "status": False,
                "resultCode": str(code),
            }

        return {
            "status": True,
            "resultCode": "00",
            "amount": tx.amount_rial,
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"status": True, "resultCode": "00"}
        return {"status": False, "resultCode": "-1"}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="کارت اعتباری ایران‌کیش",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
            provider=self.provider,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return callback payload matching real IranKish fields."""
        is_ok = tx.status in (
            TransactionStatus.settled,
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.refunded,
        )
        meta = card_metadata(self.provider, tx)
        return {
            "token": tx.authority,
            "resultCode": "00" if is_ok else "05",
            "referenceId": meta["trace_no"],
            "retrievalReferenceNumber": meta["rrn"],
            "maskedPan": meta["card_pan"],
            "amount": tx.amount_rial,
        }
