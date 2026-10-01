"""Add VisitorSession

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-01 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure citext is available
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "visitor_sessions",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("project_id", postgresql.UUID(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("magic_link_token_hash", sa.String(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index(op.f("ix_visitor_sessions_email"), "visitor_sessions", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_visitor_sessions_email"), table_name="visitor_sessions")
    op.drop_table("visitor_sessions")
