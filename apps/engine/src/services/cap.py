"""History-cap enforcement + UsageMeter bump (T014) — research R9, FR-006/FR-011.

One entry point, `record_transaction`, runs the whole thing in the caller's transaction: insert
the row, delete the rows past the cap, bump the meter, one `flush`. Callers commit; a failure
anywhere rolls all three back together, so a meter can never count a row that was not stored.

Cap semantics (FR-006): `transactions_total` is lifetime and never shrinks; `history_retained` is
`min(transactions_total, history_cap)`.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.errors import ApiError, ErrorCode
from src.models import Project, Transaction, UsageMeter, utcnow


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def check_and_bump_quota(
    session: AsyncSession, project: Project
) -> UsageMeter:
    """Verify daily request quota and atomically increment request counters."""
    await session.execute(select(Project.id).where(Project.id == project.id).with_for_update())

    meter = await session.get(UsageMeter, project.id, with_for_update=True)
    if meter is None:
        meter = UsageMeter(
            project_id=project.id,
            requests_total=0,
            requests_today=0,
            transactions_total=0,
            history_retained=0,
            window_started_at=utcnow(),
        )
        session.add(meter)
        await session.flush()

    now = utcnow()
    window_start = _ensure_aware(meter.window_started_at)
    if (now - window_start).total_seconds() >= 86400:
        meter.requests_today = 0
        meter.window_started_at = now
        window_start = now

    if project.daily_requests_cap > 0 and meter.requests_today >= project.daily_requests_cap:
        seconds_left = max(1, int(86400 - (now - window_start).total_seconds()))
        reset_ts = int((window_start + timedelta(days=1)).timestamp())
        raise ApiError(
            ErrorCode.daily_quota_exceeded,
            f"Daily request quota of {project.daily_requests_cap} requests has been exhausted for this workspace.",
            status=429,
            details={
                "limit": project.daily_requests_cap,
                "current": meter.requests_today,
                "resets_in_seconds": seconds_left,
                "upgrade_url": "/pricing",
            },
            headers={
                "Retry-After": str(seconds_left),
                "X-RateLimit-Limit": str(project.daily_requests_cap),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_ts),
            },
        )

    meter.requests_today += 1
    meter.requests_total += 1
    await session.flush()
    return meter


async def record_transaction(
    session: AsyncSession, project: Project, tx: Transaction
) -> UsageMeter:
    """Persist `tx` for `project`, enforce the history cap, and bump the meter.

    Does not commit — the caller owns the transaction boundary (see module docstring). This is
    the seam T025 (transaction initiation) calls on insert.
    """
    if tx.project_id != project.id:
        raise ValueError(f"transaction belongs to {tx.project_id}, not project {project.id}")

    # Lock the project row FIRST. This lock is the serialisation point for the whole
    # function: without it, N concurrent inserts each run their DELETE against a snapshot
    # that cannot see the others' uncommitted rows, so `OFFSET history_cap` finds nothing
    # and no row is ever deleted — the cap silently goes unenforced while the meter still
    # reports the capped value. Verified against real Postgres (SQLite serialises writers,
    # so it cannot reproduce this).
    await session.execute(select(Project.id).where(Project.id == project.id).with_for_update())

    session.add(tx)
    await session.flush()  # INSERT first, so the cap counts the new row

    # Cap the OTHER rows to `cap - 1`, so the row just inserted always occupies the last slot.
    #
    # Two things this ordering must get right:
    #  - The new row is excluded from the ranking entirely. Ranking it among the others lets it
    #    fall past the offset when `created_at` ties and be deleted by its own call — handing the
    #    caller a transaction that is already gone (reproduced on real Postgres: 10/12 inserts
    #    lost this way when timestamps tied). Ties are real: `created_at` defaults to a Python
    #    microsecond clock, so rows written in one burst can share it.
    #  - Keeping `cap - 1` others (not `cap`) keeps the total at exactly `cap` even when ties make
    #    the new row's rank ambiguous, instead of drifting one row over per tie burst.
    # ponytail: O(offset) per insert; swap for a keyset cut on (created_at, id) if a project ever
    # runs a big cap under heavy insert load.
    doomed = (
        select(Transaction.id)
        .where(Transaction.project_id == project.id, Transaction.id != tx.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset(max(project.history_cap - 1, 0))
    )
    await session.execute(delete(Transaction).where(Transaction.id.in_(doomed)))

    meter = await session.get(UsageMeter, project.id, with_for_update=True)
    if meter is None:
        meter = UsageMeter(
            project_id=project.id,
            requests_total=0,
            requests_today=0,
            transactions_total=0,
            history_retained=0,
            window_started_at=utcnow(),
        )
        session.add(meter)

    now = utcnow()
    window_start = _ensure_aware(meter.window_started_at)
    if (now - window_start).total_seconds() >= 86400:
        meter.requests_today = 0
        meter.window_started_at = now
        window_start = now

    if project.daily_requests_cap > 0 and meter.requests_today >= project.daily_requests_cap:
        seconds_left = max(1, int(86400 - (now - window_start).total_seconds()))
        reset_ts = int((window_start + timedelta(days=1)).timestamp())
        raise ApiError(
            ErrorCode.daily_quota_exceeded,
            f"Daily request quota of {project.daily_requests_cap} requests has been exhausted for this workspace.",
            status=429,
            details={
                "limit": project.daily_requests_cap,
                "current": meter.requests_today,
                "resets_in_seconds": seconds_left,
                "upgrade_url": "/pricing",
            },
            headers={
                "Retry-After": str(seconds_left),
                "X-RateLimit-Limit": str(project.daily_requests_cap),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_ts),
            },
        )

    # The row lock above is what keeps this read-modify-write atomic against a concurrent insert
    # for the same project. SQLite ignores FOR UPDATE, but it serialises writers anyway.
    meter.requests_today += 1
    meter.requests_total += 1
    meter.transactions_total += 1
    meter.history_retained = min(meter.transactions_total, project.history_cap)

    await session.flush()
    return meter
