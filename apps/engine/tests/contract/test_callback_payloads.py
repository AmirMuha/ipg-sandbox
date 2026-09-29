"""Golden snapshot contract tests for callback payloads (T035).

Contracts: specs/001-mvp/contracts/adapter-surfaces.md §4.
Pins one golden payload per (adapter × stage) with real gateway field names. Drift fails CI.
"""

from uuid import UUID

import pytest

from src.adapters.base import (
    STAGE_NOTIFY,
    STAGE_REFUND,
    STAGE_SETTLE,
)
from src.models import (
    AdapterConfig,
    ApiUnit,
    Provider,
    Transaction,
    TransactionStatus,
)
from src.webhooks.payloads import payload_for

FIXED_ID = UUID("11111111-1111-1111-1111-111111111111")
FIXED_AUTHORITY = "auth-123"
FIXED_AMOUNT_RIAL = 250000
FIXED_APP_REF = "999"

# Fields that vary on each execution (e.g. wall-clock timestamps)
_VOLATILE_KEYS = {"date"}


def _make_tx(status: TransactionStatus) -> Transaction:
    return Transaction(
        id=FIXED_ID,
        authority=FIXED_AUTHORITY,
        amount_rial=FIXED_AMOUNT_RIAL,
        app_reference=FIXED_APP_REF,
        status=status,
    )


GOLDEN_PAYLOADS = {
    ("zarinpal", STAGE_SETTLE): {
        "Status": "OK",
        "Authority": "auth-123",
        "RefID": 350000,
        "PaymentID": "PID-11111111-1111-1111-1111-111111111111",
    },
    ("zarinpal", STAGE_NOTIFY): {
        "Status": "OK",
        "Authority": "auth-123",
        "RefID": 350000,
        "PaymentID": "PID-11111111-1111-1111-1111-111111111111",
    },
    ("zarinpal", STAGE_REFUND): {
        "Status": "OK",
        "Authority": "auth-123",
        "RefID": 350000,
    },
    ("idpay", STAGE_SETTLE): {
        "status": 100,
        "track_id": 350000,
        "id": "auth-123",
        "order_id": "999",
        "amount": 25000,
        "card_no": "502229******1234",
        "hashed_card_no": "21EC2020-3AEA-4069-A2DD-08002B30309D",
    },
    ("idpay", STAGE_NOTIFY): {
        "status": 100,
        "track_id": 350000,
        "id": "auth-123",
        "order_id": "999",
        "amount": 25000,
        "card_no": "502229******1234",
        "hashed_card_no": "21EC2020-3AEA-4069-A2DD-08002B30309D",
    },
    ("idpay", STAGE_REFUND): {
        "status": 100,
        "track_id": 350000,
        "id": "auth-123",
        "order_id": "999",
        "amount": 25000,
        "card_no": "502229******1234",
        "hashed_card_no": "21EC2020-3AEA-4069-A2DD-08002B30309D",
    },
    ("behpardakht", STAGE_SETTLE): {
        "ResCode": 0,
        "RefId": "auth-123",
        "SaleOrderId": 999,
        "SaleReferenceId": 350000,
    },
    ("behpardakht", STAGE_NOTIFY): {
        "ResCode": 0,
        "RefId": "auth-123",
        "SaleOrderId": 999,
        "SaleReferenceId": 350000,
    },
    ("behpardakht", STAGE_REFUND): {
        "ResCode": 0,
        "RefId": "auth-123",
        "SaleOrderId": 999,
        "SaleReferenceId": 350000,
    },
}


@pytest.mark.parametrize(
    ("provider", "api_unit", "stage", "status"),
    [
        (Provider.zarinpal, ApiUnit.rial, STAGE_SETTLE, TransactionStatus.settled),
        (Provider.zarinpal, ApiUnit.rial, STAGE_NOTIFY, TransactionStatus.settled),
        (Provider.zarinpal, ApiUnit.rial, STAGE_REFUND, TransactionStatus.refunded),
        (Provider.idpay, ApiUnit.toman, STAGE_SETTLE, TransactionStatus.settled),
        (Provider.idpay, ApiUnit.toman, STAGE_NOTIFY, TransactionStatus.settled),
        (Provider.idpay, ApiUnit.toman, STAGE_REFUND, TransactionStatus.refunded),
        (Provider.behpardakht, ApiUnit.rial, STAGE_SETTLE, TransactionStatus.settled),
        (Provider.behpardakht, ApiUnit.rial, STAGE_NOTIFY, TransactionStatus.settled),
        (Provider.behpardakht, ApiUnit.rial, STAGE_REFUND, TransactionStatus.refunded),
    ],
    ids=[
        "zarinpal-settle",
        "zarinpal-notify",
        "zarinpal-refund",
        "idpay-settle",
        "idpay-notify",
        "idpay-refund",
        "behpardakht-settle",
        "behpardakht-notify",
        "behpardakht-refund",
    ],
)
def test_golden_callback_payload(provider, api_unit, stage, status):
    config = AdapterConfig(provider=provider, api_unit=api_unit)
    tx = _make_tx(status)
    payload = payload_for(config, stage, tx)

    # Exclude volatile fields
    non_volatile = {k: v for k, v in payload.items() if k not in _VOLATILE_KEYS}
    expected = GOLDEN_PAYLOADS[(provider.value, stage)]
    assert non_volatile == expected

    # If IDPay, assert date format
    if provider == Provider.idpay:
        assert "date" in payload
        assert len(payload["date"]) == 14  # %Y%m%d%H%M%S
        assert payload["date"].isdigit()
