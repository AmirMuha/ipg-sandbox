"""Add WebhookDelivery table and project webhook_url (T037).

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-29

Spec: specs/001-mvp/data-model.md §WebhookDelivery
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("webhook_url", sa.Text(), nullable=True))
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("result", sa.Text(), server_default="pending", nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_webhook_deliveries_transaction_id",
        "webhook_deliveries",
        ["transaction_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_transaction_id", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_column("projects", "webhook_url")
