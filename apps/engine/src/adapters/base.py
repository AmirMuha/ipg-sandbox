"""Abstract emulated-adapter interface (T012) — research R2, contracts/adapter-surfaces.md.

Interface only: the three concrete adapters are T021–T023 (Phase 3). The five methods below are
the seam the engine drives every gateway through, and the three class attributes are what
`AdapterConfig` rows and the `/adapters` endpoint are built from.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from src.api.errors import ApiError, ErrorCode
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

# How the emulated gateway hands the result back to the merchant (FR-005). Real gateways are not
# uniform about this and merchant code parses accordingly, so a sandbox that always answers JSON
# cannot exercise the callback parser a Shaparak app actually ships.
TRANSPORT_JSON_POST = "json_post"
TRANSPORT_FORM_POST = "form_post"
TRANSPORT_GET = "get"


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
    #: Transport the *callback* to the merchant uses (FR-005): a Shaparak PSP form-POSTs, a
    #: payment facilitator GETs with query params, some REST gateways post JSON.
    callback_transport: ClassVar[str] = TRANSPORT_JSON_POST

    def __init__(self, config: AdapterConfig) -> None:
        self.config = config

    def check_credentials(self) -> None:
        """Raise `ApiError(invalid_credentials)` when configured creds do not match the scheme.

        Concrete adapters override; the default is a no-op so an adapter with no credentials
        (none in v1) does not have to write one.
        """
        return None

    def verify_supplied_credentials(self, supplied: dict[str, Any]) -> None:
        """Reject request credentials that are absent, empty, or not the configured value.

        One implementation for every adapter (T080). Each route used to check only
        `supplied == ""`, so an omitted key fell through as `None` and any value at all was
        accepted — a wrong merchant still created a payment. Comparing against
        `AdapterConfig.credentials` is what `/api/v1/adapters/{id}/test` already implies.

        Skips a key the caller did not send when the adapter's own scheme does not require it,
        so an adapter with no credential requirement stays usable.
        """
        configured = self.config.credentials or {}
        for key in self.credential_scheme:
            expected = configured.get(key)
            if not expected:
                # Misconfigured adapter, not a bad request — `check_credentials` owns that.
                self.check_credentials()
                continue
            value = supplied.get(key)
            if not value:
                raise ApiError(
                    ErrorCode.invalid_credentials,
                    f"Missing or empty credential: {key}",
                    status=401,
                )
            if value != expected:
                raise ApiError(
                    ErrorCode.invalid_credentials,
                    f"Invalid credential value for {key}",
                    status=401,
                )

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


def unsupported_operation(provider: str, path: str) -> ApiError:
    """Explicit rejection for an operation this adapter does not emulate.

    T081: without a catch-all on the REST adapters, an unknown path fell through to FastAPI's
    default 404 and answered `{"code": "not_found"}` — indistinguishable from "you asked for the
    wrong URL" and never naming the adapter. `spec.md:108` and `contracts/adapter-surfaces.md:9`
    both require an explicit "not supported by this adapter".
    """
    return ApiError(
        ErrorCode.unsupported_operation,
        f"Operation not supported by the {provider} adapter: {path}",
        status=400,
    )
