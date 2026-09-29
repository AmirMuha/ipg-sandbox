"""Shared outcome logic (T030) — spec US2 acceptance 1-4, data-model.md state machine.

Every forced outcome resolves to a status transition and, for `pending_settle`, a due-time.
Adapters keep their own wire shapes; this module owns only the state-machine decision, so the
three gateways cannot drift apart on what a scenario means.
"""

import asyncio
from datetime import timedelta, timezone

from src.models import Project, ScenarioOutcome, Transaction, TransactionStatus, utcnow

_NON_PENDING_AT_CHECKOUT = frozenset(
    {ScenarioOutcome.decline, ScenarioOutcome.verify_fail, ScenarioOutcome.timeout}
)


def checkout_confirm_status(tx: Transaction) -> TransactionStatus | None:
    """Status for the checkout confirm button. `None` leaves the row alone.

    `verify_fail` and `decline` confirm successfully at the HTTP boundary but stay `initiated`,
    so verify can take the legal `initiated -> declined` edge. A confirmed row in `pending`
    could only reach `settled`, `approved`, or `expired`.
    """
    if tx.effective_scenario in _NON_PENDING_AT_CHECKOUT:
        return None
    return TransactionStatus.pending


def set_due_at(tx: Transaction, project: Project) -> None:
    """Anchor `pending_settle`'s settle to checkout (adapter-surfaces.md global rules)."""
    tx.due_at = utcnow() + timedelta(seconds=project.pending_settle_delay_s)


async def apply_initiate_outcome(tx: Transaction, project: Project) -> ScenarioOutcome | None:
    """Spec US2.2: timeout fires at initiate. Sleep bounded, then mark the row failed."""
    if tx.effective_scenario is not ScenarioOutcome.timeout:
        return None

    if project.timeout_delay_s > 0:
        await asyncio.sleep(project.timeout_delay_s)
    tx.transition_to(TransactionStatus.failed)
    return ScenarioOutcome.timeout


async def apply_verify_outcome(tx: Transaction) -> None:
    """Apply the verify-stage transition for `tx.effective_scenario`.

    `pending_settle` blocks for whatever is left of its due-time and settles synchronously, so
    the app gets a final answer the way a real gateway's verify does. The scheduler sweep is the
    crash-recovery net for a process that died mid-sleep, not the primary path.
    """
    if tx.status in (
        TransactionStatus.settled,
        TransactionStatus.declined,
        TransactionStatus.failed,
        TransactionStatus.refunded,
        TransactionStatus.expired,
    ):
        return
    if tx.effective_scenario in (ScenarioOutcome.decline, ScenarioOutcome.verify_fail):
        tx.transition_to(TransactionStatus.declined)
        return
    if tx.effective_scenario is ScenarioOutcome.timeout:
        if tx.status is TransactionStatus.pending:
            tx.transition_to(TransactionStatus.expired)
        else:
            tx.transition_to(TransactionStatus.failed)
        return
    if tx.effective_scenario is ScenarioOutcome.refund:
        tx.transition_to(TransactionStatus.approved)
        return
    if tx.effective_scenario is ScenarioOutcome.pending_settle and tx.due_at is not None:
        due = tx.due_at if tx.due_at.tzinfo is not None else tx.due_at.replace(tzinfo=timezone.utc)
        remaining = (due - utcnow()).total_seconds()
        if remaining > 0:
            await asyncio.sleep(remaining)
    tx.transition_to(TransactionStatus.settled)
