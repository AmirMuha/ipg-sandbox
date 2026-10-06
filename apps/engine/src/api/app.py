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

from src.adapters.asan_pardakht import router as asan_pardakht_router
from src.adapters.behpardakht import router as behpardakht_router
from src.adapters.fanava import router as fanava_router
from src.adapters.idpay import router as idpay_router
from src.adapters.irankish import router as irankish_router
from src.adapters.pardakht_novin import router as pardakht_novin_router
from src.adapters.parsian import router as parsian_router
from src.adapters.pasargad import router as pasargad_router
from src.adapters.registry import seed_configs
from src.adapters.sadad import router as sadad_router
from src.adapters.saman import router as saman_router
from src.adapters.sarmayeh import router as sarmayeh_router
from src.adapters.sizpay import router as sizpay_router
from src.adapters.zarinpal import router as zarinpal_router
from src.api.admin_providers import router as admin_providers_router
from src.api.admin_subscriptions import router as admin_subscriptions_router
from src.api.auth import router as auth_router
from src.api.billing import router as billing_router
from src.api.errors import install_error_handlers
from src.api.routes import router
from src.config import Settings
from src.models import AdapterConfig, Project, Provider
from src.scenarios.scheduler import run as run_scheduler
from src.services.billing import run_subscription_expiry


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
    expiry_task = asyncio.create_task(run_subscription_expiry(app.state.session_factory))
    try:
        yield
    finally:
        scheduler_task.cancel()
        expiry_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await scheduler_task
        with contextlib.suppress(asyncio.CancelledError):
            await expiry_task
        if owned_engine is not None:
            await owned_engine.dispose()


async def _seed_adapters(session: AsyncSession, project: Project) -> None:
    """Seed adapters for `project` from the registry for all implemented gateways."""
    existing = (
        await session.scalars(select(AdapterConfig).where(AdapterConfig.project_id == project.id))
    ).first()
    if existing is not None:
        return

    configs = [AdapterConfig(**kw) for kw in seed_configs(project.id)]
    session.add_all(configs)


async def _seed_default_project(session: AsyncSession, settings: Settings) -> None:
    """Local self-host runs one project; `GET /project` and `/adapters` answer on a bare stack."""
    project = await session.scalar(select(Project).limit(1))
    if project is None:
        is_local = os.environ.get("ENGINE_PROFILE", "local") == "local"
        project = Project(
            name="default",
            tier="developer",
            daily_requests_cap=0 if is_local else 100,
            max_active_adapters=0 if is_local else 2,
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
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(auth_router)
    app.include_router(admin_providers_router)
    app.include_router(admin_subscriptions_router)
    app.include_router(billing_router)
    app.include_router(router)
    app.include_router(zarinpal_router)
    app.include_router(idpay_router)
    app.include_router(behpardakht_router)
    app.include_router(saman_router)
    app.include_router(sadad_router)
    app.include_router(parsian_router)
    app.include_router(pasargad_router)
    app.include_router(asan_pardakht_router)
    app.include_router(pardakht_novin_router)
    app.include_router(irankish_router)
    app.include_router(fanava_router)
    app.include_router(sarmayeh_router)
    app.include_router(sizpay_router)
    return app


app = create_app()
