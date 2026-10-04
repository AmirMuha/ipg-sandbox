"""Provider → adapter-class resolution, and seed specification (FR-002).

Two jobs, both here so the 13 gateways never need a shared hand-maintained list:

1. `resolve_adapter_class` — find the `PaymentAdapter` subclass for a `Provider` by importing
   `src.adapters.<provider>` and taking the subclass out of its `__all__` (every adapter package
   already exports exactly `["<X>Adapter", "router"]`). A provider whose module does not exist yet
   resolves to `None` rather than raising, so the engine boots and serves the implemented gateways
   while the rest are still being written.

2. `seed_configs` — derive each project's default `AdapterConfig` rows from the adapter classes
   themselves (`endpoint_path_prefix`, `api_unit`, `credential_scheme`) instead of a hardcoded
   table. Before this, `api/app.py` and `tests/conftest.py` each carried their own copy of the same
   three rows, and a new adapter that forgot its row answered `404 adapter <name> not found` to its
   own initiate call.
"""

import importlib
from functools import lru_cache
from typing import Any
from uuid import UUID

from src.models import Provider

#: The v1 rows used these exact values and existing contract tests assert on them, so they are
#: pinned here. Every other provider gets an obvious `sandbox-<key>` placeholder, which is honest
#: about being fake and is easy to spot in a dashboard's credentials box.
_PROD_CREDENTIALS: dict[Provider, dict[str, Any]] = {
    Provider.zarinpal: {"merchant_id": "sandbox-merchant"},
    Provider.idpay: {"api_key": "sandbox-key"},
    Provider.behpardakht: {"terminal_id": 123456, "username": "sandbox", "password": "sandbox"},
}


@lru_cache(maxsize=None)
def resolve_adapter_class(provider: Provider) -> type | None:
    """Return the `PaymentAdapter` subclass emulating `provider`, or `None` if not written yet.

    Only a missing *adapter package* is swallowed; an ImportError raised from inside an adapter
    module (a genuine bug) propagates, so it is not mistaken for "not implemented".
    """
    module_name = f"src.adapters.{provider.value}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return None
        raise

    # Imported here rather than at module scope: `base` imports `src.models`, and this module is
    # imported from `api.app` during startup.
    from src.adapters.base import PaymentAdapter

    for name in getattr(module, "__all__", ()):
        obj = getattr(module, name, None)
        if isinstance(obj, type) and issubclass(obj, PaymentAdapter) and obj is not PaymentAdapter:
            return obj
    return None


def seed_configs(
    project_id: UUID,
    credentials: dict[Provider, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Default `AdapterConfig` kwargs for every provider that has an adapter implementation.

    `credentials` overrides whole rows by provider; providers absent from it fall back to
    `_PROD_CREDENTIALS`, then to a placeholder per key in the class's `credential_scheme`.
    """
    overrides = credentials or {}
    rows: list[dict[str, Any]] = []

    for provider in Provider:
        adapter_cls = resolve_adapter_class(provider)
        if adapter_cls is None:
            continue

        if provider in overrides:
            creds = overrides[provider]
        elif provider in _PROD_CREDENTIALS:
            creds = _PROD_CREDENTIALS[provider]
        else:
            creds = {key: f"sandbox-{key}" for key in adapter_cls.credential_scheme}

        rows.append(
            {
                "project_id": project_id,
                "provider": provider,
                "endpoint_path_prefix": adapter_cls.endpoint_path_prefix,
                "api_unit": adapter_cls.api_unit,
                "credentials": creds,
            }
        )

    return rows
