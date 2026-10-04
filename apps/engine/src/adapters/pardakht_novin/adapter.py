"""Pardakht Novin Arian (PNA) emulated adapter (T020) — contracts/adapter-surfaces.md §2.2."""

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


class PardakhtNovinAdapter(PaymentAdapter):
    """Pardakht Novin Arian (PNA) emulated gateway."""

    provider = Provider.pardakht_novin
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/pardakht_novin"
    credential_scheme = ("merchant_id", "password")
    callback_transport = TRANSPORT_FORM_POST

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        has_merch = creds.get("merchant_id") or creds.get("merchantId") or creds.get("UserName")
        if not has_merch:
            raise ApiError(
                ErrorCode.invalid_credentials,
                f"Missing required credentials: {self.credential_scheme}",
                status=401,
            )

    async def create_payment(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Initiate payment and return token + checkout URL."""
        self.check_credentials()
        token = str(uuid.uuid4().hex[:12])
        tx.authority = token
        return {
            "Status": "0",
            "Token": token,
            "url": f"{self.endpoint_path_prefix}/checkout/{token}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        meta = card_metadata(self.provider, tx)
        if is_already_verified(tx):
            return {
                "Result": get_duplicate_verify_code(self.provider),
                "Amount": tx.amount_rial,
                "RRN": meta["rrn"],
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            code = get_scenario_response(self.provider, tx.effective_scenario)["code"]
            return {
                "Result": str(code),
                "Amount": tx.amount_rial,
                "RRN": meta["rrn"],
            }

        return {
            "Result": "0",
            "Amount": tx.amount_rial,
            "RRN": meta["rrn"],
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"Result": "0"}
        return {"Result": "-1"}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="پرداخت نوین آرین (PNA)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
            provider=self.provider,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return callback payload matching real Pardakht Novin fields."""
        is_ok = tx.status in (
            TransactionStatus.settled,
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.refunded,
        )
        meta = card_metadata(self.provider, tx)
        return {
            "RefNum": tx.authority,
            "ResNum": tx.app_reference or "",
            "State": "OK" if is_ok else "Canceled",
            "TraceNo": meta["trace_no"],
            "RRN": meta["rrn"],
            "Amount": tx.amount_rial,
        }
