"""Transaction initiation, loading, and state transition service (T025).

Single owner of:
1. `amount_rial >= 0` trust boundary validation
2. `effective_scenario` resolution at initiation via `resolve_scenario`
3. History cap enforcement and meter updates via `record_transaction`
4. State machine transitions via `Transaction.transition_to`
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.errors import ApiError, ErrorCode, not_found
from src.models import (
    AdapterConfig,
    Project,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
)
from src.scenarios.resolve import resolve_scenario
from src.services.cap import record_transaction


async def initiate(
    session: AsyncSession,
    project: Project,
    adapter: AdapterConfig,
    *,
    amount_rial: int,
    authority: str | None = None,
    forced_scenario: ScenarioOutcome | None = None,
    header: str | None = None,
    app_reference: str | None = None,
    description: str | None = None,
    callback_url: str | None = None,
    return_url: str | None = None,
    raw_request: dict[str, Any] | None = None,
    raw_response: dict[str, Any] | None = None,
    currency: str = "IRR",
) -> Transaction:
    """Initiate a new transaction, enforce history cap, and bump usage meters."""
    if amount_rial < 0:
        raise ApiError(ErrorCode.validation_error, "amount_rial must be non-negative", status=422)

    effective = resolve_scenario(
        forced_scenario,
        header=header,
        project_default=project.default_scenario,
    )

    tx = Transaction(
        project_id=project.id,
        adapter_id=adapter.id,
        amount_rial=amount_rial,
        currency=currency,
        status=TransactionStatus.initiated,
        forced_scenario=forced_scenario,
        effective_scenario=effective,
        authority=authority,
        app_reference=app_reference,
        description=description,
        callback_url=callback_url,
        return_url=return_url,
        raw_request=raw_request,
        raw_response=raw_response,
    )

    await record_transaction(session, project, tx)
    await session.commit()
    return tx


async def load_by_authority(
    session: AsyncSession,
    project: Project,
    authority: str,
) -> Transaction:
    """Find transaction by authority under project, or raise not_found."""
    stmt = select(Transaction).where(
        Transaction.project_id == project.id,
        Transaction.authority == authority,
    )
    tx = await session.scalar(stmt)
    if tx is None:
        raise not_found("transaction")
    return tx


async def load_by_id(
    session: AsyncSession,
    project: Project,
    transaction_id: uuid.UUID,
) -> Transaction:
    """Find transaction by ID under project, or raise not_found."""
    stmt = select(Transaction).where(
        Transaction.project_id == project.id,
        Transaction.id == transaction_id,
    )
    tx = await session.scalar(stmt)
    if tx is None:
        raise not_found("transaction")
    return tx


async def advance(
    session: AsyncSession,
    tx: Transaction,
    new_status: TransactionStatus,
    *,
    raw_request: dict[str, Any] | None = None,
    raw_response: dict[str, Any] | None = None,
) -> Transaction:
    """Transition transaction to `new_status`, update raw payloads if provided, and commit."""
    tx.transition_to(new_status)
    if raw_request is not None:
        tx.raw_request = raw_request
    if raw_response is not None:
        tx.raw_response = raw_response
    await session.commit()
    return tx


def is_already_verified(tx: Transaction) -> bool:
    """Return True if transaction is already in settled/approved state (FR-011, T036)."""
    return tx.status in (TransactionStatus.settled, TransactionStatus.approved)

