"""Behpardakht (Mellat) emulated adapter (T023) — contracts/adapter-surfaces.md §3."""

import random
from typing import Any

from src.adapters.base import (
    CallbackStage,
    PaymentAdapter,
)
from src.api.errors import ApiError, ErrorCode
from src.checkout.page import render_checkout_page
from src.models import (
    ApiUnit,
    Provider,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
)
from src.scenarios.adapter_mappings import get_duplicate_verify_code
from src.scenarios.outcomes import apply_verify_outcome
from src.services.transactions import is_already_verified


class BehpardakhtAdapter(PaymentAdapter):
    """Behpardakht (Mellat) SOAP-style emulated gateway."""

    provider = Provider.behpardakht
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/behpardakht"
    credential_scheme = ("terminal_id", "username", "password")

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        # Accept snake_case or camelCase keys
        has_term = creds.get("terminal_id") or creds.get("terminalId")
        has_user = creds.get("username") or creds.get("userName")
        has_pass = creds.get("password") or creds.get("userPassword")
        if not (has_term and has_user and has_pass):
            raise ApiError(
                ErrorCode.invalid_credentials,
                f"Missing required credentials: {self.credential_scheme}",
                status=401,
            )

    async def create_payment(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Initiate payment and return emulated RefId + checkout URL."""
        self.check_credentials()
        ref_id = str(random.randint(100000000000, 999999999999))
        tx.authority = ref_id
        return {
            "ResCode": 0,
            "RefId": ref_id,
            "RedirectUrl": f"http://localhost:8080{self.endpoint_path_prefix}/checkout/{ref_id}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        if is_already_verified(tx):
            return {"ResCode": get_duplicate_verify_code(self.provider)}

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            return {"ResCode": 11}

        return {"ResCode": 0}

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle reverse/refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            return {"ResCode": 0}
        return {"ResCode": 45}

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="به‌پرداخت ملت (Behpardakht Mellat)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return golden callback payload matching real Mellat fields."""
        res_code = (
            0
            if tx.status
            in (
                TransactionStatus.settled,
                TransactionStatus.pending,
                TransactionStatus.approved,
                TransactionStatus.refunded,
            )
            else 11
        )
        sale_ref_id = 100000 + (tx.amount_rial % 900000)
        sale_order_id = (
            int(tx.app_reference) if tx.app_reference and tx.app_reference.isdigit() else 0
        )
        return {
            "ResCode": res_code,
            "RefId": tx.authority,
            "SaleOrderId": sale_order_id,
            "SaleReferenceId": sale_ref_id,
        }
