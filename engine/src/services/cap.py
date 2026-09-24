"""History-cap enforcement + UsageMeter bump (T014) — research R9, FR-006/FR-011.

One entry point, `record_transaction`, runs the whole thing in the caller's transaction: insert
the row, delete the rows past the cap, bump the meter, one `flush`. Callers commit; a failure
anywhere rolls all three back together, so a meter can never count a row that was not stored.

Cap semantics (FR-006): `transactions_total` is lifetime and never shrinks; `history_retained` is
`min(transactions_total, history_cap)`.
"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Project, Transaction, UsageMeter


async def record_transaction(
    session: AsyncSession, project: Project, tx: Transaction
) -> UsageMeter:
    """Persist `tx` for `project`, enforce the history cap, and bump the meter.

    Does not commit — the caller owns the transaction boundary (see module docstring). This is
    the seam T025 (transaction initiation) calls on insert.
    """
    if tx.project_id != project.id:
        raise ValueError(f"transaction belongs to {tx.project_id}, not project {project.id}")

    session.add(tx)
    await session.flush()  # INSERT first, so the cap counts the new row

    # Newest-first, skip the cap worth of survivors, and everything left is past the cap. OFFSET
    # rather than a keyset cut because `created_at` ties are real for rows written in one burst,
    # and this matches the documented "delete oldest rows beyond history_cap" wording.
    # ponytail: O(offset) per insert; swap for a keyset cut on (created_at, id) if a project ever
    # runs a big cap under heavy insert load.
    doomed = (
        select(Transaction.id)
        .where(Transaction.project_id == project.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset(project.history_cap)
    )
    await session.execute(delete(Transaction).where(Transaction.id.in_(doomed)))

    meter = await session.get(UsageMeter, project.id, with_for_update=True)
    if meter is None:
        meter = UsageMeter(
            project_id=project.id, requests_total=0, transactions_total=0, history_retained=0
        )
        session.add(meter)

    # The row lock above is what keeps this read-modify-write atomic against a concurrent insert
    # for the same project. SQLite ignores FOR UPDATE, but it serialises writers anyway.
    meter.requests_total += 1
    meter.transactions_total += 1
    meter.history_retained = min(meter.transactions_total, project.history_cap)

    await session.flush()
    return meter
