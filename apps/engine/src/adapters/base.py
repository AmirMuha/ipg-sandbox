"""Abstract emulated-adapter interface (T012) — research R2, contracts/adapter-surfaces.md.

Interface only: the three concrete adapters are T021–T023 (Phase 3). The five methods below are
the seam the engine drives every gateway through, and the three class attributes are what
`AdapterConfig` rows and the `/adapters` endpoint are built from.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from src.models import AdapterConfig, ApiUnit, Provider, Transaction

# contracts/adapter-surfaces.md stages + data-model.md's WebhookDelivery `stage` enum
# (`notify | settle | refund`). `callback_payload` switches on these.
CallbackStage = str
STAGE_INITIATE = "initiate"
STAGE_RETURN = "return"
STAGE_VERIFY = "verify"
STAGE_REFUND = "refund"
# Async callback points: `settle` fires on pending→settled, `notify` is the plain result
# notification. T038's per-adapter payload builders are keyed on these.
STAGE_SETTLE = "settle"
STAGE_NOTIFY = "notify"


class PaymentAdapter(ABC):
    """One emulated gateway.

    Subclasses are stateless per-request apart from `config`; the engine resolves an
    `AdapterConfig` row, hands it to the adapter, and drives the five methods.
    """

    #: `Provider` this adapter emulates — matches `AdapterConfig.provider`.
    provider: ClassVar[Provider]
    #: Unit the emulated API expects. Amounts cross this boundary here and are Rial canonical
    #: inside the engine (clarification 4), so adapters convert on the way in and out.
    api_unit: ClassVar[ApiUnit]
    #: Default mount path; `AdapterConfig.endpoint_path_prefix` overrides it per project.
    endpoint_path_prefix: ClassVar[str]
    #: Substrings that must appear in `AdapterConfig.credentials`, e.g. `("merchant_id",)`.
    credential_scheme: ClassVar[tuple[str, ...]]

    def __init__(self, config: AdapterConfig) -> None:
        self.config = config

    def check_credentials(self) -> None:
        """Raise `ApiError(invalid_credentials)` when configured creds do not match the scheme.

        Concrete adapters override; the default is a no-op so an adapter with no credentials
        (none in v1) does not have to write one.
        """
        return None

    @abstractmethod
    async def create_payment(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Initiate. Returns the wire response (emulated `authority`/`id`/`RefId` + start URL)."""

    @abstractmethod
    async def verify(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Verify/settle. Outcome follows `tx.effective_scenario` (research R5)."""

    @abstractmethod
    async def refund(self, tx: Transaction, request: dict[str, Any]) -> dict[str, Any]:
        """Refund/reverse. Only meaningful after settle — see the state machine in models."""

    @abstractmethod
    async def checkout_page(self, tx: Transaction) -> str:
        """Server-rendered hosted checkout HTML for this transaction (T024)."""

    @abstractmethod
    def callback_payload(self, stage: CallbackStage, tx: Transaction) -> dict[str, Any]:
        """Payload the adapter POSTs to the app's callback URL, in the *real* gateway's field
        names for `stage` (clarification 2). Sync: it is pure shaping, no I/O."""


def to_rial(amount: int, unit: ApiUnit) -> int:
    """Convert boundary amount into canonical Rial (clarification 4)."""
    return amount * 10 if unit == ApiUnit.toman else amount


def from_rial(amount_rial: int, unit: ApiUnit) -> int:
    """Convert canonical Rial to boundary unit (clarification 4)."""
    return amount_rial // 10 if unit == ApiUnit.toman else amount_rial
