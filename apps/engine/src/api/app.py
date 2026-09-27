"""FastAPI app (T011) — contracts/control-api.md.

Importing this module must not touch the network or a database: the engine is built in the
lifespan, and tests replace `app.state.session_factory` with an in-memory one.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.errors import install_error_handlers
from src.api.routes import router
from src.config import Settings
from src.models import Project


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the engine and seed the default project, so a fresh compose stack answers reads."""
    settings = Settings.from_env()
    # Tests inject their own factory before entering the client; only build an engine if nobody
    # did, and only dispose what this function created.
    owned_engine = None
    if getattr(app.state, "session_factory", None) is None:
        owned_engine = create_async_engine(settings.database_url)
        app.state.session_factory = async_sessionmaker(owned_engine, expire_on_commit=False)

    async with app.state.session_factory() as session:
        await _seed_default_project(session, settings)

    yield
    if owned_engine is not None:
        await owned_engine.dispose()


async def _seed_default_project(session: AsyncSession, settings: Settings) -> None:
    """Local self-host runs exactly one project; `GET /project` must answer on a bare stack (T016).

    ponytail: seed only — adapters are seeded by the Phase 3 adapter dispatch. The schema itself
    is alembic's job (`alembic upgrade head`), not this function's.
    """
    if await session.scalar(select(Project).limit(1)) is not None:
        return
    session.add(
        Project(
            name="default",
            history_cap=settings.history_cap,
            webhook_retry_max=settings.webhook_retry_max,
            pending_settle_delay_s=settings.pending_settle_delay_s,
            timeout_delay_s=settings.timeout_delay_s,
        )
    )
    await session.commit()


def create_app() -> FastAPI:
    app = FastAPI(title="IPG Sandbox Engine", version="0.1.0", lifespan=lifespan)
    install_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
