"""Administrator control over platform-wide gateway availability (006-admin-ipg-visibility).

Deliberately its own module rather than another route on the merchant `router` in
`routes/__init__.py`. The two surfaces have different authorisation (this one needs
`require_admin`), different scoping (the platform project, not the caller's), and different
audiences. Keeping them apart means a missing auth guard on one cannot be masked by a guard
added to the other — which is the failure mode this feature exists to prevent.

`GET /api/v1/providers` is intentionally unauthenticated (research.md D5): it backs a public
marketing page and returns gateway ids only — no credentials, no project data, no merchant data.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode, not_found
from src.api.scoping import require_admin
from src.models import AdapterConfig, Provider, User
from src.services.provider_availability import (
    get_offered_providers,
    platform_adapter,
    platform_project,
)

router = APIRouter(prefix="/api/v1")


def _availability_body(providers: list[str]) -> dict[str, Any]:
    return {"providers": providers, "count": len(providers)}


@router.get("/providers")
async def list_offered_providers(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Which gateways are offered right now. Public, and never cached (FR-022)."""
    offered = await get_offered_providers(session)
    return _availability_body(sorted(p.value for p in offered))


@router.patch("/admin/providers/{provider}")
async def set_provider_availability(
    request: Request,
    provider: str,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Offer or withdraw a gateway for every merchant (FR-001, FR-009, FR-010).

    Writes the **platform** project's row. The admin's own project, if they have one, is not
    consulted and not modified — availability is one global fact with one writer.
    """
    body = await request.json()
    unknown = set(body) - {"enabled"}
    if unknown:
        raise ApiError(
            ErrorCode.validation_error,
            f"unknown field(s): {sorted(unknown)}",
            status=422,
            details={"allowed": ["enabled"]},
        )

    enabled = body.get("enabled")
    if not isinstance(enabled, bool):
        raise ApiError(ErrorCode.validation_error, "enabled must be a boolean", status=422)

    try:
        prov = Provider(provider)
    except ValueError:
        raise not_found(f"provider {provider}") from None

    adapter = await platform_adapter(session, prov)
    if adapter is None:
        raise not_found(f"provider {prov.value}")

    if not enabled and adapter.enabled:
        # FR-010: at least one gateway must stay offered, or the platform cannot take a payment
        # at all. Counted from the platform project only — the caller's project is irrelevant.
        platform = await platform_project(session)
        active = (
            await session.scalar(
                select(func.count())
                .select_from(AdapterConfig)
                .where(
                    AdapterConfig.project_id == platform.id,
                    AdapterConfig.enabled.is_(True),
                    AdapterConfig.id != adapter.id,
                )
            )
            or 0
        )
        if active == 0:
            raise ApiError(
                ErrorCode.validation_error,
                "At least one payment gateway must remain available.",
                status=422,
                details={"last_offered": prov.value},
            )

    adapter.enabled = enabled
    await session.commit()

    offered = await get_offered_providers(session)
    return _availability_body(sorted(p.value for p in offered))
