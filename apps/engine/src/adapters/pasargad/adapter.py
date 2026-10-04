"""Pasargad PEP emulated adapter (T014) — contracts/adapter-surfaces.md §1.4."""

import uuid
from typing import Any

from src.adapters.base import (
    CallbackStage,
    PaymentAdapter,
    TRANSPORT_FORM_POST,
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


class PasargadAdapter(PaymentAdapter):
    """Pasargad PEP REST-style emulated gateway."""

    provider = Provider.pasargad
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/pasargad"
    credential_scheme = ("merchant_code", "terminal_code")
    callback_transport = TRANSPORT_FORM_POST

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        has_merch = creds.get("merchant_code") or creds.get("merchantCode")
        has_term = creds.get("terminal_code") or creds.get("terminalCode")
        if not (has_merch and has_term):
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
            "resultCode": 0,
            "result": "Success",
            "token": token,
            "url": f"http://localhost:8080{self.endpoint_path_prefix}/checkout/{token}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        meta = card_metadata(self.provider, tx)
        if is_already_verified(tx):
            return {
                "resultCode": get_duplicate_verify_code(self.provider),
                "result": "Already verified",
                "referenceNumber": meta["rrn"],
                "trackId": meta["trace_no"],
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            mapping = get_scenario_response(self.provider, tx.effective_scenario)
            return {
                "resultCode": mapping["code"],
                "result": mapping["message"],
            }

        return {
            "resultCode": 0,
            "result": "Success",
            "amount": tx.amount_rial,
            "referenceNumber": meta["rrn"],
            "trackId": meta["trace_no"],
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"resultCode": 0, "result": "Success"}
        return {"resultCode": -1, "result": "Refund failed"}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="پرداخت الکترونیک پاسارگاد (PEP)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
            provider=self.provider,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return callback payload matching real Pasargad PEP fields."""
        is_ok = tx.status in (
            TransactionStatus.settled,
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.refunded,
        )
        meta = card_metadata(self.provider, tx)
        return {
            "invoiceNumber": tx.app_reference or "",
            "invoiceDate": "2026-10-03",
            "transactionId": tx.authority,
            "referenceNumber": meta["rrn"],
            "trackId": meta["trace_no"],
            "status": 0 if is_ok else 1,
            "amount": tx.amount_rial,
        }
