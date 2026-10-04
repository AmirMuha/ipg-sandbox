"""Enumerations — spec: specs/001-mvp/data-model.md (T008).

`enum.StrEnum` (stdlib, 3.12+) so members serialize straight to the wire values the
adapters and control API speak, and store as Postgres native enum labels.
"""

import enum


class ProjectKind(enum.StrEnum):
    """Project.kind"""

    local = "local"
    demo = "demo"


class ScenarioOutcome(enum.StrEnum):
    """Shared by Project.default_scenario, Transaction.forced_scenario/effective_scenario."""

    approve = "approve"
    decline = "decline"
    timeout = "timeout"
    refund = "refund"
    pending_settle = "pending_settle"
    verify_fail = "verify_fail"


class Provider(enum.StrEnum):
    """Every emulated gateway (FR-002).

    Declaration order MUST match the label order in
    `alembic/versions/0006_provider_labels.py` — the two are read together when a human has to
    reason about the Postgres enum.
    """

    # v1 gateways (Phase 3 of 001-mvp)
    zarinpal = "zarinpal"
    idpay = "idpay"
    behpardakht = "behpardakht"

    # Top-tier banking PSPs (003 US1)
    saman = "saman"
    sadad = "sadad"
    parsian = "parsian"
    pasargad = "pasargad"
    asan_pardakht = "asan_pardakht"

    # Specialized / institutional PSPs (003 US2)
    pardakht_novin = "pardakht_novin"
    irankish = "irankish"
    fanava = "fanava"
    sarmayeh = "sarmayeh"

    # Payment facilitators (003 US3)
    sizpay = "sizpay"


class ApiUnit(enum.StrEnum):
    """Unit the emulated API expects; engine stores Rial canonical (clarification 4)."""

    rial = "rial"
    toman = "toman"


class TransactionStatus(enum.StrEnum):
    """State machine states — transitions enforced by `Transaction.transition_to`."""

    initiated = "initiated"
    pending = "pending"
    settled = "settled"
    approved = "approved"
    refunded = "refunded"
    expired = "expired"
    declined = "declined"
    failed = "failed"
