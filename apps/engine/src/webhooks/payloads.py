"""Per-adapter callback payload resolution (T038) — research R7, adapter-surfaces.md §4.

The builders themselves live on each adapter (`PaymentAdapter.callback_payload`). This module
resolves a `Transaction`'s AdapterConfig to the class that owns the right field names.

Adapter classes resolve lazily via `src.adapters.registry.resolve_adapter_class`, so each new
gateway registers automatically without editing this file.
"""

from typing import Any

from src.adapters.registry import resolve_adapter_class
from src.models import AdapterConfig, Provider, Transaction


class _LazyAdapterMap:
    """Dict-like facade preserving `ADAPTER_CLASSES[provider]` access pattern."""

    def __getitem__(self, provider: Provider) -> type:
        cls = resolve_adapter_class(provider)
        if cls is None:
            raise KeyError(f"No adapter implementation found for provider: {provider}")
        return cls

    def __contains__(self, provider: object) -> bool:
        if not isinstance(provider, Provider):
            return False
        return resolve_adapter_class(provider) is not None

    def get(self, provider: Provider, default: Any = None) -> Any:
        cls = resolve_adapter_class(provider)
        return cls if cls is not None else default


ADAPTER_CLASSES = _LazyAdapterMap()


def payload_for(config: AdapterConfig, stage: str, tx: Transaction) -> dict[str, Any]:
    """Build `tx`'s callback payload in the real gateway's field names."""
    adapter_cls = ADAPTER_CLASSES[config.provider]
    return adapter_cls(config).callback_payload(stage, tx)
