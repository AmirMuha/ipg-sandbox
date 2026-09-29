"""ORM models — spec: specs/001-mvp/data-model.md (T008).

Conventions worth knowing before editing:
- Timestamps are timezone-aware (`DateTime(timezone=True)` = timestamptz) and always UTC.
- `server_default` is raw SQL, so it needs `text(...)` — a bare Python default there breaks DDL.
- Numeric rules live in `CheckConstraint`s (DB-level = native rung of the ladder), not in
  `@validates` hooks, so a bad value fails on flush for every writer, not just the ORM.
- Types are Postgres-native (UUID/JSONB/ARRAY). `tests/unit/conftest.py` compiles them down to
  SQLite equivalents so the CHECK constraints can be executed for real in unit tests.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .enums import ApiUnit, ProjectKind, Provider, ScenarioOutcome, TransactionStatus

# Project.delay knob bounds — "delays >= 0 and < 300" (data-model.md Validation).
_DELAYS_OK = (
    "pending_settle_delay_s >= 0 AND pending_settle_delay_s < 300"
    " AND timeout_delay_s >= 0 AND timeout_delay_s < 300"
)

# State machine diagram, data-model.md. Only these edges may mutate `status`.
ALLOWED_TRANSITIONS: dict[TransactionStatus, frozenset[TransactionStatus]] = {
    TransactionStatus.initiated: frozenset(
        {
            TransactionStatus.pending,  # approve / pending_settle path
            TransactionStatus.declined,  # decline / verify_fail at verify
            TransactionStatus.failed,  # timeout outcome, unsupported op, invalid credentials
        }
    ),
    TransactionStatus.pending: frozenset(
        {
            TransactionStatus.settled,  # approve, or pending_settle once now >= due_at
            TransactionStatus.approved,  # refund scenario parks here before refunding
            TransactionStatus.expired,  # abandoned checkout / timeout window
        }
    ),
    TransactionStatus.approved: frozenset({TransactionStatus.refunded}),
}
# settled / refunded / expired / declined / failed are terminal — no outgoing edges.


class IllegalTransitionError(RuntimeError):
    """Raised when a caller tries to move a Transaction along an edge not in the diagram."""


def utcnow() -> datetime:
    """Timezone-aware UTC now (datetime.utcnow() is naive and deprecated)."""
    return datetime.now(timezone.utc)


class Project(Base):
    """Container for all simulation data; local self-host runs exactly one."""

    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("history_cap >= 1", name="ck_projects_history_cap_min"),
        CheckConstraint(_DELAYS_OK, name="ck_projects_delays_bounded"),
        CheckConstraint("webhook_retry_max >= 1", name="ck_projects_webhook_retry_max_min"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[ProjectKind] = mapped_column(
        default=ProjectKind.local, server_default=ProjectKind.local.value, nullable=False
    )
    default_scenario: Mapped[ScenarioOutcome] = mapped_column(
        default=ScenarioOutcome.approve,
        server_default=ScenarioOutcome.approve.value,
        nullable=False,
    )
    history_cap: Mapped[int] = mapped_column(
        Integer, default=1000, server_default=text("1000"), nullable=False
    )
    webhook_retry_max: Mapped[int] = mapped_column(
        Integer, default=3, server_default=text("3"), nullable=False
    )
    # Backoff schedule in seconds between webhook retries (T039 worker reads it).
    webhook_retry_backoff_s: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=lambda: [1, 2, 4], server_default=text("'{1,2,4}'")
    )
    pending_settle_delay_s: Mapped[int] = mapped_column(
        Integer, default=5, server_default=text("5"), nullable=False
    )
    timeout_delay_s: Mapped[int] = mapped_column(
        Integer, default=30, server_default=text("30"), nullable=False
    )
    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("now()"), nullable=False
    )


class AdapterConfig(Base):
    """Per-project emulated-gateway configuration (FR-002, FR-012)."""

    __tablename__ = "adapter_configs"
    __table_args__ = (
        # "one enabled row per (project, provider)"; disabled rows are unlimited so an operator
        # can keep alternatives parked.
        Index(
            "uq_adapter_configs_enabled_provider",
            "project_id",
            "provider",
            unique=True,
            postgresql_where=text("enabled"),
        ),
        CheckConstraint("api_unit IN ('rial', 'toman')", name="ck_adapter_configs_api_unit"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[Provider] = mapped_column(nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    # No `::jsonb` cast: Postgres coerces the literal anyway, and the cast would break the
    # SQLite DDL that unit tests depend on.
    credentials: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'")
    )
    api_unit: Mapped[ApiUnit] = mapped_column(
        default=ApiUnit.rial, server_default=ApiUnit.rial.value, nullable=False
    )
    endpoint_path_prefix: Mapped[str] = mapped_column(Text, nullable=False)


class Transaction(Base):
    """One emulated payment attempt. `amount_rial` is the Rial canonical value."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount_rial >= 0", name="ck_transactions_amount_rial_min"),
        UniqueConstraint("project_id", "authority", name="uq_transactions_project_authority"),
        # newest-first list + history-cap deletion
        Index("ix_transactions_project_created_at", "project_id", text("created_at DESC")),
        # scheduler sweep for `now >= due_at` (research R5)
        Index("ix_transactions_status_due_at", "status", "due_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    adapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("adapter_configs.id", ondelete="RESTRICT"), nullable=False
    )
    amount_rial: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), default="IRR", server_default=text("'IRR'"), nullable=False
    )
    status: Mapped[TransactionStatus] = mapped_column(
        default=TransactionStatus.initiated,
        server_default=TransactionStatus.initiated.value,
        nullable=False,
    )
    forced_scenario: Mapped[ScenarioOutcome | None] = mapped_column(nullable=True)
    effective_scenario: Mapped[ScenarioOutcome] = mapped_column(
        default=ScenarioOutcome.approve,
        server_default=ScenarioOutcome.approve.value,
        nullable=False,
    )
    authority: Mapped[str | None] = mapped_column(Text, nullable=True)
    app_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    callback_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    return_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_request: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=text("now()"),
        nullable=False,
    )

    def transition_to(self, new_status: TransactionStatus) -> None:
        """Move to `new_status` along the state machine, or raise.

        The single guard every status write routes through: an edge absent from
        `ALLOWED_TRANSITIONS` raises instead of silently mutating (data-model.md Validation).
        Re-saving the current status is a no-op, so idempotent callers stay safe.
        """
        if new_status == self.status:
            return
        # `status` is None on a never-flushed row, but the DB default comes back as a member on
        # load — so getting here with None means the caller skipped a flush, not a legal edge.
        if self.status is None or new_status not in ALLOWED_TRANSITIONS.get(
            self.status, frozenset()
        ):
            raise IllegalTransitionError(
                f"illegal transaction transition {getattr(self.status, 'value', None)!r}"
                f" -> {new_status.value!r}"
            )
        self.status = new_status


class UsageMeter(Base):
    """Counters only — no billing fields, no invoices (FR-011). One row per project."""

    __tablename__ = "usage_meters"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    requests_total: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0"), nullable=False
    )
    transactions_total: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0"), nullable=False
    )
    history_retained: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    webhook_attempts: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=text("now()"),
        nullable=False,
    )
