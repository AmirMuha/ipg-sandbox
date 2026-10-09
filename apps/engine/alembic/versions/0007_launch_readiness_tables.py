"""Add users, user_sessions, subscriptions tables and project/meter extensions (004-launch-readiness-flows).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    uuid_type = sa.String(36) if is_sqlite else postgresql.UUID(as_uuid=True)

    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("auth_provider", sa.String(32), server_default=sa.text("'local'"), nullable=False),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("project_id", uuid_type, sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True),
        sa.Column("tier", sa.String(32), server_default=sa.text("'team'"), nullable=False),
        sa.Column("status", sa.String(32), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("amount_rial", sa.BigInteger(), nullable=False),
        sa.Column("zarinpal_authority", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("zarinpal_ref_id", sa.BigInteger(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.add_column("projects", sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("projects", sa.Column("tier", sa.String(32), server_default=sa.text("'developer'"), nullable=False))
    op.add_column("projects", sa.Column("daily_requests_cap", sa.Integer(), server_default=sa.text("100"), nullable=False))
    op.add_column("projects", sa.Column("max_active_adapters", sa.Integer(), server_default=sa.text("2"), nullable=False))

    op.add_column("usage_meters", sa.Column("requests_today", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("usage_meters", sa.Column("window_started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))


def downgrade() -> None:
    op.drop_column("usage_meters", "window_started_at")
    op.drop_column("usage_meters", "requests_today")
    op.drop_column("projects", "max_active_adapters")
    op.drop_column("projects", "daily_requests_cap")
    op.drop_column("projects", "tier")
    op.drop_column("projects", "user_id")
    op.drop_table("subscriptions")
    op.drop_table("user_sessions")
    op.drop_table("users")
