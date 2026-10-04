"""Shared checkout action handler (FR-004, FR-008).

Every gateway's hosted page has three action buttons: `confirm`, `fail`, and `abandon`.
The state transitions are identical across all 13 gateways:
  - confirm:   advances to `pending` (or stays `initiated` for verify_fail/decline so verify can
               take the legal edge), schedules due_at for `pending_settle`.
  - fail:      advances to `declined`.
  - abandon:   advances to `pending` then `expired`.

Before this existed, the 40-line `checkout_action` handler was copy-pasted into every
`routes.py`. What *does* vary per gateway is the redirect query/body: Behpardakht sends
`ResCode=0/11/17` + `SaleReferenceId`, Zarinpal sends `Status=OK/NOK/CANCELLED`, Saman sends
`State=OK` + `RefNum`. This module executes the shared state change and returns the chosen
action string, so each route builds its own wire return.
"""

from typing import Literal
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Project,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
)
from src.scenarios.outcomes import (
    checkout_confirm_status,
    set_due_at,
)
from src.services import transactions

CheckoutAction = Literal["confirm", "fail", "abandon"]


async def apply_checkout_action(
    session: AsyncSession,
    tx: Transaction,
    project: Project,
    action: str,
) -> CheckoutAction:
    """Advance `tx` per `action`. Returns the normalized action name."""
    if action == "confirm":
        if (target := checkout_confirm_status(tx)) is not None:
            if tx.effective_scenario is ScenarioOutcome.pending_settle:
                set_due_at(tx, project)
            await transactions.advance(session, tx, target)
        return "confirm"
    if action == "fail":
        await transactions.advance(session, tx, TransactionStatus.declined)
        return "fail"
    # abandon
    await transactions.advance(session, tx, TransactionStatus.pending)
    await transactions.advance(session, tx, TransactionStatus.expired)
    return "abandon"


def append_query(base_url: str, params: dict) -> str:
    """Append query string to `base_url`, picking `?` or `&` correctly."""
    qs = urlencode(params)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{qs}"
