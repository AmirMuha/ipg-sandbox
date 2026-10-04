"""Billing and subscription models (004-launch-readiness-flows)."""

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionTier(StrEnum):
    developer = "developer"
    team = "team"
    unlimited = "unlimited"


class SubscriptionStatus(StrEnum):
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    tier: Mapped[str] = mapped_column(
        String(32), default=SubscriptionTier.team.value, server_default=text("'team'"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=SubscriptionStatus.pending.value,
        server_default=text("'pending'"),
        nullable=False,
    )
    amount_rial: Mapped[int] = mapped_column(BigInteger, nullable=False)
    zarinpal_authority: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    zarinpal_ref_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("now()"), nullable=False
    )
