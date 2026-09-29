"""WebhookDelivery model — spec: specs/001-mvp/data-model.md §WebhookDelivery (T037)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .models import utcnow


class DeliveryResult(enum.StrEnum):
    """Delivery result enum (data-model.md)."""

    delivered = "delivered"
    failed = "failed"
    pending = "pending"


class WebhookDelivery(Base):
    """One attempt to POST one callback payload to one target (FR-007, SC-005)."""

    __tablename__ = "webhook_deliveries"
    __table_args__ = (Index("ix_webhook_deliveries_transaction_id", "transaction_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    attempt: Mapped[int] = mapped_column(
        Integer, default=1, server_default=text("1"), nullable=False
    )
    result: Mapped[DeliveryResult] = mapped_column(
        default=DeliveryResult.pending,
        server_default=DeliveryResult.pending.value,
        nullable=False,
    )
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("now()"), nullable=False
    )
