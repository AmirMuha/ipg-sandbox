"""Live Zarinpal PGv4 subscription billing integration (004-launch-readiness-flows).

Allowlisted in test_simulation_guard.py for platform subscription payments.
"""

import asyncio
import logging
import uuid
from datetime import timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.errors import ApiError, ErrorCode
from src.config import Settings
from src.models import (
    Project,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    User,
    utcnow,
)

TEAM_PLAN_AMOUNT_RIAL = 1_990_000  # 199,000 Toman

# Free-tier constants, matching what signup writes (src/api/auth.py): 100 requests/day, 2 gateways.
FREE_DAILY_REQUESTS_CAP = 100
FREE_MAX_ACTIVE_ADAPTERS = 2

EXPIRY_SWEEP_INTERVAL_S = 60
logger = logging.getLogger(__name__)


def _zarinpal_base_url(settings: Settings) -> str:
    return "https://sandbox.zarinpal.com/pg" if settings.zarinpal_sandbox else "https://payment.zarinpal.com/pg"


async def initiate_plan_upgrade(
    project: Project,
    user: User | None,
    tier: str,
    callback_url: str,
    db: AsyncSession,
    settings: Settings,
) -> tuple[Subscription, str]:
    """Request payment authority from Zarinpal PGv4 and persist pending Subscription."""
    if tier != SubscriptionTier.team.value:
        raise ApiError(ErrorCode.validation_error, f"Unsupported subscription tier: {tier}", status=400)

    # No-downgrade / no-double-charge: a project already on an active paid plan cannot buy
    # again (and therefore cannot re-buy its way to a "different" state) until it lapses.
    active = await db.scalar(
        select(Subscription.id).where(
            Subscription.project_id == project.id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.expires_at > utcnow(),
        )
    )
    if active is not None:
        raise ApiError(
            ErrorCode.unsupported_operation,
            "Project already has an active Team subscription; purchase again after it expires",
            status=409,
        )

    amount = TEAM_PLAN_AMOUNT_RIAL
    base_url = _zarinpal_base_url(settings)
    req_url = f"{base_url}/v4/payment/request.json"

    payload = {
        "merchant_id": settings.zarinpal_merchant_id,
        "amount": amount,
        "description": f"Subscription Upgrade to Team Plan for project {project.name}",
        "callback_url": callback_url,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(req_url, json=payload)
            data = resp.json()
    except Exception as exc:
        raise ApiError(ErrorCode.validation_error, f"Failed to connect to Zarinpal gateway: {exc}", status=502)

    code = data.get("data", {}).get("code")
    authority = data.get("data", {}).get("authority")
    if code != 100 or not authority:
        msg = data.get("errors", {}).get("message") or f"Zarinpal returned error code {code}"
        raise ApiError(ErrorCode.validation_error, msg, status=400)

    subscription = Subscription(
        project_id=project.id,
        user_id=user.id if user else None,
        tier=tier,
        status=SubscriptionStatus.pending.value,
        amount_rial=amount,
        zarinpal_authority=authority,
    )
    db.add(subscription)
    await db.commit()

    payment_url = f"{base_url}/StartPay/{authority}"
    return subscription, payment_url


async def verify_plan_upgrade(
    authority: str,
    status_param: str,
    db: AsyncSession,
    settings: Settings,
) -> Subscription:
    """Verify Zarinpal PGv4 payment and upgrade project tier upon success."""
    subscription = await db.scalar(
        select(Subscription).where(Subscription.zarinpal_authority == authority)
    )
    if not subscription:
        raise ApiError(ErrorCode.not_found, "Subscription record not found", status=404)

    if status_param.upper() != "OK":
        subscription.status = SubscriptionStatus.cancelled.value
        await db.commit()
        return subscription

    base_url = _zarinpal_base_url(settings)
    verify_url = f"{base_url}/v4/payment/verify.json"
    payload = {
        "merchant_id": settings.zarinpal_merchant_id,
        "amount": subscription.amount_rial,
        "authority": authority,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(verify_url, json=payload)
            data = resp.json()
    except Exception as exc:
        raise ApiError(ErrorCode.validation_error, f"Failed to verify payment with Zarinpal: {exc}", status=502)

    code = data.get("data", {}).get("code")
    ref_id = data.get("data", {}).get("ref_id")

    if code in (100, 101):
        subscription.status = SubscriptionStatus.active.value
        subscription.zarinpal_ref_id = ref_id
        subscription.started_at = utcnow()
        subscription.expires_at = utcnow() + timedelta(days=30)

        # Upgrade project entitlements: unlimited requests and all adapters allowed
        project = await db.get(Project, subscription.project_id)
        if project:
            project.tier = SubscriptionTier.team.value
            project.daily_requests_cap = 0
            project.max_active_adapters = 0

        await db.commit()
        return subscription
    else:
        subscription.status = SubscriptionStatus.cancelled.value
        await db.commit()
        msg = data.get("errors", {}).get("message") or f"Payment verification failed (code {code})"
        raise ApiError(ErrorCode.validation_error, msg, status=400)


def revert_to_free(project: Project) -> None:
    """Put a project back on the free tier — the single writer for deactivation and expiry.

    ponytail: always 100/2, so the local-profile bootstrap project (0/0 = unlimited) also gets
    capped if someone deactivates a paid sub there; per-profile restore only if local billing
    becomes a real scenario. `history_cap` is left alone: upgrade never raises it.
    """
    project.tier = SubscriptionTier.developer.value
    project.daily_requests_cap = FREE_DAILY_REQUESTS_CAP
    project.max_active_adapters = FREE_MAX_ACTIVE_ADAPTERS


async def _has_other_active(db: AsyncSession, project_id: uuid.UUID, exclude_id: uuid.UUID) -> bool:
    """True when another unexpired active subscription still pays for this project."""
    other = await db.scalar(
        select(Subscription.id).where(
            Subscription.project_id == project_id,
            Subscription.id != exclude_id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.expires_at > utcnow(),
        )
    )
    return other is not None


async def deactivate_subscription(db: AsyncSession, subscription: Subscription) -> Subscription:
    """Cancel an already-paid plan immediately and revert its project to the free tier.

    Only `active` rows may be deactivated — expiring or cancelling a pending payment is the
    gateway callback's job, not the admin's.
    """
    if subscription.status != SubscriptionStatus.active.value:
        raise ApiError(
            ErrorCode.unsupported_operation,
            f"Only an active subscription can be deactivated (status: {subscription.status})",
            status=409,
        )

    subscription.status = SubscriptionStatus.cancelled.value
    if not await _has_other_active(db, subscription.project_id, subscription.id):
        project = await db.get(Project, subscription.project_id)
        if project:
            revert_to_free(project)
    await db.commit()
    return subscription


async def expire_due_subscriptions(db: AsyncSession) -> int:
    """Lapse every active subscription past its paid period; returns how many were transitioned.

    Without this, entitlements never end: `GET /billing/subscription` falls back to
    `project.tier`, which would stay `team` forever.
    """
    due = (
        await db.scalars(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.expires_at.is_not(None),
                Subscription.expires_at <= utcnow(),
            )
        )
    ).all()
    for sub in due:
        sub.status = SubscriptionStatus.expired.value
        if not await _has_other_active(db, sub.project_id, sub.id):
            project = await db.get(Project, sub.project_id)
            if project:
                revert_to_free(project)
    if due:
        await db.commit()
    return len(due)


async def run_subscription_expiry(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Sweep expired subscriptions every EXPIRY_SWEEP_INTERVAL_S (a lifespan task)."""
    while True:
        try:
            async with session_factory() as session:
                await expire_due_subscriptions(session)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("subscription expiry sweep failed")
        await asyncio.sleep(EXPIRY_SWEEP_INTERVAL_S)
