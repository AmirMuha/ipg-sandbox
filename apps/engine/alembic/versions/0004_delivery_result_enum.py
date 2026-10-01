"""Align webhook_deliveries.result with the DeliveryResult enum (T037/T060).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-01

0002 created `webhook_deliveries.result` as `Text()`, but `WebhookDelivery.result` is mapped to
a `DeliveryResult` StrEnum, which SQLAlchemy renders as the native Postgres type
`deliveryresult`. Every INSERT therefore failed against a real database with
`type "deliveryresult" does not exist` — the SQLite-backed test suite compiled the same
column as plain TEXT and never saw it.

0001 already established the project convention: enum columns are native Postgres ENUMs
(`postgresql.ENUM(..., create_type=False)`), created once in the `upgrade()` body. This
revision follows it, creating the missing type rather than downgrading the model to String.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DELIVERY_RESULT = postgresql.ENUM(
    "delivered",
    "failed",
    "pending",
    name="deliveryresult",
    create_type=False,
)


def upgrade() -> None:
    DELIVERY_RESULT.create(op.get_bind(), checkfirst=True)
    # Drop the default first: the column carries `server_default='pending'` as a bare text
    # literal, and Postgres refuses to auto-cast that literal to the new type
    # ("default for column \"result\" cannot be cast automatically to type deliveryresult").
    # We re-attach it as a cast expression afterwards so the model default survives.
    op.alter_column("webhook_deliveries", "result", server_default=None)
    op.alter_column(
        "webhook_deliveries",
        "result",
        existing_type=sa.Text(),
        type_=DELIVERY_RESULT,
        existing_nullable=False,
        postgresql_using="result::deliveryresult",
    )
    op.alter_column(
        "webhook_deliveries",
        "result",
        server_default=sa.text("'pending'::deliveryresult"),
    )


def downgrade() -> None:
    op.alter_column("webhook_deliveries", "result", server_default=None)
    op.alter_column(
        "webhook_deliveries",
        "result",
        existing_type=DELIVERY_RESULT,
        type_=sa.Text(),
        existing_nullable=False,
        postgresql_using="result::text",
    )
    op.alter_column("webhook_deliveries", "result", server_default=sa.text("'pending'"))
    DELIVERY_RESULT.drop(op.get_bind(), checkfirst=True)
