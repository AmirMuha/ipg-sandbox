"""Park every non-Zarinpal adapter disabled, matching the new-project default (005).

`seed_configs` used to omit `enabled`, so `AdapterConfig.enabled` fell back to its
`default=True` and a fresh project came up with all 13 gateways live at once. New projects now
seed Zarinpal enabled and the rest parked; this migration brings existing rows in line.

The statement is plain SQL so it runs identically on the native Postgres `provider` enum and on
the SQLite VARCHAR the test suite uses.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE adapter_configs SET enabled = false WHERE provider != 'zarinpal'")


def downgrade() -> None:
    # Restores the pre-0009 state, where the column default made every adapter live.
    op.execute("UPDATE adapter_configs SET enabled = true WHERE provider != 'zarinpal'")