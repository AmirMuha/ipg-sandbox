"""IranKish emulated routes (T023) — contracts/adapter-surfaces.md §2.3."""

from typing import Annotated
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import STAGE_NOTIFY, STAGE_REFUND, STAGE_SETTLE
from src.adapters.checkout_flow import apply_checkout_action
from src.adapters.irankish.adapter import IranKishAdapter
from src.api.db import get_session
from src.api.errors import not_found
from src.api.routes import current_project
from src.checkout.page import render_auto_submit_post_form
from src.models import AdapterConfig, Project, Provider, TransactionStatus
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/irankish", tags=["irankish"])


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> IranKishAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.irankish,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("irankish adapter")
    return IranKishAdapter(config)


@router.post("/api/v1/token")
async def get_token(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[IranKishAdapter, Depends(get_adapter)],
) -> JSONResponse:
    payload = await request.json()
    amount = int(payload.get("amount") or 0)
    req_id = str(payload.get("requestUniqueId") or "")
    cb_url = str(payload.get("revertURL") or "")

    tx = await transactions.initiate(
        session,
        project,
        adapter.config,
        amount_rial=amount,
        app_reference=req_id,
        callback_url=cb_url,
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
    adapter: Annotated[IranKishAdapter, Depends(get_adapter)],
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
    adapter: Annotated[IranKishAdapter, Depends(get_adapter)],
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


@router.post("/api/v1/verify")
async def verify(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[IranKishAdapter, Depends(get_adapter)],
) -> JSONResponse:
    payload = await request.json()
    token = payload.get("token") or ""
    tx = await transactions.load_by_authority(session, project, token)
    resp = await adapter.verify(tx, payload)
    tx.raw_response = resp
    await session.commit()

    if tx.status == TransactionStatus.settled:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
    elif tx.status == TransactionStatus.declined:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

    return JSONResponse(content=resp)
