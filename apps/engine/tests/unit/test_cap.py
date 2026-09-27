"""T014 guard: cap + meter move together, and `history_retained` is the min-rule from FR-011.

Async (`asyncio.run`) rather than pytest-asyncio: `record_transaction` is one coroutine, and
adding an async-test plugin configuration for a single file is not worth the fixtures.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.models import AdapterConfig, Base, Project, Provider, Transaction, UsageMeter
from src.services.cap import record_transaction

_BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _sync_schema(url: str) -> None:
    """Build the schema with a sync engine — the async engine cannot CREATE TABLE these types."""
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()


def _make_project(session: Session, history_cap: int) -> uuid.UUID:
    project = Project(id=uuid.uuid4(), name="default", history_cap=history_cap)
    session.add(project)
    session.commit()
    return project.id


def _make_adapter(session: Session, project_id: uuid.UUID) -> uuid.UUID:
    adapter = AdapterConfig(
        id=uuid.uuid4(),
        project_id=project_id,
        provider=Provider.zarinpal,
        endpoint_path_prefix="/zarinpal",
    )
    session.add(adapter)
    session.commit()
    return adapter.id


def _run(coro_factory):
    return asyncio.run(coro_factory())


async def _insert(
    url: str, project_id: uuid.UUID, adapter_id: uuid.UUID, count: int, start: int = 0
) -> UsageMeter:
    """Insert `count` transactions through the real cap path, oldest first."""
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            project = await session.get(Project, project_id)
            meter = None
            for i in range(start, start + count):
                tx = Transaction(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    adapter_id=adapter_id,
                    amount_rial=1_000,
                    authority=f"A-{i}",
                    created_at=_BASE_TIME + timedelta(minutes=i),
                )
                meter = await record_transaction(session, project, tx)
            await session.commit()
            return meter
    finally:
        await engine.dispose()


@pytest.fixture
def db(tmp_path):
    """A throwaway SQLite file plus the ids of a project/adapter pair to write against."""
    url = f"sqlite:///{tmp_path / 'cap.db'}"
    _sync_schema(url)
    with Session(create_engine(url)) as session:
        project_id = _make_project(session, history_cap=2)
        adapter_id = _make_adapter(session, project_id)
    return {
        "url": url,
        "async_url": f"sqlite+aiosqlite:///{tmp_path / 'cap.db'}",
        "project_id": project_id,
        "adapter_id": adapter_id,
    }


def _stored_names(url: str, project_id: uuid.UUID) -> list[str]:
    with Session(create_engine(url)) as session:
        rows = session.scalars(
            select(Transaction.authority)
            .where(Transaction.project_id == project_id)
            .order_by(Transaction.created_at)
        )
        return list(rows)


def _meter(url: str, project_id: uuid.UUID) -> UsageMeter:
    with Session(create_engine(url)) as session:
        return session.get(UsageMeter, project_id)


def test_cap_deletes_only_the_oldest_rows_beyond_the_cap(db):
    """history_cap=2, insert 3 -> the newest two survive, oldest is gone."""
    _run(lambda: _insert(db["async_url"], db["project_id"], db["adapter_id"], 3))

    assert _stored_names(db["url"], db["project_id"]) == ["A-1", "A-2"]


def test_transactions_total_keeps_counting_past_the_cap(db):
    """FR-006: the lifetime counter must not shrink when rows are deleted."""
    meter = _run(lambda: _insert(db["async_url"], db["project_id"], db["adapter_id"], 5))

    assert meter.transactions_total == 5
    assert meter.history_retained == 2  # min(5, 2)
    assert _stored_names(db["url"], db["project_id"]) == ["A-3", "A-4"]


def test_history_retained_is_min_of_total_and_cap_before_the_cap_bites(tmp_path):
    """Below the cap, retained == total — the min-rule has to hold on the way up too."""
    url = f"sqlite:///{tmp_path / 'under.db'}"
    _sync_schema(url)
    with Session(create_engine(url)) as session:
        project_id = _make_project(session, history_cap=10)
        adapter_id = _make_adapter(session, project_id)

    meter = _run(
        lambda: _insert(f"sqlite+aiosqlite:///{tmp_path / 'under.db'}", project_id, adapter_id, 3)
    )

    assert meter.transactions_total == 3
    assert meter.history_retained == 3


def test_meter_row_is_created_on_first_insert(db):
    """No pre-seeded meter: the first insert must create it, not raise."""
    meter = _run(lambda: _insert(db["async_url"], db["project_id"], db["adapter_id"], 1))

    assert meter is not None
    assert meter.requests_total == 1
    assert meter.transactions_total == 1


def test_cap_and_meter_share_one_transaction(db):
    """A rollback after `record_transaction` must undo the insert, the delete, and the meter."""

    async def _insert_then_rollback():
        engine = create_async_engine(db["async_url"])
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory() as session:
                project = await session.get(Project, db["project_id"])
                tx = Transaction(
                    id=uuid.uuid4(),
                    project_id=db["project_id"],
                    adapter_id=db["adapter_id"],
                    amount_rial=1_000,
                    authority="ROLLBACK-ME",
                )
                await record_transaction(session, project, tx)
                await session.rollback()
        finally:
            await engine.dispose()

    _run(_insert_then_rollback)

    assert _stored_names(db["url"], db["project_id"]) == []
    assert _meter(db["url"], db["project_id"]) is None


def test_mismatched_project_id_is_rejected(db):
    """Cheap guard: writing a transaction under the wrong project would corrupt the cap count."""

    async def _wrong_project():
        engine = create_async_engine(db["async_url"])
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory() as session:
                project = await session.get(Project, db["project_id"])
                tx = Transaction(
                    id=uuid.uuid4(),
                    project_id=db["project_id"],
                    adapter_id=db["adapter_id"],
                    amount_rial=1_000,
                )
                tx.project_id = uuid.uuid4()  # detach from the project under test
                await record_transaction(session, project, tx)
        finally:
            await engine.dispose()

    with pytest.raises(ValueError):
        _run(_wrong_project)
