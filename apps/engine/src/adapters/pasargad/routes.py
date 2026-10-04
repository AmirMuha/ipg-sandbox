"""Pasargad PEP emulated routes (T015) — contracts/adapter-surfaces.md §1.4."""

from typing import Annotated
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import STAGE_NOTIFY, STAGE_REFUND, STAGE_SETTLE
from src.adapters.checkout_flow import apply_checkout_action
from src.adapters.crypto import verify_rsa
from src.adapters.pasargad.adapter import PasargadAdapter
from src.api.db import get_session
from src.api.errors import ApiError, not_found
from src.api.routes import current_project
from src.checkout.page import render_auto_submit_post_form
from src.models import AdapterConfig, Project, Provider, Transaction, TransactionStatus
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/pasargad", tags=["pasargad"])


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> PasargadAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.pasargad,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("pasargad adapter")
    return PasargadAdapter(config)


@router.post("/api/payment/purchase")
async def purchase(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[PasargadAdapter, Depends(get_adapter)],
) -> JSONResponse:
    payload = await request.json()
    amount = int(payload.get("amount") or 0)
    invoice_no = str(payload.get("invoiceNumber") or "")
    redirect_addr = str(payload.get("redirectAddress") or "")

    # Optional signature verification
    creds = adapter.config.credentials or {}
    public_key = creds.get("public_key")
    if public_key and "sign" in payload:
        raw_to_verify = f"{payload.get('invoiceNumber')}#{payload.get('invoiceDate')}#{amount}"
        if not verify_rsa(public_key, payload["sign"], raw_to_verify):
            return JSONResponse(status_code=400, content={"resultCode": -1, "result": "Invalid signature"})

    tx = await transactions.initiate(
        session,
        project,
        adapter.config,
        amount_rial=amount,
        app_reference=invoice_no,
        callback_url=redirect_addr,
        raw_request=payload,
    )
    resp = await adapter.create_payment(tx, payload)
    tx.raw_response = resp
    await session.commit()
    return JSONResponse(content=resp)


@router.get("/checkout/{token}", response_class=HTMLResponse)
async def checkout_view(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[PasargadAdapter, Depends(get_adapter)],
    lang: str = "fa",
) -> HTMLResponse:
    tx = await transactions.load_by_authority(session, project, token)
    html = await adapter.checkout_page(tx, lang=lang)
    return HTMLResponse(content=html)


@router.post("/checkout/{token}", response_class=HTMLResponse)
async def checkout_action(
    request: Request,
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[PasargadAdapter, Depends(get_adapter)],
) -> HTMLResponse:
    body = await request.body()
    parsed = parse_qs(body.decode("utf-8"))
    action = parsed.get("action", ["confirm"])[0]

    tx = await transactions.load_by_authority(session, project, token)
    await apply_checkout_action(session, tx, project, action)

    callback_url = tx.callback_url or tx.return_url or "/"
    callback_data = adapter.callback_payload("return", tx)

    html = render_auto_submit_post_form(callback_url, callback_data)
    return HTMLResponse(content=html)


@router.post("/api/payment/verify")
async def verify(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[PasargadAdapter, Depends(get_adapter)],
) -> JSONResponse:
    payload = await request.json()
    invoice_no = str(payload.get("invoiceNumber") or "")
    stmt = (
        select(Transaction)
        .where(
            Transaction.project_id == project.id,
            Transaction.app_reference == invoice_no,
        )
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )
    tx = await session.scalar(stmt)
    if tx is None:
        return JSONResponse(status_code=404, content={"resultCode": -1, "result": "Transaction not found"})

    resp = await adapter.verify(tx, payload)
    tx.raw_response = resp
    await session.commit()

    if tx.status == TransactionStatus.settled:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
    elif tx.status == TransactionStatus.declined:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

    return JSONResponse(content=resp)
