"""Transaction control routes (T026) — contracts/control-api.md."""

import random
import uuid
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode, not_found
from src.api.routes import current_project
from src.models import (
    AdapterConfig,
    Project,
    Provider,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
)
from src.services import transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])
MAX_PAGE_SIZE = 100


def _transaction_body(tx: Transaction, *, include_raw: bool) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": tx.id,
        "project_id": tx.project_id,
        "adapter_id": tx.adapter_id,
        "amount_rial": tx.amount_rial,
        "currency": tx.currency,
        "status": tx.status,
        "forced_scenario": tx.forced_scenario,
        "effective_scenario": tx.effective_scenario,
        "authority": tx.authority,
        "app_reference": tx.app_reference,
        "description": tx.description,
        "callback_url": tx.callback_url,
        "return_url": tx.return_url,
        "due_at": tx.due_at,
        "created_at": tx.created_at,
        "updated_at": tx.updated_at,
    }
    if include_raw:
        body["raw_request"] = tx.raw_request
        body["raw_response"] = tx.raw_response
    return body


@router.get("")
async def list_transactions(
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
    status: TransactionStatus | None = None,
    adapter: Provider | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
) -> dict[str, Any]:
    """Newest first, pagination-safe (contracts/control-api.md Behavioral guarantees)."""
    where = [Transaction.project_id == project.id]
    if status is not None:
        where.append(Transaction.status == status)
    if adapter is not None:
        where.append(
            Transaction.adapter_id.in_(
                select(AdapterConfig.id).where(
                    AdapterConfig.project_id == project.id, AdapterConfig.provider == adapter
                )
            )
        )

    total = await session.scalar(select(func.count()).select_from(Transaction).where(*where))
    rows = await session.scalars(
        select(Transaction)
        .where(*where)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [_transaction_body(tx, include_raw=False) for tx in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post("", status_code=201)
async def pre_seed_transaction(
    request: Request,
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Pre-seed transaction with optional forced scenario (control-api.md)."""
    body: dict[str, Any] = await request.json()

    adapter_val = body.get("adapter")
    if not adapter_val:
        raise ApiError(ErrorCode.validation_error, "adapter is required", status=422)

    # Find adapter config by provider name or id
    adapter_stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        or_(
            AdapterConfig.provider == adapter_val,
            AdapterConfig.id == (UUID(adapter_val) if _is_valid_uuid(adapter_val) else None),
        ),
    )
    adapter_config = await session.scalar(adapter_stmt)
    if adapter_config is None:
        raise not_found(f"adapter {adapter_val}")

    amount_rial = body.get("amount_rial")
    if amount_rial is None:
        raise ApiError(ErrorCode.validation_error, "amount_rial is required", status=422)
    try:
        amount_rial = int(amount_rial)
    except (ValueError, TypeError):
        raise ApiError(
            ErrorCode.validation_error, "amount_rial must be an integer", status=422
        ) from None

    if amount_rial < 0:
        raise ApiError(ErrorCode.validation_error, "amount_rial must be non-negative", status=422)

    forced_scenario_str = body.get("forced_scenario")
    forced_scenario: ScenarioOutcome | None = None
    if forced_scenario_str:
        try:
            forced_scenario = ScenarioOutcome(forced_scenario_str)
        except ValueError:
            raise ApiError(
                ErrorCode.scenario_invalid,
                f"Invalid scenario: {forced_scenario_str}",
                status=422,
            ) from None

    authority = body.get("authority")
    if not authority:
        if adapter_config.provider == Provider.behpardakht:
            authority = str(random.randint(100000000000, 999999999999))
        else:
            authority = uuid.uuid4().hex

    tx = await transactions.initiate(
        session,
        project,
        adapter_config,
        amount_rial=amount_rial,
        authority=authority,
        forced_scenario=forced_scenario,
        app_reference=body.get("app_reference"),
        description=body.get("description"),
        callback_url=body.get("callback_url"),
        return_url=body.get("return_url"),
        raw_request=body,
        raw_response={"status": "pre_seeded", "authority": authority},
        currency=body.get("currency", "IRR"),
    )

    return _transaction_body(tx, include_raw=True)


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: UUID,
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    tx = await session.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.project_id == project.id
        )
    )
    if tx is None:
        raise not_found("transaction")
    return _transaction_body(tx, include_raw=True)


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: UUID,
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Manual purge of a transaction (control-api.md)."""
    tx = await session.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.project_id == project.id
        )
    )
    if tx is None:
        raise not_found("transaction")

    body = _transaction_body(tx, include_raw=True)
    await session.delete(tx)
    await session.commit()
    return body


def _is_valid_uuid(val: Any) -> bool:
    try:
        UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False
