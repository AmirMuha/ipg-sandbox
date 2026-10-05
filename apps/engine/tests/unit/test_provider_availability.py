"""Platform-project lookup and the shared availability read path (T007).

This file is the stop-gate for research.md D1. Everything in 006-admin-ipg-visibility rests on
"the platform project is the row with `user_id IS NULL`". If that stops holding, the fallback is
a `GatewayState` table and a migration — so these tests assert the assumption directly rather
than trusting it.

Sync tests wrapping `asyncio.run`, matching the convention in `tests/unit/test_transactions.py`
(pytest-asyncio here is not in auto mode).
"""

import asyncio
import uuid

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.adapters.registry import seed_configs
from src.models import AdapterConfig, Base, Project, Provider
from src.services.provider_availability import (
    get_offered_providers,
    is_offered,
    platform_adapter,
    platform_project,
)


def _seed(db_file, *, with_platform=True, user_projects=0):
    """Build a database and return an async session factory over it."""
    sync_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sync_engine)
    with Session(sync_engine) as s:
        if with_platform:
            platform = Project(id=uuid.uuid4(), name="default")
            s.add(platform)
            s.flush()
            s.add_all(
                [
                    AdapterConfig(
                        id=uuid.uuid4(),
                        **{**kw, "enabled": kw["provider"] is Provider.zarinpal},
                    )
                    for kw in seed_configs(platform.id)
                ]
            )
        for i in range(user_projects):
            p = Project(id=uuid.uuid4(), name=f"user-{i}", user_id=uuid.uuid4())
            s.add(p)
            s.flush()
            s.add_all(
                [
                    AdapterConfig(id=uuid.uuid4(), **{**kw, "enabled": True})
                    for kw in seed_configs(p.id)
                ]
            )
        s.commit()
    sync_engine.dispose()

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    return async_sessionmaker(engine, expire_on_commit=False), engine


def test_exactly_one_platform_project_among_user_projects(tmp_path):
    """D1: `user_id IS NULL` picks the platform row and never a merchant's project."""

    async def _test():
        factory, engine = _seed(tmp_path / "d1.db", user_projects=3)
        async with factory() as session:
            found = await platform_project(session)
            assert found is not None
            assert found.name == "default"
            assert found.user_id is None
        await engine.dispose()

    asyncio.run(_test())


def test_no_platform_project_degrades_to_empty_not_an_error(tmp_path):
    """FR-023: absence of a platform row is a real state, handled by the caller."""

    async def _test():
        factory, engine = _seed(tmp_path / "none.db", with_platform=False, user_projects=2)
        async with factory() as session:
            assert await platform_project(session) is None
            assert await get_offered_providers(session) == set()
            assert await is_offered(session, Provider.zarinpal) is False
            assert await platform_adapter(session, Provider.zarinpal) is None
        await engine.dispose()

    asyncio.run(_test())


def test_offered_set_reads_the_platform_rows(tmp_path):
    """Only Zarinpal is seeded enabled, matching migration 0009."""

    async def _test():
        factory, engine = _seed(tmp_path / "offered.db", user_projects=1)
        async with factory() as session:
            assert await get_offered_providers(session) == {Provider.zarinpal}
            assert await is_offered(session, Provider.zarinpal) is True
            assert await is_offered(session, Provider.idpay) is False
        await engine.dispose()

    asyncio.run(_test())


def test_platform_adapter_finds_disabled_rows_too(tmp_path):
    """The admin write target must resolve a withdrawn gateway, not only an offered one."""

    async def _test():
        factory, engine = _seed(tmp_path / "target.db")
        async with factory() as session:
            row = await platform_adapter(session, Provider.idpay)
            assert row is not None
            assert row.enabled is False
        await engine.dispose()

    asyncio.run(_test())
