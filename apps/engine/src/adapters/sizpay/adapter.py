"""SizPay emulated adapter (T030) — contracts/adapter-surfaces.md §3.3."""

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


class SizpayAdapter(PaymentAdapter):
    """SizPay Payment Facilitator emulated gateway."""

    provider = Provider.sizpay
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/sizpay"
    credential_scheme = ("merchant_id", "terminal_id", "username", "password")
    callback_transport = TRANSPORT_FORM_POST

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        has_merch = creds.get("merchant_id") or creds.get("MerchantID")
        has_term = creds.get("terminal_id") or creds.get("TerminalID")
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
            "ResCode": 0,
            "Message": "Success",
            "Token": token,
            "url": f"{self.endpoint_path_prefix}/checkout/{token}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        meta = card_metadata(self.provider, tx)
        if is_already_verified(tx):
            return {
                "ResCode": get_duplicate_verify_code(self.provider),
                "Message": "Already confirmed",
                "RefNo": meta["rrn"],
                "Amount": tx.amount_rial,
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            mapping = get_scenario_response(self.provider, tx.effective_scenario)
            return {
                "ResCode": mapping["code"],
                "Message": mapping["message"],
            }

        return {
            "ResCode": 0,
            "Message": "Confirmed",
            "RefNo": meta["rrn"],
            "Amount": tx.amount_rial,
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"ResCode": 0, "Message": "Refunded"}
        return {"ResCode": -1, "Message": "Refund failed"}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="سیزپی (SizPay)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
            provider=self.provider,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return callback payload matching real SizPay fields."""
        is_ok = tx.status in (
            TransactionStatus.settled,
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.refunded,
        )
        meta = card_metadata(self.provider, tx)
        return {
            "ResCode": 0 if is_ok else -1,
            "Token": tx.authority,
            "InvoiceNo": tx.app_reference or "",
            "RefNo": meta["rrn"],
            "CardNoMask": meta["card_pan"],
            "Amount": tx.amount_rial,
        }
