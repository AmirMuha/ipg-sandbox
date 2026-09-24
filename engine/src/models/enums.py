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
    """The three v1 emulated gateways (FR-002)."""

    zarinpal = "zarinpal"
    idpay = "idpay"
    behpardakht = "behpardakht"


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
