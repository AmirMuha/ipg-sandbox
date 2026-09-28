"""Read-only control API (T015) — contracts/control-api.md.

Every handler is a `GET`; the pre-seed `POST /transactions` and the `PATCH`/`DELETE` routes are
T031/T032 (Phase 4). There is no service or repository layer: the queries are short enough that a
layer between them and the route would only be a second place to read the same five lines.

Response shapes are the ORM rows serialized by hand. That is deliberate — `response_model` would
need a parallel set of pydantic schemas mirroring `models.py`, and the one rule that actually
matters here (meters exposing *only* counters, FR-011) is easier to guard with an explicit list.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import not_found
from src.models import (
    AdapterConfig,
    Project,
    ProjectKind,
    UsageMeter,
)

router = APIRouter(prefix="/api/v1")

# FR-011: counters only — no billing fields, no invoices. This tuple *is* the contract; the
# unit test asserts the response key set equals it.
METER_FIELDS = ("requests_total", "transactions_total", "history_retained", "webhook_attempts")

MAX_PAGE_SIZE = 100


async def current_project(session: Annotated[AsyncSession, Depends(get_session)]) -> Project:
    """The project every read is scoped to (FR-014 isolation).

    Local self-host runs exactly one project (data-model.md), so this is the oldest row.
    ponytail: single-project scope; T052 (hosted demo) swaps this for the session-cookie lookup.
    """
    project = await session.scalar(
        select(Project).order_by(Project.created_at, Project.id).limit(1)
    )
    if project is None:
        raise not_found("project")
    return project


def _project_body(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "kind": project.kind,
        "default_scenario": project.default_scenario,
        "history_cap": project.history_cap,
        "webhook_retry_max": project.webhook_retry_max,
        "webhook_retry_backoff_s": list(project.webhook_retry_backoff_s),
        "pending_settle_delay_s": project.pending_settle_delay_s,
        "timeout_delay_s": project.timeout_delay_s,
        "created_at": project.created_at,
    }


def _adapter_body(adapter: AdapterConfig, *, kind: ProjectKind) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": adapter.id,
        "project_id": adapter.project_id,
        "provider": adapter.provider,
        "enabled": adapter.enabled,
        "api_unit": adapter.api_unit,
        "endpoint_path_prefix": adapter.endpoint_path_prefix,
    }
    # Local self-host: the operator entered these test values themselves, so reading them back is
    # part of configuring (and debugging) the stack. Demo: the project is visitor-scoped and the
    # route is reachable by that visitor, so the same read becomes a credential-display surface
    # (FR-014). Omit rather than mask — a mask leaks length and invites false confidence.
    if kind is ProjectKind.local:
        body["credentials"] = adapter.credentials
    return body


@router.get("/project")
async def get_project(
    project: Annotated[Project, Depends(current_project)],
) -> dict[str, Any]:
    return _project_body(project)


@router.get("/adapters")
async def list_adapters(
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict[str, Any]]:
    adapters = await session.scalars(
        select(AdapterConfig)
        .where(AdapterConfig.project_id == project.id)
        .order_by(AdapterConfig.provider)
    )
    return [_adapter_body(adapter, kind=project.kind) for adapter in adapters]


@router.get("/meters")
async def get_meters(
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, int]:
    """Counters only — FR-011. A project with no rows yet reports zeros."""
    meter = await session.get(UsageMeter, project.id)
    return {field: (getattr(meter, field, 0) or 0) if meter else 0 for field in METER_FIELDS}


from src.api.routes.transactions import router as transactions_router  # noqa: E402

router.include_router(transactions_router)
