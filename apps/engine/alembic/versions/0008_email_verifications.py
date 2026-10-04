"""Add email_verifications table for OTP registration flow.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    uuid_type = sa.String(36) if is_sqlite else postgresql.UUID(as_uuid=True)

    op.create_table(
        "email_verifications",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("email", sa.String(255), index=True, nullable=False),
        sa.Column("code", sa.String(6), nullable=False),
        sa.Column("verification_token", sa.String(64), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("email_verifications")
