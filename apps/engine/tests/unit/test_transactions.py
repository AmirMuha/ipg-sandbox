"""Unit tests for transaction service (T025)."""

import asyncio
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.errors import ApiError, ErrorCode
from src.models import (
    AdapterConfig,
    Base,
    IllegalTransitionError,
    Project,
    Provider,
    ScenarioOutcome,
    TransactionStatus,
    UsageMeter,
)
from src.services.transactions import advance, initiate, load_by_authority


def _sync_schema(url: str) -> None:
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    db_file = tmp_path / "test_tx.db"
    sync_url = f"sqlite:///{db_file}"
    _sync_schema(sync_url)
    return f"sqlite+aiosqlite:///{db_file}"


def test_initiate_negative_amount_raises(db_url: str):
    async def _test():
        engine = create_async_engine(db_url)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            project = Project(id=uuid.uuid4(), name="default", history_cap=10)
            adapter = AdapterConfig(
                id=uuid.uuid4(),
                project_id=project.id,
                provider=Provider.zarinpal,
                endpoint_path_prefix="/zarinpal",
            )
            session.add_all([project, adapter])
            await session.commit()

            with pytest.raises(ApiError) as exc_info:
                await initiate(
                    session,
                    project,
                    adapter,
                    amount_rial=-100,
                    authority="A-1",
                )
            assert exc_info.value.code == ErrorCode.validation_error
            assert exc_info.value.status == 422
        await engine.dispose()

    asyncio.run(_test())


def test_initiate_success_and_scenario_resolution(db_url: str):
    async def _test():
        engine = create_async_engine(db_url)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            project = Project(
                id=uuid.uuid4(),
                name="default",
                history_cap=10,
                default_scenario=ScenarioOutcome.approve,
            )
            adapter = AdapterConfig(
                id=uuid.uuid4(),
                project_id=project.id,
                provider=Provider.zarinpal,
                endpoint_path_prefix="/zarinpal",
            )
            session.add_all([project, adapter])
            await session.commit()

            # 1. Initiated with header override
            tx1 = await initiate(
                session,
                project,
                adapter,
                amount_rial=1000,
                authority="A-1",
                header="decline",
            )
            assert tx1.effective_scenario == ScenarioOutcome.decline
            assert tx1.status == TransactionStatus.initiated

            # 2. Check meters bumped
            meter = await session.get(UsageMeter, project.id)
            assert meter is not None
            assert meter.transactions_total == 1
            assert meter.history_retained == 1

            # 3. Load by authority
            loaded = await load_by_authority(session, project, "A-1")
            assert loaded.id == tx1.id

            # 4. Advance status
            await advance(session, tx1, TransactionStatus.pending)
            assert tx1.status == TransactionStatus.pending

            # 5. Illegal transition raises
            with pytest.raises(IllegalTransitionError):
                await advance(session, tx1, TransactionStatus.initiated)

        await engine.dispose()

    asyncio.run(_test())
