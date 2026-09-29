"""Webhook delivery routes (T040) — contracts/control-api.md."""

from typing import Annotated, Any
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode, not_found
from src.api.routes import _project_body, current_project
from src.models import (
    AdapterConfig,
    DeliveryResult,
    Project,
    Transaction,
    WebhookDelivery,
)
from src.webhooks.worker import deliver_once

router = APIRouter(tags=["deliveries"])
MAX_PAGE_SIZE = 100


def _delivery_body(d: WebhookDelivery) -> dict[str, Any]:
    return {
        "id": d.id,
        "transaction_id": d.transaction_id,
        "target_url": d.target_url,
        "stage": d.stage,
        "payload": d.payload,
        "attempt": d.attempt,
        "result": d.result,
        "response_status": d.response_status,
        "error": d.error,
        "created_at": d.created_at,
    }


@router.get("/deliveries")
async def list_deliveries(
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
    transaction_id: UUID | None = None,
    result: DeliveryResult | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
) -> dict[str, Any]:
    """List webhook deliveries scoped to current project's transactions."""
    where_clauses = [Transaction.project_id == project.id]
    if transaction_id is not None:
        where_clauses.append(WebhookDelivery.transaction_id == transaction_id)
    if result is not None:
        where_clauses.append(WebhookDelivery.result == result)

    total_stmt = (
        select(func.count())
        .select_from(WebhookDelivery)
        .join(Transaction, Transaction.id == WebhookDelivery.transaction_id)
        .where(*where_clauses)
    )
    total = (await session.scalar(total_stmt)) or 0

    stmt = (
        select(WebhookDelivery)
        .join(Transaction, Transaction.id == WebhookDelivery.transaction_id)
        .where(*where_clauses)
        .order_by(WebhookDelivery.created_at.desc(), WebhookDelivery.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    deliveries = (await session.scalars(stmt)).all()

    return {
        "items": [_delivery_body(d) for d in deliveries],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post("/deliveries/{delivery_id}/retry")
async def retry_delivery(
    request: Request,
    delivery_id: UUID,
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Force immediate re-attempt of a webhook delivery."""
    stmt = (
        select(WebhookDelivery)
        .join(Transaction, Transaction.id == WebhookDelivery.transaction_id)
        .where(
            WebhookDelivery.id == delivery_id,
            Transaction.project_id == project.id,
        )
    )
    old_delivery = await session.scalar(stmt)
    if old_delivery is None:
        raise not_found("delivery")

    tx = await session.get(Transaction, old_delivery.transaction_id)
    if tx is None:
        raise not_found("transaction")

    config = await session.get(AdapterConfig, tx.adapter_id)
    if config is None:
        raise not_found("adapter")

    # Next attempt number
    attempt_num = old_delivery.attempt + 1
    new_delivery = await deliver_once(
        request.app.state.session_factory,
        project,
        tx,
        config,
        old_delivery.stage,
        old_delivery.target_url,
        attempt_num,
    )
    return _delivery_body(new_delivery)


@router.put("/project/webhook-url")
async def update_project_webhook_url(
    request: Request,
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Update project-level default webhook URL."""
    body = await request.json()
    if "webhook_url" not in body:
        raise ApiError(ErrorCode.validation_error, "webhook_url field is required", status=422)

    url = body["webhook_url"]
    if url is not None:
        if not isinstance(url, str):
            raise ApiError(
                ErrorCode.validation_error, "webhook_url must be a string or null", status=422
            )
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ApiError(
                ErrorCode.validation_error,
                "webhook_url must be an absolute http(s) URL",
                status=422,
            )

    project.webhook_url = url
    await session.commit()
    return _project_body(project)
