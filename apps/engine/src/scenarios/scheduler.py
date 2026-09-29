"""DB-backed due-time sweep (T031) — research R5, data-model.md index `(status, due_at)`.

`due_at` lives in Postgres, so a restart mid-delay loses nothing: the row is still pending and
still due. The sweep is the crash-recovery net, not the primary settle path (verify settles
`pending_settle` synchronously; this catches the process that died before it got there).
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.adapters.base import STAGE_SETTLE
from src.models import ScenarioOutcome, Transaction, TransactionStatus, utcnow
from src.webhooks.worker import schedule_delivery

logger = logging.getLogger(__name__)

SWEEP_INTERVAL_S = 1.0
# ponytail: one sweep at a time per process; a claim column if a second engine ever runs.
BATCH = 100


async def sweep_once(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> int:
    """Settle due `pending_settle` rows. Returns the number transitioned."""
    rows = (
        await session.scalars(
            select(Transaction)
            .where(
                Transaction.status == TransactionStatus.pending,
                Transaction.due_at.is_not(None),
                Transaction.due_at <= utcnow(),
            )
            .limit(BATCH)
        )
    ).all()
    count = 0
    settled_txs: list[Transaction] = []
    for tx in rows:
        if tx.effective_scenario is not ScenarioOutcome.pending_settle:
            continue
        tx.transition_to(TransactionStatus.settled)
        settled_txs.append(tx)
        count += 1
    if count > 0:
        await session.commit()
        if session_factory is not None:
            for tx in settled_txs:
                schedule_delivery(session_factory, tx.project_id, tx.id, STAGE_SETTLE)
    return count


async def run(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Sweep loop. Cancel cleanly — lifespan shutdown awaits this."""
    while True:
        try:
            async with session_factory() as session:
                await sweep_once(session, session_factory=session_factory)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("scheduler sweep failed")
        await asyncio.sleep(SWEEP_INTERVAL_S)
