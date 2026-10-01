"""Zarinpal emulated gateway routes (T021) — contracts/adapter-surfaces.md §1."""

from typing import Annotated, Any
from urllib.parse import parse_qs, urlencode

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import (
    STAGE_NOTIFY,
    STAGE_REFUND,
    STAGE_SETTLE,
    to_rial,
)
from src.adapters.base import unsupported_operation as base_unsupported
from src.adapters.zarinpal.adapter import ZarinpalAdapter
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
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/zarinpal", tags=["zarinpal"])


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> ZarinpalAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.zarinpal,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("adapter zarinpal")
    return ZarinpalAdapter(config)


def _append_query(base_url: str, params: dict[str, Any]) -> str:
    qs = urlencode(params)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{qs}"


@router.post("/request/payment")
async def initiate_payment(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[ZarinpalAdapter, Depends(get_adapter)],
    x_sandbox_scenario: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()

    # Credential check. Rejects absent, empty AND mismatched values: checking only `== ""`
    # let an omitted merchant_id fall through as `None`, and accepting any value meant a
    # wrong merchant still created a payment (spec edge case: invalid or unknown credentials
    # must surface a clear error, not a hang or a generic crash).
    merchant_id = body.get("merchant_id")
    if merchant_id is None:
        merchant_id = body.get("MerchantID")
    adapter.verify_supplied_credentials({"merchant_id": merchant_id})

    amount = body.get("amount") or body.get("Amount")
    if amount is None:
        raise ApiError(ErrorCode.validation_error, "amount is required", status=422)

    amount_rial = to_rial(int(amount), adapter.api_unit)
    callback_url = body.get("callback_url") or body.get("CallbackURL")
    return_url = body.get("return_url") or body.get("ReturnURL") or callback_url
    description = body.get("description") or body.get("Description")
    currency = body.get("currency") or body.get("Currency") or "IRR"

    tx = await transactions.initiate(
        session,
        project,
        adapter.config,
        amount_rial=amount_rial,
        header=x_sandbox_scenario,
        callback_url=callback_url,
        return_url=return_url,
        description=description,
        currency=currency,
        raw_request=body,
    )

    if await apply_initiate_outcome(tx, project) is ScenarioOutcome.timeout:
        timeout_resp = {"code": -33, "message": "Payment session expired"}
        tx.raw_response = timeout_resp
        await session.commit()
        return timeout_resp

    resp = await adapter.create_payment(tx, body)
    tx.raw_response = resp
    await session.commit()
    return resp


@router.get("/checkout/{authority}", response_class=HTMLResponse)
async def checkout_view(
    authority: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[ZarinpalAdapter, Depends(get_adapter)],
    lang: str = "fa",
) -> HTMLResponse:
    tx = await transactions.load_by_authority(session, project, authority)
    html = await adapter.checkout_page(tx, lang=lang)
    return HTMLResponse(content=html)


@router.post("/checkout/{authority}")
async def checkout_action(
    request: Request,
    authority: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> RedirectResponse:
    body_bytes = await request.body()
    parsed_form = parse_qs(body_bytes.decode("utf-8"))
    action_list = parsed_form.get("action", ["confirm"])
    action = action_list[0] if action_list else "confirm"

    tx = await transactions.load_by_authority(session, project, authority)
    target_url = tx.return_url or tx.callback_url or "/"

    if action == "confirm":
        if (target := checkout_confirm_status(tx)) is not None:
            if tx.effective_scenario is ScenarioOutcome.pending_settle:
                set_due_at(tx, project)
            await transactions.advance(session, tx, target)
        status_param = "OK"
    elif action == "fail":
        await transactions.advance(session, tx, TransactionStatus.declined)
        status_param = "NOK"
    else:  # abandon
        await transactions.advance(session, tx, TransactionStatus.pending)
        await transactions.advance(session, tx, TransactionStatus.expired)
        status_param = "CANCELLED"

    redirect_target = _append_query(target_url, {"Authority": tx.authority, "Status": status_param})
    return RedirectResponse(url=redirect_target, status_code=302)


@router.get("/callback/{authority}")
async def callback_redirect(
    authority: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    status: str = Query("OK", alias="Status"),
) -> RedirectResponse:
    tx = await transactions.load_by_authority(session, project, authority)
    target_url = tx.return_url or tx.callback_url or "/"
    redirect_target = _append_query(target_url, {"Authority": tx.authority, "Status": status})
    return RedirectResponse(url=redirect_target, status_code=302)


@router.post("/payment/verification")
async def verify_payment(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[ZarinpalAdapter, Depends(get_adapter)],
) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()
    authority = body.get("authority") or body.get("Authority")
    if not authority:
        raise ApiError(ErrorCode.validation_error, "authority is required", status=422)

    tx = await transactions.load_by_authority(session, project, authority)
    resp = await adapter.verify(tx, body)
    tx.raw_response = resp
    await session.commit()
    if tx.status == TransactionStatus.settled:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
    elif tx.status == TransactionStatus.declined:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)
    return resp


@router.post("/payment/refund")
async def refund_payment(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[ZarinpalAdapter, Depends(get_adapter)],
) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()
    authority = body.get("authority") or body.get("Authority")
    if not authority:
        raise ApiError(ErrorCode.validation_error, "authority is required", status=422)

    tx = await transactions.load_by_authority(session, project, authority)
    resp = await adapter.refund(tx, body)
    tx.raw_response = resp
    await session.commit()
    if tx.status == TransactionStatus.refunded:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_REFUND)
    return resp


# T081: an operation this adapter does not emulate is answered explicitly, not as a bare 404.
# A wrong *method* on a real operation must still answer 405, so the catch-all checks the path
# against the operations this adapter actually serves before claiming it.
_ZARINPAL_OPERATIONS = frozenset(
    {
        "request/payment",
        "checkout/{authority}",
        "callback/{authority}",
        "payment/verification",
        "payment/refund",
    }
)


@router.api_route(
    "/{unsupported:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def unsupported_operation(request: Request, unsupported: str) -> None:
    if unsupported in _ZARINPAL_OPERATIONS:
        raise ApiError(
            ErrorCode.unsupported_operation,
            "Method not allowed for this operation",
            status=405,
        )
    raise base_unsupported("zarinpal", f"/zarinpal/{unsupported}")
