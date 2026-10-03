"""Project-wide aggregate metrics (T012) — contracts/control-api.md §1.

Every number here is aggregated in SQL over all retained rows, never assembled in Python
from one page of transactions: FR-004 exists precisely because the previous dashboard cards
summed whatever 50 rows the list endpoint happened to return.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.routes import current_project
from src.models import (
    AdapterConfig,
    DeliveryResult,
    Project,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
    WebhookDelivery,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Totals, status/scenario breakdowns, lifecycle funnel, webhook and gateway rollups."""
    tx_scope = (Transaction.project_id == project.id,)

    # Volume, transaction count, and the count of rows that are NOT in a terminal failure
    # state — success rate as "settled / everything", which is what the contract's example
    # (139 settled of 148 = 93.9%) reports.
    totals = (
        await session.execute(
            select(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount_rial), 0),
                func.coalesce(
                    func.sum(case((Transaction.status == TransactionStatus.settled, 1), else_=0)),
                    0,
                ),
            ).where(*tx_scope)
        )
    ).one()
    total_transactions, total_volume, settled_count = (int(v or 0) for v in totals)

    status_breakdown = {s.value: 0 for s in TransactionStatus}
    for status, count in (
        await session.execute(
            select(Transaction.status, func.count()).where(*tx_scope).group_by(Transaction.status)
        )
    ).all():
        status_breakdown[status.value] = int(count)

    scenario_distribution = {s.value: 0 for s in ScenarioOutcome}
    for scenario, count in (
        await session.execute(
            select(Transaction.effective_scenario, func.count())
            .where(*tx_scope)
            .group_by(Transaction.effective_scenario)
        )
    ).all():
        if scenario is not None:
            scenario_distribution[scenario.value] = int(count)

    webhook_counts = {r.value: 0 for r in DeliveryResult}
    for result, count in (
        await session.execute(
            select(WebhookDelivery.result, func.count())
            .join(Transaction, Transaction.id == WebhookDelivery.transaction_id)
            .where(*tx_scope)
            .group_by(WebhookDelivery.result)
        )
    ).all():
        webhook_counts[result.value] = int(count)

    per_adapter_counts = (
        await session.execute(
            select(Transaction.adapter_id, func.count())
            .where(*tx_scope)
            .group_by(Transaction.adapter_id)
        )
    ).all()
    configured_total = await session.scalar(
        select(func.count())
        .select_from(AdapterConfig)
        .where(AdapterConfig.project_id == project.id)
    )
    # "active" means the gateway has actually been exercised inside the retention window,
    # so `active_total <= configured_total` always holds.
    active_total = sum(1 for adapter_id, _ in per_adapter_counts if adapter_id is not None)

    return {
        "total_volume_rial": total_volume,
        "total_transactions": total_transactions,
        "success_rate_percent": (
            round(settled_count / total_transactions * 100, 1) if total_transactions else 0.0
        ),
        "status_breakdown": status_breakdown,
        "scenario_distribution": scenario_distribution,
        "funnel": {
            # Monotonic by construction: each stage's population is a subset of the last.
            "initiated": total_transactions,
            "hosted": sum(
                status_breakdown[s.value]
                for s in (
                    TransactionStatus.pending,
                    TransactionStatus.approved,
                    TransactionStatus.settled,
                    TransactionStatus.refunded,
                    TransactionStatus.expired,
                    TransactionStatus.declined,
                )
            ),
            "callback": sum(
                status_breakdown[s.value]
                for s in (
                    TransactionStatus.approved,
                    TransactionStatus.settled,
                    TransactionStatus.refunded,
                )
            ),
            "settled": status_breakdown[TransactionStatus.settled.value],
        },
        "webhooks": {
            "total_deliveries": sum(webhook_counts.values()),
            "delivered": webhook_counts[DeliveryResult.delivered.value],
            "failed": webhook_counts[DeliveryResult.failed.value],
            "pending": webhook_counts[DeliveryResult.pending.value],
        },
        "gateways": {"configured_total": configured_total, "active_total": active_total},
    }
