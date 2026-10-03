"""FastAPI app (T011) — contracts/control-api.md.

Importing this module must not touch the network or a database: the engine is built in the
lifespan, and tests replace `app.state.session_factory` with an in-memory one.
"""

import asyncio
import contextlib
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.adapters.behpardakht import router as behpardakht_router
from src.adapters.idpay import router as idpay_router
from src.adapters.zarinpal import router as zarinpal_router
from src.api.errors import install_error_handlers
from src.api.routes import router
from src.config import Settings
from src.models import AdapterConfig, ApiUnit, Project, Provider
from src.scenarios.scheduler import run as run_scheduler


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

    scheduler_task = asyncio.create_task(run_scheduler(app.state.session_factory))
    try:
        yield
    finally:
        scheduler_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await scheduler_task
        if owned_engine is not None:
            await owned_engine.dispose()


async def _seed_adapters(session: AsyncSession, project: Project) -> None:
    """Give `project` the three sandbox adapters if it has none.

    Called for *every* project, not just the first: in the demo profile each visitor gets their
    own project, and a project with no AdapterConfig answers every initiate with
    `404 adapter zarinpal not found` — the demo flow could not create a payment at all.
    """
    existing = (
        await session.scalars(select(AdapterConfig).where(AdapterConfig.project_id == project.id))
    ).first()
    if existing is not None:
        return

    session.add_all(
        [
            AdapterConfig(
                project_id=project.id,
                provider=Provider.zarinpal,
                endpoint_path_prefix="/zarinpal",
                api_unit=ApiUnit.rial,
                credentials={"merchant_id": "sandbox-merchant"},
            ),
            AdapterConfig(
                project_id=project.id,
                provider=Provider.idpay,
                endpoint_path_prefix="/idpay",
                api_unit=ApiUnit.toman,
                credentials={"api_key": "sandbox-key"},
            ),
            AdapterConfig(
                project_id=project.id,
                provider=Provider.behpardakht,
                endpoint_path_prefix="/behpardakht",
                api_unit=ApiUnit.rial,
                credentials={
                    "terminal_id": 123456,
                    "username": "sandbox",
                    "password": "sandbox",
                },
            ),
        ]
    )


async def _seed_default_project(session: AsyncSession, settings: Settings) -> None:
    """Local self-host runs one project; `GET /project` and `/adapters` answer on a bare stack."""
    project = await session.scalar(select(Project).limit(1))
    if project is None:
        project = Project(
            name="default",
            history_cap=settings.history_cap,
            webhook_retry_max=settings.webhook_retry_max,
            pending_settle_delay_s=settings.pending_settle_delay_s,
            timeout_delay_s=settings.timeout_delay_s,
        )
        session.add(project)
        await session.flush()

    await _seed_adapters(session, project)
    await session.commit()


def create_app() -> FastAPI:
    app = FastAPI(title="IPG Sandbox Engine", version="0.1.0", lifespan=lifespan)
    # FR-010: the dashboard's port is whatever `DASHBOARD_PORT` resolves to, and a developer
    # routinely runs it on 3001+ when 3000 is taken. The regex covers every loopback port on
    # both host spellings so a remap does not silently break the browser's preflights; the
    # explicit origins keep the container-internal hostname working for SSR.
    dashboard_port = os.environ.get("DASHBOARD_PORT", "").strip() or "3000"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{dashboard_port}",
            f"http://127.0.0.1:{dashboard_port}",
            "http://dashboard:3000",
        ],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(router)
    app.include_router(zarinpal_router)
    app.include_router(idpay_router)
    app.include_router(behpardakht_router)
    return app


app = create_app()
