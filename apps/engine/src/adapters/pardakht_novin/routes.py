"""Pardakht Novin (PNA) emulated routes (T021) — contracts/adapter-surfaces.md §2.2."""

from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import STAGE_NOTIFY, STAGE_SETTLE
from src.adapters.checkout_flow import apply_checkout_action
from src.adapters.pardakht_novin.adapter import PardakhtNovinAdapter
from src.adapters.soap import (
    SOAP_CONTENT_TYPE,
    MalformedEnvelope,
    envelope,
    malformed_fault,
    parse_body,
    wsdl_file_response,
)
from src.api.db import get_session
from src.api.errors import not_found
from src.api.routes import current_project
from src.checkout.page import render_auto_submit_post_form
from src.models import AdapterConfig, Project, Provider, TransactionStatus
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/pardakht_novin", tags=["pardakht_novin"])
WSDL_PATH = Path(__file__).parent / "pardakht_novin.wsdl"


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> PardakhtNovinAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.pardakht_novin,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("pardakht_novin adapter")
    return PardakhtNovinAdapter(config)


@router.post("/GenerateToken")
async def generate_token(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[PardakhtNovinAdapter, Depends(get_adapter)],
) -> JSONResponse:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        body = await request.body()
        parsed = parse_qs(body.decode("utf-8"))
        payload = {k: v[0] for k, v in parsed.items()}

    amount = int(payload.get("Amount") or payload.get("amount") or 0)
    order_id = str(payload.get("OrderId") or payload.get("orderId") or "")
    cb_url = str(payload.get("CallbackUrl") or payload.get("callbackUrl") or "")

    tx = await transactions.initiate(
        session,
        project,
        adapter.config,
        amount_rial=amount,
        app_reference=order_id,
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
    adapter: Annotated[PardakhtNovinAdapter, Depends(get_adapter)],
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
    adapter: Annotated[PardakhtNovinAdapter, Depends(get_adapter)],
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
async def services_wsdl(request: Request) -> Response:
    return wsdl_file_response(WSDL_PATH, request)


@router.post("/Verify")
async def verify(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[PardakhtNovinAdapter, Depends(get_adapter)],
) -> Response:
    content_type = request.headers.get("content-type", "")
    if "xml" in content_type:
        raw_body = await request.body()
        try:
            op_name, params = parse_body(raw_body)
        except MalformedEnvelope:
            return malformed_fault()

        ref_num = params.get("RefNum") or params.get("Token") or ""
        tx = await transactions.load_by_authority(session, project, ref_num)
        resp = await adapter.verify(tx, params)
        tx.raw_response = resp
        await session.commit()

        if tx.status == TransactionStatus.settled:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
        elif tx.status == TransactionStatus.declined:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

        body = (
            '    <VerifyResponse xmlns="http://pna.shaparak.ir/services">\n'
            f"      <Result>{resp.get('Result', '0')}</Result>\n"
            f"      <Amount>{resp.get('Amount', tx.amount_rial)}</Amount>\n"
            "    </VerifyResponse>"
        )
        return Response(content=envelope(body), media_type=SOAP_CONTENT_TYPE)

    payload = await request.json()
    ref_num = payload.get("RefNum") or payload.get("Token") or ""
    tx = await transactions.load_by_authority(session, project, ref_num)
    resp = await adapter.verify(tx, payload)
    tx.raw_response = resp
    await session.commit()

    if tx.status == TransactionStatus.settled:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
    elif tx.status == TransactionStatus.declined:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

    return JSONResponse(content=resp)
