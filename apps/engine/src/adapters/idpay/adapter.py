"""IDPay emulated adapter (T022) — contracts/adapter-surfaces.md §2."""

import uuid
from datetime import datetime, timezone
from typing import Any

from src.adapters.base import (
    CallbackStage,
    PaymentAdapter,
    from_rial,
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


class IDPayAdapter(PaymentAdapter):
    """IDPay REST-style emulated gateway."""

    provider = Provider.idpay
    api_unit = ApiUnit.toman
    endpoint_path_prefix = "/idpay"
    credential_scheme = ("api_key",)

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
        """Initiate payment and return emulated ID + sandbox start URL."""
        self.check_credentials()
        pay_id = uuid.uuid4().hex
        tx.authority = pay_id
        return {
            "id": pay_id,
            "link": f"{self.endpoint_path_prefix}/payment/start/{pay_id}",
        }

    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify payment outcome per tx.effective_scenario."""
        amount_toman = from_rial(tx.amount_rial, self.api_unit)
        track_id = 100000 + (tx.amount_rial % 900000)

        if tx.status == TransactionStatus.settled:
            return {
                "status": 101,
                "track_id": track_id,
                "id": tx.authority,
                "order_id": tx.app_reference or "",
                "amount": amount_toman,
                "card_no": "502229******1234",
                "hashed_card_no": "21EC2020-3AEA-4069-A2DD-08002B30309D",
                "date": datetime.now(timezone.utc).isoformat(),
            }

        await apply_verify_outcome(tx)

        if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
            return {
                "status": 50,
                "error_code": 50,
                "error_message": "Payment failed / declined",
            }

        if tx.effective_scenario == ScenarioOutcome.refund:
            return {
                "status": 100,
                "track_id": track_id,
                "id": tx.authority,
                "order_id": tx.app_reference or "",
                "amount": amount_toman,
                "card_no": "502229******1234",
                "hashed_card_no": "21EC2020-3AEA-4069-A2DD-08002B30309D",
                "date": datetime.now(timezone.utc).isoformat(),
            }

        return {
            "status": 100,
            "track_id": track_id,
            "id": tx.authority,
            "order_id": tx.app_reference or "",
            "amount": amount_toman,
            "card_no": "502229******1234",
            "hashed_card_no": "21EC2020-3AEA-4069-A2DD-08002B30309D",
            "date": datetime.now(timezone.utc).isoformat(),
        }

    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Post-settle refund."""
        if tx.status in (TransactionStatus.settled, TransactionStatus.approved):
            tx.transition_to(TransactionStatus.refunded)
            track_id = 100000 + (tx.amount_rial % 900000)
            return {
                "status": 200,
                "track_id": track_id,
                "message": "Payment refunded successfully",
            }
        return {
            "status": 51,
            "error_code": 51,
            "error_message": "Refund not allowed for current transaction status",
        }

    async def checkout_page(self, tx: Transaction, lang: str = "fa") -> str:
        """Render hosted checkout page."""
        return render_checkout_page(
            tx,
            provider_name="آیدی پی (IDPay)",
            action_url=f"{self.endpoint_path_prefix}/payment/start/{tx.authority}",
            lang=lang,
        )

    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Return golden callback payload matching real IDPay fields."""
        track_id = 100000 + (tx.amount_rial % 900000)
        status_num = (
            100
            if tx.status
            in (
                TransactionStatus.settled,
                TransactionStatus.pending,
                TransactionStatus.approved,
                TransactionStatus.refunded,
            )
            else 50
        )
        amount_toman = from_rial(tx.amount_rial, self.api_unit)
        payload: dict[str, Any] = {
            "status": status_num,
            "track_id": track_id,
            "id": tx.authority,
            "order_id": tx.app_reference or "",
            "amount": amount_toman,
            "card_no": "502229******1234",
            "hashed_card_no": "21EC2020-3AEA-4069-A2DD-08002B30309D",
            "date": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        }
        return payload
