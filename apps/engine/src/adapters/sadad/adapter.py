"""Sadad Bank Melli emulated adapter (T010) — contracts/adapter-surfaces.md §1.2."""

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


class SadadAdapter(PaymentAdapter):
    """Sadad Bank Melli emulated gateway."""

    provider = Provider.sadad
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/sadad"
    credential_scheme = ("terminal_id", "merchant_id", "terminal_key")
    callback_transport = TRANSPORT_FORM_POST

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        has_term = creds.get("terminal_id") or creds.get("TerminalId")
        has_merch = creds.get("merchant_id") or creds.get("MerchantId")
        if not (has_term and has_merch):
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
            "ResCode": 0,
            "Token": token,
            "Description": "Success",
            "url": f"{self.endpoint_path_prefix}/checkout/{token}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        meta = card_metadata(self.provider, tx)
        if is_already_verified(tx):
            return {
                "ResCode": get_duplicate_verify_code(self.provider),
                "Description": "Already verified",
                "RetrivalReferenceNumber": meta["rrn"],
                "RetrivalRefNo": meta["rrn"],
                "SystemTraceNo": meta["trace_no"],
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            mapping = get_scenario_response(self.provider, tx.effective_scenario)
            return {
                "ResCode": mapping["code"],
                "Description": mapping["message"],
            }

        return {
            "ResCode": 0,
            "Amount": tx.amount_rial,
            "Description": "Success",
            "RetrivalReferenceNumber": meta["rrn"],
            "RetrivalRefNo": meta["rrn"],
            "SystemTraceNo": meta["trace_no"],
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"ResCode": 0, "Description": "Refunded"}
        return {"ResCode": -1, "Description": "Refund not allowed"}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="سداد (بانک ملی)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
            provider=self.provider,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return callback payload matching real Sadad fields."""
        is_ok = tx.status in (
            TransactionStatus.settled,
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.refunded,
        )
        meta = card_metadata(self.provider, tx)
        return {
            "ResCode": 0 if is_ok else 101,
            "OrderId": tx.app_reference or "",
            "Token": tx.authority,
            "RetrivalReferenceNumber": meta["rrn"],
            "SystemTraceNo": meta["trace_no"],
            "Amount": tx.amount_rial,
        }
