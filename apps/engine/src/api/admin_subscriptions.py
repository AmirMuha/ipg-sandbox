"""Administrator control over paid subscriptions (deactivation, 007-plan-deactivation).

Same separation-of-surfaces reasoning as `admin_providers`: this router answers only to
`require_admin`, the merchant billing router only to the caller's own project — keeping them
apart means a missing guard on one cannot be masked by a guard present on the other.

Deactivation is deliberately admin-only and immediate: the paying user gets no self-serve
button (see settings page), and entitlements drop on the spot rather than at `expires_at`.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import not_found
from src.api.scoping import require_admin
from src.models import Project, Subscription, SubscriptionStatus, User
from src.services.billing import deactivate_subscription

router = APIRouter(prefix="/api/v1")


def _sub_body(sub: Subscription, project: Project | None, buyer: User | None) -> dict[str, Any]:
    return {
        "subscription_id": str(sub.id),
        "project_id": str(sub.project_id),
        "project_name": project.name if project else None,
        "buyer_email": buyer.email if buyer else None,
        "tier": sub.tier,
        "status": sub.status,
        "amount_toman": sub.amount_rial // 10,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
    }


@router.get("/admin/subscriptions")
async def list_subscriptions(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Every subscription an admin may act on: all rows except already-cancelled ones."""
    rows = (
        await db.execute(
            select(Subscription, Project, User)
            .join(Project, Subscription.project_id == Project.id)
            .outerjoin(User, Subscription.user_id == User.id)
            .where(Subscription.status != SubscriptionStatus.cancelled.value)
            .order_by(Subscription.created_at.desc())
            .limit(50)
        )
    ).all()
    return {"subscriptions": [_sub_body(sub, project, buyer) for sub, project, buyer in rows]}


@router.post("/admin/subscriptions/{subscription_id}/deactivate")
async def deactivate(
    subscription_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Cancel an active paid plan now and drop its project back to the free tier."""
    sub = await db.get(Subscription, subscription_id)
    if sub is None:
        raise not_found("Subscription")

    await deactivate_subscription(db, sub)

    project = await db.get(Project, sub.project_id)
    buyer = await db.get(User, sub.user_id) if sub.user_id else None
    return {"subscription": _sub_body(sub, project, buyer)}
