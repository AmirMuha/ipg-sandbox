"""Add visitor_sessions.expires_at for magic-link expiry (T071).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-01

T052 specifies a "single-use expiring" magic-link token. Single-use held (`verified_at` is
checked), but nothing bounded the window: `main.py` selected on the token hash with no time
predicate, so a link stayed valid forever until first use.

Nullable so existing rows stay valid; the demo signs up with an explicit expiry going forward.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "visitor_sessions",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("visitor_sessions", "expires_at")
