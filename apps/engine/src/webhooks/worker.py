"""Webhook delivery worker (T039) — research R6, FR-007, SC-005.

One `deliver()` call is one (transaction, stage) -> retry chain. Every attempt INSERTs a
`pending` row and UPDATEs it with the outcome, so an unreachable target leaves the same
visible trail as a successful one (data-model.md Rule, no-silent-loss).
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.models import (
    AdapterConfig,
    DeliveryResult,
    Project,
    Transaction,
    UsageMeter,
    WebhookDelivery,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_S = 5.0
_SUCCESS = range(200, 400)

_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def _backoff(project: Project, attempt: int) -> float:
    """Delay in seconds before retry `attempt` (1-based index)."""
    schedule = list(project.webhook_retry_backoff_s)
    if not schedule:
        return 0.0
    idx = min(attempt - 1, len(schedule) - 1)
    return float(schedule[idx])


def _target_for(tx: Transaction, project: Project) -> str | None:
    """Per-transaction callback_url wins; project default webhook_url is fallback."""
    return tx.callback_url or project.webhook_url


async def _attempt(
    session: AsyncSession,
    project: Project,
    tx: Transaction,
    stage: str,
    target: str,
    payload: dict[str, Any],
    attempt_num: int,
) -> WebhookDelivery:
    """INSERT pending row -> POST -> UPDATE result. Pending is durable before network call."""
    row = WebhookDelivery(
        transaction_id=tx.id,
        target_url=target,
        stage=stage,
        payload=payload,
        attempt=attempt_num,
        result=DeliveryResult.pending,
    )
    session.add(row)
    await session.commit()

    # Increment UsageMeter counter
    meter = await session.get(UsageMeter, project.id)
    if meter is None:
        meter = UsageMeter(project_id=project.id)
        session.add(meter)
    meter.webhook_attempts += 1
    await session.commit()

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
            resp = await client.post(target, json=payload)
        ok = resp.status_code in _SUCCESS
        row.result = DeliveryResult.delivered if ok else DeliveryResult.failed
        row.response_status = resp.status_code
        if not ok:
            row.error = f"HTTP {resp.status_code}"
    except httpx.HTTPError as exc:
        row.result = DeliveryResult.failed
        row.error = f"{type(exc).__name__}: {exc}"[:500]
    except Exception as exc:
        row.result = DeliveryResult.failed
        row.error = f"{type(exc).__name__}: {exc}"[:500]

    await session.commit()
    return row


async def deliver(
    session_factory: async_sessionmaker[AsyncSession],
    project: Project,
    tx: Transaction,
    config: AdapterConfig,
    stage: str,
) -> WebhookDelivery | None:
    """Run bounded retry chain for one (tx, stage). Returns the last attempt row."""
    target = _target_for(tx, project)
    if not target:
        return None

    from src.webhooks.payloads import payload_for

    payload = payload_for(config, stage, tx)

    async with session_factory() as session:
        for attempt_num in range(1, project.webhook_retry_max + 1):
            if attempt_num > 1:
                delay = _backoff(project, attempt_num - 1)
                if delay > 0:
                    await asyncio.sleep(delay)

            row = await _attempt(session, project, tx, stage, target, payload, attempt_num)
            if row.result is DeliveryResult.delivered:
                return row
        return row


async def deliver_once(
    session_factory: async_sessionmaker[AsyncSession],
    project: Project,
    tx: Transaction,
    config: AdapterConfig,
    stage: str,
    target: str,
    attempt_num: int,
) -> WebhookDelivery:
    """Execute a single attempt (used by manual retry)."""
    from src.webhooks.payloads import payload_for

    payload = payload_for(config, stage, tx)
    async with session_factory() as session:
        return await _attempt(session, project, tx, stage, target, payload, attempt_num)


async def _run_scheduled_delivery(
    session_factory: async_sessionmaker[AsyncSession],
    project_id: UUID,
    tx_id: UUID,
    stage: str,
) -> None:
    try:
        async with session_factory() as session:
            tx = await session.get(Transaction, tx_id)
            project = await session.get(Project, project_id)
            if tx is None or project is None:
                return
            config = await session.get(AdapterConfig, tx.adapter_id)
            if config is None:
                return
            await deliver(session_factory, project, tx, config, stage)
    except Exception:
        logger.exception("Scheduled webhook delivery failed for tx %s", tx_id)


def schedule_delivery(
    session_factory: async_sessionmaker[AsyncSession],
    project_id: UUID,
    tx_id: UUID,
    stage: str,
) -> asyncio.Task[Any]:
    """Fire-and-forget delivery task. Strong ref held until completion."""
    task = asyncio.create_task(_run_scheduled_delivery(session_factory, project_id, tx_id, stage))
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    return task
