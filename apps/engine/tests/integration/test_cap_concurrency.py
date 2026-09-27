"""T014 regression: the history cap must hold under CONCURRENT inserts (FR-006).

Why this is not in `tests/unit/`: the bug it guards is a Postgres concurrency defect.
`cap.py` previously flushed the INSERT and ran its `DELETE ... OFFSET history_cap` *before*
taking any row lock, so N concurrent transactions each measured the window against a snapshot
that could not see the others' uncommitted rows. `OFFSET cap` then found nothing to delete and
no row was ever removed — while the meter still reported the capped value.

SQLite cannot reproduce that (it ignores `FOR UPDATE` and serialises writers anyway), so on
SQLite this test would pass against the broken code. It is therefore gated on a real Postgres
via `TEST_DATABASE_URL` and **skips** otherwise, rather than reporting a vacuous success.

Run it with, e.g.:
    TEST_DATABASE_URL=postgresql+asyncpg://postgres:sandbox@localhost:5432/ipg \
      .venv/bin/python -m pytest tests/integration/test_cap_concurrency.py -v
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.models import AdapterConfig, Base, Project, Provider, Transaction, UsageMeter
from src.services.cap import record_transaction

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="needs a real Postgres: SQLite serialises writers, so the bug cannot reproduce there",
)

CAP = 2
INSERTS = 6


async def _seed(session_factory) -> tuple[uuid.UUID, uuid.UUID]:
    async with session_factory() as session:
        project = Project(id=uuid.uuid4(), name="cap-concurrency", history_cap=CAP)
        session.add(project)
        await session.flush()
        adapter = AdapterConfig(
            id=uuid.uuid4(),
            project_id=project.id,
            provider=Provider.zarinpal,
            endpoint_path_prefix="/zarinpal",
        )
        session.add(adapter)
        await session.commit()
        return project.id, adapter.id


async def _insert(session_factory, project_id, adapter_id, index: int, prefix: str) -> None:
    async with session_factory() as session:
        project = await session.get(Project, project_id)
        tx = Transaction(
            id=uuid.uuid4(),
            project_id=project_id,
            adapter_id=adapter_id,
            amount_rial=1_000 + index,
            authority=f"{prefix}-{index}",
        )
        await record_transaction(session, project, tx)
        await session.commit()


async def _kept(session_factory, project_id) -> tuple[list[str], UsageMeter | None]:
    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(Transaction.authority).where(Transaction.project_id == project_id)
                )
            )
            .scalars()
            .all()
        )
        return list(rows), await session.get(UsageMeter, project_id)


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        # Drop first: these tests pin explicit ids, so residue from a previous run would collide
        # on the primary key. Per-test isolation also keeps the cap assertions exact.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_sequential_inserts_hold_the_cap(session_factory):
    """Control: the pre-fix code already passed this, so it proves the harness itself works."""
    project_id, adapter_id = await _seed(session_factory)

    for i in range(INSERTS):
        await _insert(session_factory, project_id, adapter_id, i, "SEQ")

    kept, meter = await _kept(session_factory, project_id)
    assert len(kept) == CAP
    assert meter.transactions_total == INSERTS
    assert meter.history_retained == CAP


@pytest.mark.asyncio
async def test_concurrent_inserts_hold_the_cap(session_factory):
    """The regression: pre-fix this kept all 6 rows against a cap of 2."""
    project_id, adapter_id = await _seed(session_factory)

    await asyncio.gather(
        *[_insert(session_factory, project_id, adapter_id, i, "CON") for i in range(INSERTS)]
    )

    kept, meter = await _kept(session_factory, project_id)
    assert len(kept) == CAP, f"cap not enforced under concurrency: kept {sorted(kept)}"
    assert meter.transactions_total == INSERTS, "lifetime counter must still count every insert"
    assert meter.history_retained == CAP


@pytest.mark.asyncio
async def test_newest_inserts_survive_when_timestamps_tie(session_factory):
    """A transaction must never be deleted by the same call that inserted it.

    Regression: ranking the new row among the others let it fall past `OFFSET history_cap` when
    `created_at` tied, so it was deleted by its own call while the meter still counted it — the
    caller was handed a transaction that was already gone. Reproduced on real Postgres at 10/12
    inserts lost. Ties are real: `created_at` defaults to a microsecond clock, so a burst can
    share it, and `len(kept) == cap` alone cannot catch this (the count stays right either way).

    Deterministic, not probabilistic: verified against Postgres, `(created_at DESC, id DESC)`
    ranks the *largest* id first, so ids descend with insertion order to make the row just
    inserted rank last — i.e. the row most exposed to being deleted by its own call. With random
    UUIDs the new row's rank is a coin flip, which is how a vacuous version of this test can
    pass against the bug.
    """
    project_id, adapter_id = await _seed(session_factory)

    # One identical created_at for every row, so ranking falls through to `id DESC`.
    tied_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    for i in range(INSERTS):
        authority = f"TIE-{i}"
        # Descending ids: the newest row has the smallest id, so it ranks last under `id DESC`.
        tx_id = uuid.UUID(int=INSERTS - i)
        async with session_factory() as session:
            project = await session.get(Project, project_id)
            await record_transaction(
                session,
                project,
                Transaction(
                    id=tx_id,
                    project_id=project_id,
                    adapter_id=adapter_id,
                    amount_rial=1_000 + i,
                    authority=authority,
                    created_at=tied_at,
                ),
            )
            await session.commit()

        # The invariant, checked the moment the caller would get the row back.
        async with session_factory() as session:
            still_there = (
                await session.execute(
                    select(Transaction.authority).where(Transaction.authority == authority)
                )
            ).scalar_one_or_none()
        assert still_there == authority, (
            f"{authority} was deleted by its own record_transaction call"
        )

    async with session_factory() as session:
        kept = (
            (
                await session.execute(
                    select(Transaction.authority).where(Transaction.project_id == project_id)
                )
            )
            .scalars()
            .all()
        )
    assert len(kept) == CAP, f"expected exactly {CAP} rows, got {len(kept)}"
