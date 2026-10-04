"""Live Zarinpal PGv4 subscription billing integration (004-launch-readiness-flows).

Allowlisted in test_simulation_guard.py for platform subscription payments.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
