"""T058: full-scale history-cap validation (FR-006, quickstart §9).

The unit suite (`tests/unit/test_cap.py`) proves cap *semantics* at history_cap=2. This file
proves them at the shipped default of 1000, against the exact assertions quickstart §9 names:
`history_retained == history_cap`, `transactions_total` still counting, oldest dropped and
newest intact.

Async (`asyncio.run`) like `test_cap.py`, for the same reason: one coroutine, and a plugin
config for a single file is not worth the fixtures.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.models import AdapterConfig, Base, Project, Provider, Transaction
from src.services.cap import record_transaction

DEFAULT_CAP = 1000
_BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
# Cap + 25: enough to prove the meter keeps counting past the cap, few enough to stay quick.
OVERFLOW = 25


def _sync_schema(url: str) -> None:
    """Build the schema with a sync engine — the async engine cannot CREATE TABLE these types."""
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()


async def _insert_over_cap(async_url: str, project_id: uuid.UUID, adapter_id: uuid.UUID):
    """Insert DEFAULT_CAP + OVERFLOW transactions through the real cap path, oldest first.

    Distinct `created_at` per row: the cap ranks by `(created_at desc, id desc)`, and tied
    timestamps make the boundary row ambiguous, which is exactly what this test must not
    conflate with "oldest dropped / newest intact".
    """
    engine = create_async_engine(async_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            project = await session.get(Project, project_id)
            for i in range(DEFAULT_CAP + OVERFLOW):
                tx = Transaction(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    adapter_id=adapter_id,
                    amount_rial=1_000,
                    authority=f"A-{i}",
                    created_at=_BASE_TIME + timedelta(minutes=i),
                )
                await record_transaction(session, project, tx)
            await session.commit()
    finally:
        await engine.dispose()


@pytest.fixture
def db(tmp_path):
    """Throwaway SQLite file plus a project/adapter pair seeded at the shipped default cap."""
    url = f"sqlite:///{tmp_path / 'history_cap.db'}"
    _sync_schema(url)
    with Session(create_engine(url)) as session:
        project = Project(id=uuid.uuid4(), name="default", history_cap=DEFAULT_CAP)
        session.add(project)
        adapter = AdapterConfig(
            id=uuid.uuid4(),
            project_id=project.id,
            provider=Provider.zarinpal,
            endpoint_path_prefix="/zarinpal",
        )
        session.add(adapter)
        session.commit()
        project_id, adapter_id = project.id, adapter.id
    return {
        "url": url,
        "async_url": f"sqlite+aiosqlite:///{tmp_path / 'history_cap.db'}",
        "project_id": project_id,
        "adapter_id": adapter_id,
    }


def _authorities(url: str, project_id: uuid.UUID) -> list[str]:
    with Session(create_engine(url)) as session:
        return list(
            session.scalars(
                select(Transaction.authority)
                .where(Transaction.project_id == project_id)
                .order_by(Transaction.created_at)
            )
        )


def test_cap_drops_oldest_and_keeps_newest_at_the_shipped_default(db):
    """quickstart §9: oldest rows gone, newest intact, exactly `history_cap` rows survive."""
    asyncio.run(_insert_over_cap(db["async_url"], db["project_id"], db["adapter_id"]))

    kept = _authorities(db["url"], db["project_id"])

    assert len(kept) == DEFAULT_CAP
    # A-0..A-24 are the oldest 25 and must be gone; the tail must be intact and contiguous.
    assert kept[0] == f"A-{OVERFLOW}"
    assert kept[-1] == f"A-{DEFAULT_CAP + OVERFLOW - 1}"
    assert kept == [f"A-{i}" for i in range(OVERFLOW, DEFAULT_CAP + OVERFLOW)]


def test_meter_reports_capped_retained_and_lifetime_total(db):
    """FR-006: `history_retained` is capped; `transactions_total` is lifetime and never shrinks."""
    asyncio.run(_insert_over_cap(db["async_url"], db["project_id"], db["adapter_id"]))

    with Session(create_engine(db["url"])) as session:
        meter = session.execute(
            select(
                func.count().label("n"),
            ).select_from(Transaction)
        ).one()

    assert meter.n == DEFAULT_CAP

    from src.models import UsageMeter

    with Session(create_engine(db["url"])) as session:
        usage = session.get(UsageMeter, db["project_id"])

    assert usage.transactions_total == DEFAULT_CAP + OVERFLOW
    assert usage.history_retained == DEFAULT_CAP  # min(total, cap)


def test_row_count_matches_meter_after_overflow(db):
    """The meter must not claim a cap the table does not hold (they move in one transaction)."""
    asyncio.run(_insert_over_cap(db["async_url"], db["project_id"], db["adapter_id"]))

    from src.models import UsageMeter

    with Session(create_engine(db["url"])) as session:
        usage = session.get(UsageMeter, db["project_id"])
        stored = session.scalar(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.project_id == db["project_id"])
        )

    assert stored == usage.history_retained == DEFAULT_CAP
