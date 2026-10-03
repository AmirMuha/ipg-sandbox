"""Transaction control routes (T026) — contracts/control-api.md."""

import random
import uuid
from datetime import datetime, time
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import STAGE_NOTIFY, STAGE_SETTLE
from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode, not_found
from src.api.routes import current_project
from src.config import public_base_url
from src.models import (
    AdapterConfig,
    Project,
    Provider,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
    WebhookDelivery,
)
from src.scenarios.outcomes import apply_verify_outcome, checkout_confirm_status, set_due_at
from src.scenarios.resolve import resolve_scenario
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/transactions", tags=["transactions"])
MAX_PAGE_SIZE = 100

# IDPay mounts its hosted page at `/payment/start/{id}` while the other two use
# `/checkout/{ref}` — the same suffix the wire protocol names, not a dashboard invention.
_CHECKOUT_SUFFIX = {
    Provider.idpay: "/payment/start/{authority}",
}
_DEFAULT_CHECKOUT_SUFFIX = "/checkout/{authority}"


def checkout_path(adapter: AdapterConfig, tx: Transaction) -> str:
    """Host-relative path of `tx`'s hosted checkout page, from its adapter's mount prefix."""
    if adapter is None:
        return ""
    suffix = _CHECKOUT_SUFFIX.get(adapter.provider, _DEFAULT_CHECKOUT_SUFFIX).format(
        authority=tx.authority
    )
    return f"{adapter.endpoint_path_prefix}{suffix}"


def _transaction_body(
    tx: Transaction, *, include_raw: bool, adapter: AdapterConfig | None = None
) -> dict[str, Any]:
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
        # FR-002: computed here rather than left to the client, so no dashboard has to
        # re-derive a gateway's mount prefix. `None` only when the adapter row is gone.
        "checkout_url": (
            f"{public_base_url()}{checkout_path(adapter, tx)}" if adapter is not None else None
        ),
    }
    if include_raw:
        body["raw_request"] = tx.raw_request
        body["raw_response"] = tx.raw_response
    return body


async def _adapter_map(session: AsyncSession, adapter_ids: set[UUID]) -> dict[UUID, AdapterConfig]:
    """Adapter rows for the listed ids — `checkout_url` needs each row's mount prefix."""
    stmt = select(AdapterConfig).where(AdapterConfig.id.in_(adapter_ids))
    return {a.id: a for a in await session.scalars(stmt)}


async def _resolve_adapter(session: AsyncSession, project: Project, value: Any) -> AdapterConfig:
    """Adapter by provider name or id, enabled only — the shape `/simulate` accepts."""
    stmt = select(AdapterConfig).where(AdapterConfig.project_id == project.id)
    if value in tuple(Provider):
        stmt = stmt.where(AdapterConfig.provider == value, AdapterConfig.enabled.is_(True))
    elif _is_valid_uuid(value):
        stmt = stmt.where(AdapterConfig.id == UUID(str(value)), AdapterConfig.enabled.is_(True))
    else:
        raise ApiError(
            ErrorCode.validation_error,
            "adapter must be a provider name or adapter UUID",
            status=422,
            details={"allowed": [p.value for p in Provider]},
        )
    adapter = await session.scalar(stmt)
    if adapter is None:
        raise not_found(f"adapter {value}")
    return adapter


@router.get("")
async def list_transactions(
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
    q: str | None = None,
    status: TransactionStatus | None = None,
    adapter: Provider | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
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
    if q and q.strip():
        # `%` and `_` are LIKE wildcards; a search for "ORD_1" must not also match "ORDX1".
        needle = f"%{q.strip().replace('%', r'\%').replace('_', r'\_')}%"
        where.append(
            or_(
                Transaction.authority.ilike(needle),
                Transaction.app_reference.ilike(needle),
                Transaction.description.ilike(needle),
            )
        )
    if from_date is not None:
        where.append(Transaction.created_at >= from_date)
    if to_date is not None:
        # Date-only filters (e.g. from <input type="date">) parse to midnight 00:00:00.
        # Include the entire day by advancing to 23:59:59.999999.
        if to_date.time() == time.min:
            to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        where.append(Transaction.created_at <= to_date)

    total = await session.scalar(select(func.count()).select_from(Transaction).where(*where))
    rows = list(
        await session.scalars(
            select(Transaction)
            .where(*where)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    adapters = await _adapter_map(session, {tx.adapter_id for tx in rows})
    return {
        "items": [
            _transaction_body(tx, include_raw=False, adapter=adapters.get(tx.adapter_id))
            for tx in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/simulate", status_code=201)
async def simulate_transaction(
    request: Request,
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Create a payment from the dashboard: interactive checkout, or instant settlement.

    `/transactions` stays the low-level pre-seed; this is the high-level one a human or a
    CI script drives, so `auto_complete` runs the same two steps a browser would take
    (hosted checkout confirm, then verify) rather than writing `status` directly.
    """
    body: dict[str, Any] = await request.json()

    if not body.get("adapter"):
        raise ApiError(ErrorCode.validation_error, "adapter is required", status=422)
    adapter_config = await _resolve_adapter(session, project, body["adapter"])

    amount_rial = body.get("amount_rial")
    if amount_rial is None:
        raise ApiError(ErrorCode.validation_error, "amount_rial is required", status=422)
    try:
        amount_rial = int(amount_rial)
    except (ValueError, TypeError):
        raise ApiError(
            ErrorCode.validation_error, "amount_rial must be an integer", status=422
        ) from None

    forced_scenario: ScenarioOutcome | None = None
    if body.get("forced_scenario"):
        try:
            forced_scenario = ScenarioOutcome(body["forced_scenario"])
        except ValueError:
            raise ApiError(
                ErrorCode.scenario_invalid,
                f"Invalid scenario: {body['forced_scenario']}",
                status=422,
            ) from None

    authority = body.get("authority")
    if not authority:
        authority = (
            str(random.randint(100000000000, 999999999999))
            if adapter_config.provider == Provider.behpardakht
            else uuid.uuid4().hex
        )

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
        raw_response={"status": "simulated", "authority": authority},
    )

    callback_dispatched = False
    if body.get("auto_complete"):
        # Same edges the hosted page and the verify endpoint take, in the same order.
        if (target := checkout_confirm_status(tx)) is not None:
            if tx.effective_scenario is ScenarioOutcome.pending_settle:
                set_due_at(tx, project)
            await transactions.advance(session, tx, target)
        await apply_verify_outcome(tx)
        await session.commit()

        # Contract §2: a callback is dispatched "if callback_url is present". The flag has to
        # mean *sent*, not *would send* — the worker no-ops without a target, and a dashboard
        # reporting a dispatched callback that never left would be lying.
        if tx.callback_url or project.webhook_url:
            if tx.status is TransactionStatus.settled:
                schedule_delivery(
                    request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE
                )
                callback_dispatched = True
            elif tx.status is TransactionStatus.declined:
                schedule_delivery(
                    request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY
                )
                callback_dispatched = True

    body_tx = _transaction_body(tx, include_raw=True, adapter=adapter_config)
    return {
        "transaction": body_tx,
        "checkout_url": body_tx["checkout_url"],
        "execution_mode": "auto_completed" if body.get("auto_complete") else "interactive",
        "callback_dispatched": callback_dispatched,
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

    return _transaction_body(tx, include_raw=True, adapter=adapter_config)


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
    adapter = await session.scalar(select(AdapterConfig).where(AdapterConfig.id == tx.adapter_id))
    return _transaction_body(tx, include_raw=True, adapter=adapter)


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

    adapter = await session.scalar(select(AdapterConfig).where(AdapterConfig.id == tx.adapter_id))
    body = _transaction_body(tx, include_raw=True, adapter=adapter)
    # Explicit child delete: the FK says ondelete="CASCADE", but SQLite only honours that
    # with PRAGMA foreign_keys=ON, which the test/host engine never sets. Deleting the parent
    # alone would raise IntegrityError on Postgres-with-FK and orphan rows on SQLite.
    await session.execute(delete(WebhookDelivery).where(WebhookDelivery.transaction_id == tx.id))
    await session.delete(tx)
    await session.commit()
    return {**body, "deleted": True}


@router.patch("/{transaction_id}")
async def patch_transaction(
    request: Request,
    transaction_id: UUID,
    project: Annotated[Project, Depends(current_project)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """T032: force (or clear) the per-transaction scenario. Affects this row's future processing."""
    body: dict[str, Any] = await request.json()

    if "forced_scenario" not in body:
        raise ApiError(ErrorCode.validation_error, "forced_scenario is required", status=422)

    raw = body["forced_scenario"]
    forced: ScenarioOutcome | None = None
    if raw is not None:
        try:
            forced = ScenarioOutcome(raw)
        except ValueError:
            raise ApiError(
                ErrorCode.scenario_invalid,
                f"Invalid scenario: {raw}",
                status=422,
            ) from None

    tx = await session.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.project_id == project.id
        )
    )
    if tx is None:
        raise not_found("transaction")

    tx.forced_scenario = forced
    tx.effective_scenario = resolve_scenario(forced, project_default=project.default_scenario)
    await session.commit()
    adapter = await session.scalar(select(AdapterConfig).where(AdapterConfig.id == tx.adapter_id))
    return _transaction_body(tx, include_raw=True, adapter=adapter)


def _is_valid_uuid(val: Any) -> bool:
    try:
        UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False
