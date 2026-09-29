"""Zarinpal emulated adapter (T021) — contracts/adapter-surfaces.md §1."""

import uuid
from typing import Any

from src.adapters.base import (
    STAGE_NOTIFY,
    STAGE_SETTLE,
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
from src.scenarios.outcomes import apply_verify_outcome


class ZarinpalAdapter(PaymentAdapter):
    """Zarinpal REST-style emulated gateway."""

    provider = Provider.zarinpal
    api_unit = ApiUnit.rial
    endpoint_path_prefix = "/zarinpal"
    credential_scheme = ("merchant_id",)

    def check_credentials(self) -> None:
        """Validate configured test credentials."""
        creds = self.config.credentials or {}
        if not all(k in creds and creds[k] for k in self.credential_scheme):
            raise ApiError(
                ErrorCode.invalid_credentials,
                f"Missing required credentials: {self.credential_scheme}",
                status=401,
            )

    async def create_payment(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Initiate payment and return authority + sandbox checkout URL."""
        self.check_credentials()
        authority = f"A{uuid.uuid4().hex}"
        tx.authority = authority
        return {
            "code": 100,
            "message": "Operation was successful",
            "authority": authority,
            "payment_url": f"{self.endpoint_path_prefix}/checkout/{authority}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        if tx.status == TransactionStatus.settled:
            ref_id = 100000 + (tx.amount_rial % 900000)
            return {
                "code": 101,
                "message": "Operation was successful (already verified)",
                "ref_id": ref_id,
                "card_pan": "502229******1234",
                "card_hash": "21EC2020-3AEA-4069-A2DD-08002B30309D",
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            return {
                "code": -51,
                "message": "Payment failed / declined",
            }

        ref_id = 100000 + (tx.amount_rial % 900000)
        if tx.effective_scenario == ScenarioOutcome.refund:
            return {
                "code": 100,
                "message": "Approved for refund",
                "ref_id": ref_id,
                "card_pan": "502229******1234",
                "card_hash": "21EC2020-3AEA-4069-A2DD-08002B30309D",
            }

        return {
            "code": 100,
            "message": "Verified",
            "ref_id": ref_id,
            "card_pan": "502229******1234",
            "card_hash": "21EC2020-3AEA-4069-A2DD-08002B30309D",
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle refund."""
        if tx.status == TransactionStatus.approved:
            tx.transition_to(TransactionStatus.refunded)
            ref_id = 100000 + (tx.amount_rial % 900000)
            return {
                "code": 100,
                "message": "Payment refunded successfully",
                "ref_id": ref_id,
            }
        return {
            "code": -50,
            "message": "Refund not allowed for current transaction status",
        }

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="زرین‌پال (Zarinpal)",
            action_url=f"{self.endpoint_path_prefix}/checkout/{tx.authority}",
            lang=lang,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return golden callback payload matching real Zarinpal fields."""
        ref_id = 100000 + (tx.amount_rial % 900000)
        status_str = (
            "OK"
            if tx.status
            in (
                TransactionStatus.settled,
                TransactionStatus.pending,
                TransactionStatus.approved,
                TransactionStatus.refunded,
            )
            else "NOK"
        )
        payload: dict[str, Any] = {
            "Status": status_str,
            "Authority": tx.authority,
            "RefID": ref_id,
        }
        if stage in (STAGE_SETTLE, STAGE_NOTIFY):
            payload["PaymentID"] = f"PID-{tx.id}"
        return payload
