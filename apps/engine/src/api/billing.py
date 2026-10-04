"""Billing API routes: plan upgrade initiation and settlement callback (004-launch-readiness-flows)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode
from src.api.scoping import get_current_project, get_current_user
from src.config import Settings, public_base_url
from src.models import (
    Project,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    User,
    utcnow,
)
from src.services.billing import initiate_plan_upgrade, verify_plan_upgrade

router = APIRouter(prefix="/api/v1/billing")


@router.post("/upgrade")
async def upgrade(
    request: Request,
    project: Annotated[Project, Depends(get_current_project)],
    user: Annotated[User | None, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}

    tier = body.get("tier", SubscriptionTier.team.value)
    settings = Settings.from_env()
    callback_url = f"{public_base_url()}/api/v1/billing/callback"

    subscription, payment_url = await initiate_plan_upgrade(
        project=project,
        user=user,
        tier=tier,
        callback_url=callback_url,
        db=db,
        settings=settings,
    )

    return {
        "subscription_id": str(subscription.id),
        "amount_rial": subscription.amount_rial,
        "authority": subscription.zarinpal_authority,
        "payment_url": payment_url,
    }


@router.get("/callback")
async def callback(
    Authority: str,
    Status: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RedirectResponse:
    settings = Settings.from_env()
    try:
        sub = await verify_plan_upgrade(
            authority=Authority,
            status_param=Status,
            db=db,
            settings=settings,
        )
        if sub.status == SubscriptionStatus.active.value:
            return RedirectResponse(url="/console/settings?payment=success", status_code=302)
        else:
            return RedirectResponse(url="/console/settings?payment=cancelled", status_code=302)
    except ApiError:
        return RedirectResponse(url="/console/settings?payment=failed", status_code=302)


@router.get("/subscription")
async def get_subscription(
    project: Annotated[Project, Depends(get_current_project)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    sub = await db.scalar(
        select(Subscription)
        .where(
            Subscription.project_id == project.id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.expires_at > utcnow(),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )

    if sub:
        return {
            "tier": sub.tier,
            "status": sub.status,
            "amount_toman": sub.amount_rial // 10,
            "started_at": sub.started_at.isoformat() if sub.started_at else None,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            "entitlements": {
                "daily_requests_limit": "unlimited",
                "active_adapters_limit": "all",
                "history_retention_days": 30,
            },
        }

    return {
        "tier": project.tier,
        "status": "active" if project.tier == SubscriptionTier.team.value else "free",
        "amount_toman": 0,
        "started_at": None,
        "expires_at": None,
        "entitlements": {
            "daily_requests_limit": "unlimited" if project.daily_requests_cap == 0 else project.daily_requests_cap,
            "active_adapters_limit": "all" if project.max_active_adapters == 0 else project.max_active_adapters,
            "history_retention_days": 1,
        },
    }
