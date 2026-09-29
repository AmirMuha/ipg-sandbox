"""Per-adapter callback payload resolution (T038) — research R7, adapter-surfaces.md §4.

The builders themselves live on each adapter (`PaymentAdapter.callback_payload`); this module
maps a `Transaction`'s AdapterConfig to the class that owns the right field names, so the
worker and the contract tests can ask what gateway X sends at stage Y.
"""

from typing import Any

from src.adapters.behpardakht.adapter import BehpardakhtAdapter
from src.adapters.idpay.adapter import IDPayAdapter
from src.adapters.zarinpal.adapter import ZarinpalAdapter
from src.models import AdapterConfig, Provider, Transaction

ADAPTER_CLASSES = {
    Provider.zarinpal: ZarinpalAdapter,
    Provider.idpay: IDPayAdapter,
    Provider.behpardakht: BehpardakhtAdapter,
}


def payload_for(config: AdapterConfig, stage: str, tx: Transaction) -> dict[str, Any]:
    """Build `tx`'s callback payload in the real gateway's field names."""
    adapter_cls = ADAPTER_CLASSES[config.provider]
    return adapter_cls(config).callback_payload(stage, tx)
