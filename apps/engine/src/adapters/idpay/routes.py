"""IDPay emulated gateway routes (T022) — contracts/adapter-surfaces.md §2."""

from typing import Annotated, Any
from urllib.parse import parse_qs, urlencode

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import to_rial
from src.adapters.idpay.adapter import IDPayAdapter
from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode, not_found
from src.api.routes import current_project
from src.models import (
    AdapterConfig,
    Project,
    Provider,
    ScenarioOutcome,
    TransactionStatus,
)
from src.scenarios.outcomes import (
    apply_initiate_outcome,
    checkout_confirm_status,
    set_due_at,
)
from src.services import transactions

router = APIRouter(prefix="/idpay", tags=["idpay"])


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> IDPayAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.idpay,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("adapter idpay")
    return IDPayAdapter(config)


def _append_query(base_url: str, params: dict[str, Any]) -> str:
    qs = urlencode(params)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{qs}"


@router.post("/payment")
async def initiate_payment(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[IDPayAdapter, Depends(get_adapter)],
    x_api_key: Annotated[str | None, Header(alias="X-API-KEY")] = None,
    x_sandbox_scenario: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()

    # Credential check
    api_key = x_api_key if x_api_key is not None else body.get("api_key")
    if api_key == "":
        raise ApiError(ErrorCode.invalid_credentials, "Invalid or empty api_key", status=401)
    adapter.check_credentials()

    amount = body.get("amount")
    if amount is None:
        raise ApiError(ErrorCode.validation_error, "amount is required", status=422)

    amount_toman = int(amount)
    amount_rial = to_rial(amount_toman, adapter.api_unit)
    callback_url = body.get("callback") or body.get("callback_url")
    order_id = body.get("order_id")
    desc = body.get("desc") or body.get("description")

    tx = await transactions.initiate(
        session,
        project,
        adapter.config,
        amount_rial=amount_rial,
        header=x_sandbox_scenario,
        app_reference=order_id,
        callback_url=callback_url,
        description=desc,
        currency="IRR",
        raw_request=body,
    )

    if await apply_initiate_outcome(tx, project) is ScenarioOutcome.timeout:
        timeout_resp = {
            "error_code": 51,
            "error_message": "Payment session expired",
        }
        tx.raw_response = timeout_resp
        await session.commit()
        return timeout_resp

    resp = await adapter.create_payment(tx, body)
    tx.raw_response = resp
    await session.commit()
    return resp


@router.get("/payment/start/{id}", response_class=HTMLResponse)
async def checkout_view(
    id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[IDPayAdapter, Depends(get_adapter)],
    lang: str = "fa",
) -> HTMLResponse:
    tx = await transactions.load_by_authority(session, project, id)
    html = await adapter.checkout_page(tx, lang=lang)
    return HTMLResponse(content=html)


@router.post("/payment/start/{id}")
async def checkout_action(
    request: Request,
    id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> RedirectResponse:
    body_bytes = await request.body()
    parsed_form = parse_qs(body_bytes.decode("utf-8"))
    action_list = parsed_form.get("action", ["confirm"])
    action = action_list[0] if action_list else "confirm"

    tx = await transactions.load_by_authority(session, project, id)
    target_url = tx.callback_url or tx.return_url or "/"
    track_id = 100000 + (tx.amount_rial % 900000)

    if action == "confirm":
        if (target := checkout_confirm_status(tx)) is not None:
            if tx.effective_scenario is ScenarioOutcome.pending_settle:
                set_due_at(tx, project)
            await transactions.advance(session, tx, target)
        status_code = "10"
    elif action == "fail":
        await transactions.advance(session, tx, TransactionStatus.declined)
        status_code = "7"
    else:  # abandon
        await transactions.advance(session, tx, TransactionStatus.pending)
        await transactions.advance(session, tx, TransactionStatus.expired)
        status_code = "2"

    redirect_target = _append_query(
        target_url,
        {
            "status": status_code,
            "track_id": track_id,
            "id": tx.authority,
            "order_id": tx.app_reference or "",
        },
    )
    return RedirectResponse(url=redirect_target, status_code=302)


@router.post("/payment/verify")
async def verify_payment(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[IDPayAdapter, Depends(get_adapter)],
) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()
    pay_id = body.get("id")
    if not pay_id:
        raise ApiError(ErrorCode.validation_error, "id is required", status=422)

    tx = await transactions.load_by_authority(session, project, pay_id)
    resp = await adapter.verify(tx, body)
    tx.raw_response = resp
    await session.commit()
    return resp


@router.post("/payment/refund")
async def refund_payment(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[IDPayAdapter, Depends(get_adapter)],
) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()
    pay_id = body.get("id")
    if not pay_id:
        raise ApiError(ErrorCode.validation_error, "id is required", status=422)

    tx = await transactions.load_by_authority(session, project, pay_id)
    resp = await adapter.refund(tx, body)
    tx.raw_response = resp
    await session.commit()
    return resp
