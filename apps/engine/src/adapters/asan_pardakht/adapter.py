"""Asan Pardakht (AP) emulated adapter (T016) — contracts/adapter-surfaces.md §1.5."""

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


class AsanPardakhtAdapter(PaymentAdapter):
    """Asan Pardakht (AP / آپ) emulated gateway."""

    provider = Provider.asan_pardakht
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/asan_pardakht"
    credential_scheme = ("merchant_id", "username", "password")
    callback_transport = TRANSPORT_FORM_POST

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        has_merch = creds.get("merchant_id") or creds.get("merchantId") or creds.get("merchantConfigurationId")
        if not has_merch:
            raise ApiError(
                ErrorCode.invalid_credentials,
                f"Missing required credentials: {self.credential_scheme}",
                status=401,
            )

    async def create_payment(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Initiate payment and return token + checkout URL."""
        self.check_credentials()
        token = str(uuid.uuid4().hex[:16])
        tx.authority = token
        return {
            "status": "Success",
            "token": token,
            "url": f"{self.endpoint_path_prefix}/checkout/{token}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        meta = card_metadata(self.provider, tx)
        if is_already_verified(tx):
            return {
                "status": "AlreadyVerified",
                "PayResult": get_duplicate_verify_code(self.provider),
                "rrn": meta["rrn"],
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            code = get_scenario_response(self.provider, tx.effective_scenario)["code"]
            return {
                "status": "Failed",
                "PayResult": code,
                "rrn": meta["rrn"],
            }

        return {
            "status": "Success",
            "amount": tx.amount_rial,
            "rrn": meta["rrn"],
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"status": "Success"}
        return {"status": "Failed"}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="آسان پرداخت (آپ)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
            provider=self.provider,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return callback payload matching real Asan Pardakht fields."""
        is_ok = tx.status in (
            TransactionStatus.settled,
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.refunded,
        )
        meta = card_metadata(self.provider, tx)
        return {
            "CardNumber": meta["card_pan"],
            "RRN": meta["rrn"],
            "TraceNumber": meta["trace_no"],
            "PayResult": 0 if is_ok else -1,
            "Amount": tx.amount_rial,
            "InvoiceNumber": tx.app_reference or "",
        }
