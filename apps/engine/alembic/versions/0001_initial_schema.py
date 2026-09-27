"""Initial schema: projects, adapter_configs, transactions, usage_meters (T008 models).

Revision ID: 0001
Revises:
Create Date: 2026-09-24

Self-contained snapshot — enum labels are spelled out rather than imported from
`src.models`, so a later model change cannot silently rewrite history.

WebhookDelivery is deliberately absent: it lands with T037 and gets its own revision.

Spec: specs/001-mvp/data-model.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROJECT_KIND = postgresql.ENUM("local", "demo", name="projectkind", create_type=False)
SCENARIO_OUTCOME = postgresql.ENUM(
    "approve",
    "decline",
    "timeout",
    "refund",
    "pending_settle",
    "verify_fail",
    name="scenariooutcome",
    create_type=False,
)
PROVIDER = postgresql.ENUM("zarinpal", "idpay", "behpardakht", name="provider", create_type=False)
API_UNIT = postgresql.ENUM("rial", "toman", name="apiunit", create_type=False)
TRANSACTION_STATUS = postgresql.ENUM(
    "initiated",
    "pending",
    "settled",
    "approved",
    "refunded",
    "expired",
    "declined",
    "failed",
    name="transactionstatus",
    create_type=False,
)

_ENUMS = (PROJECT_KIND, SCENARIO_OUTCOME, PROVIDER, API_UNIT, TRANSACTION_STATUS)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in _ENUMS:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", PROJECT_KIND, server_default="local", nullable=False),
        sa.Column("default_scenario", SCENARIO_OUTCOME, server_default="approve", nullable=False),
        sa.Column("history_cap", sa.Integer(), server_default=sa.text("1000"), nullable=False),
        sa.Column("webhook_retry_max", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column(
            "webhook_retry_backoff_s",
            postgresql.ARRAY(sa.Integer()),
            server_default=sa.text("'{1,2,4}'"),
            nullable=False,
        ),
        sa.Column(
            "pending_settle_delay_s", sa.Integer(), server_default=sa.text("5"), nullable=False
        ),
        sa.Column("timeout_delay_s", sa.Integer(), server_default=sa.text("30"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        # data-model.md Validation: history_cap >= 1; delays >= 0 and < 300.
        sa.CheckConstraint("history_cap >= 1", name="ck_projects_history_cap_min"),
        sa.CheckConstraint(
            "pending_settle_delay_s >= 0 AND pending_settle_delay_s < 300"
            " AND timeout_delay_s >= 0 AND timeout_delay_s < 300",
            name="ck_projects_delays_bounded",
        ),
        sa.CheckConstraint("webhook_retry_max >= 1", name="ck_projects_webhook_retry_max_min"),
    )

    op.create_table(
        "adapter_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", PROVIDER, nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "credentials", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("api_unit", API_UNIT, server_default="rial", nullable=False),
        sa.Column("endpoint_path_prefix", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.CheckConstraint("api_unit IN ('rial', 'toman')", name="ck_adapter_configs_api_unit"),
    )
    # "one enabled row per (project, provider)" — partial so disabled alternatives can coexist.
    op.create_index(
        "uq_adapter_configs_enabled_provider",
        "adapter_configs",
        ["project_id", "provider"],
        unique=True,
        postgresql_where=sa.text("enabled"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("adapter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_rial", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="IRR", nullable=False),
        sa.Column("status", TRANSACTION_STATUS, server_default="initiated", nullable=False),
        sa.Column("forced_scenario", SCENARIO_OUTCOME, nullable=True),
        sa.Column("effective_scenario", SCENARIO_OUTCOME, server_default="approve", nullable=False),
        sa.Column("authority", sa.Text(), nullable=True),
        sa.Column("app_reference", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("callback_url", sa.Text(), nullable=True),
        sa.Column("return_url", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_request", postgresql.JSONB(), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["adapter_id"], ["adapter_configs.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("amount_rial >= 0", name="ck_transactions_amount_rial_min"),
        sa.UniqueConstraint("project_id", "authority", name="uq_transactions_project_authority"),
    )
    op.create_index(
        "ix_transactions_project_created_at",
        "transactions",
        ["project_id", sa.text("created_at DESC")],
    )
    op.create_index("ix_transactions_status_due_at", "transactions", ["status", "due_at"])

    op.create_table(
        "usage_meters",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requests_total", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "transactions_total", sa.BigInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("history_retained", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("webhook_attempts", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("project_id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("usage_meters")
    op.drop_index("ix_transactions_status_due_at", table_name="transactions")
    op.drop_index("ix_transactions_project_created_at", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("uq_adapter_configs_enabled_provider", table_name="adapter_configs")
    op.drop_table("adapter_configs")
    op.drop_table("projects")

    bind = op.get_bind()
    for enum_type in reversed(_ENUMS):
        enum_type.drop(bind, checkfirst=True)
