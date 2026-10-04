"""Add remaining 10 Iranian IPG providers to provider enum (FR-001).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-04

Expands the Postgres native `provider` enum to include all 13 documented Iranian gateways.
Labels are added with `IF NOT EXISTS` so the migration is safe to re-run and safe on
Postgres 16 (where ALTER TYPE ... ADD VALUE works within transactions).

SQLite test suite guard:
SQLite compiles `Provider` to VARCHAR with no native enum or check constraint, so
`op.get_bind().dialect.name != "postgresql"` exits early.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_LABELS = (
    "saman",
    "sadad",
    "parsian",
    "pasargad",
    "asan_pardakht",
    "pardakht_novin",
    "irankish",
    "fanava",
    "sarmayeh",
    "sizpay",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for label in NEW_LABELS:
        op.execute(f"ALTER TYPE provider ADD VALUE IF NOT EXISTS '{label}'")


def downgrade() -> None:
    # PostgreSQL cannot remove values from an existing enum type without dropping
    # and recreating the entire type and rewriting dependent tables.
    pass
