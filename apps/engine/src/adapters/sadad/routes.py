"""Sadad Bank Melli emulated routes (T011) — contracts/adapter-surfaces.md §1.2."""

from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import STAGE_NOTIFY, STAGE_REFUND, STAGE_SETTLE
from src.adapters.checkout_flow import apply_checkout_action
from src.adapters.sadad.adapter import SadadAdapter
from src.adapters.soap import wsdl_file_response
from src.api.db import get_session
from src.api.errors import not_found
from src.api.routes import current_project
from src.checkout.page import render_auto_submit_post_form
from src.models import AdapterConfig, Project, Provider, TransactionStatus
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/sadad", tags=["sadad"])
WSDL_PATH = Path(__file__).parent / "sadad.wsdl"


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> SadadAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.sadad,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("sadad adapter")
    return SadadAdapter(config)


@router.post("/api/v0/Request/PaymentRequest")
async def payment_request(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SadadAdapter, Depends(get_adapter)],
) -> JSONResponse:
    payload = await request.json()
    amount = int(payload.get("Amount") or 0)
    order_id = str(payload.get("OrderId") or "")
    return_url = str(payload.get("ReturnUrl") or "")

    tx = await transactions.initiate(
        session,
        project,
        adapter.config,
        amount_rial=amount,
        app_reference=order_id,
        callback_url=return_url,
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
    adapter: Annotated[SadadAdapter, Depends(get_adapter)],
    lang: str = "fa",
) -> HTMLResponse:
    tx = await transactions.load_by_authority(session, project, token)
    html = await adapter.checkout_page(tx, lang=lang)
    return HTMLResponse(content=html)


@router.get("/Purchase", response_class=HTMLResponse)
async def purchase_get_entry(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SadadAdapter, Depends(get_adapter)],
    token: str = "",
    Token: str = "",
) -> HTMLResponse:
    t = token or Token
    tx = await transactions.load_by_authority(session, project, t)
    html = await adapter.checkout_page(tx)
    return HTMLResponse(content=html)


@router.post("/Purchase")
async def purchase_post_entry(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SadadAdapter, Depends(get_adapter)],
) -> HTMLResponse:
    body = await request.body()
    parsed = parse_qs(body.decode("utf-8"))
    token = parsed.get("Token", [""])[0] or parsed.get("token", [""])[0]
    tx = await transactions.load_by_authority(session, project, token)
    html = await adapter.checkout_page(tx)
    return HTMLResponse(content=html)


@router.post("/checkout/{token}", response_class=HTMLResponse)
async def checkout_action(
    request: Request,
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SadadAdapter, Depends(get_adapter)],
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


@router.get("/services")
async def sadad_wsdl(request: Request) -> Response:
    return wsdl_file_response(WSDL_PATH, request)


@router.post("/api/v0/Advice/Verify")
async def verify(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SadadAdapter, Depends(get_adapter)],
) -> JSONResponse:
    payload = await request.json()
    token = payload.get("Token") or payload.get("token") or ""
    tx = await transactions.load_by_authority(session, project, token)
    resp = await adapter.verify(tx, payload)
    tx.raw_response = resp
    await session.commit()

    if tx.status == TransactionStatus.settled:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
    elif tx.status == TransactionStatus.declined:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

    return JSONResponse(content=resp)
