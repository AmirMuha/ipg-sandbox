"""Saman SEP emulated routes (T009) — contracts/adapter-surfaces.md §1.1."""

from pathlib import Path
from typing import Annotated, Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import STAGE_NOTIFY, STAGE_REFUND, STAGE_SETTLE
from src.adapters.checkout_flow import apply_checkout_action
from src.adapters.saman.adapter import SamanAdapter
from src.adapters.soap import (
    SOAP_CONTENT_TYPE,
    MalformedEnvelope,
    envelope,
    fault,
    malformed_fault,
    parse_body,
    wsdl_file_response,
)
from src.api.db import get_session
from src.api.errors import ApiError, not_found
from src.api.routes import current_project
from src.checkout.page import render_auto_submit_post_form
from src.models import AdapterConfig, Project, Provider, Transaction, TransactionStatus
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/saman", tags=["saman"])
WSDL_PATH = Path(__file__).parent / "saman.wsdl"


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> SamanAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.saman,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("saman adapter")
    return SamanAdapter(config)


@router.post("/onlinepg/onlinepg")
async def initiate_token(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SamanAdapter, Depends(get_adapter)],
) -> JSONResponse:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        body = await request.body()
        parsed = parse_qs(body.decode("utf-8"))
        payload = {k: v[0] for k, v in parsed.items()}

    amount = int(payload.get("Amount") or payload.get("amount") or 0)
    res_num = str(payload.get("ResNum") or payload.get("resNum") or "")
    redirect_url = str(payload.get("RedirectUrl") or payload.get("redirectUrl") or "")

    tx = await transactions.initiate(
        session,
        project,
        adapter.config,
        amount_rial=amount,
        app_reference=res_num,
        callback_url=redirect_url,
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
    adapter: Annotated[SamanAdapter, Depends(get_adapter)],
    lang: str = "fa",
) -> HTMLResponse:
    tx = await transactions.load_by_authority(session, project, token)
    html = await adapter.checkout_page(tx, lang=lang)
    return HTMLResponse(content=html)


@router.post("/onlinepg/payment")
async def payment_post_entry(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SamanAdapter, Depends(get_adapter)],
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
    adapter: Annotated[SamanAdapter, Depends(get_adapter)],
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


@router.get("/verifyTxn")
async def verify_wsdl(request: Request) -> Response:
    return wsdl_file_response(WSDL_PATH, request)


@router.get("/service")
async def service_wsdl(request: Request) -> Response:
    return wsdl_file_response(WSDL_PATH, request)


@router.post("/verifyTxn")
async def verify_txn(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SamanAdapter, Depends(get_adapter)],
) -> Response:
    content_type = request.headers.get("content-type", "")
    if "xml" in content_type:
        raw_body = await request.body()
        try:
            op_name, params = parse_body(raw_body)
        except MalformedEnvelope:
            return malformed_fault()

        ref_num = params.get("RefNum") or params.get("refNum") or ""
        tx = await transactions.load_by_authority(session, project, ref_num)
        resp_data = await adapter.verify(tx, params)
        tx.raw_response = resp_data
        await session.commit()

        if tx.status == TransactionStatus.settled:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
        elif tx.status == TransactionStatus.declined:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

        result_code = resp_data.get("ResultCode", 0)
        soap_resp = (
            f"    <verifyTransactionResponse xmlns=\"urn:InitPaymentGateway\">\n"
            f"      <Result>{result_code}</Result>\n"
            f"    </verifyTransactionResponse>"
        )
        return Response(content=envelope(soap_resp), media_type=SOAP_CONTENT_TYPE)

    payload = await request.json()
    ref_num = payload.get("RefNum") or payload.get("refNum") or ""
    tx = await transactions.load_by_authority(session, project, ref_num)
    resp_data = await adapter.verify(tx, payload)
    tx.raw_response = resp_data
    await session.commit()

    if tx.status == TransactionStatus.settled:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
    elif tx.status == TransactionStatus.declined:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

    return JSONResponse(content=resp_data)


@router.post("/reverseTxn")
async def reverse_txn(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[SamanAdapter, Depends(get_adapter)],
) -> Response:
    content_type = request.headers.get("content-type", "")
    if "xml" in content_type:
        raw_body = await request.body()
        try:
            op_name, params = parse_body(raw_body)
        except MalformedEnvelope:
            return malformed_fault()

        ref_num = params.get("RefNum") or params.get("refNum") or ""
        tx = await transactions.load_by_authority(session, project, ref_num)
        resp_data = await adapter.refund(tx, params)
        tx.raw_response = resp_data
        await session.commit()
        if tx.status == TransactionStatus.refunded:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_REFUND)
        soap_resp = (
            f"    <reverseTransactionResponse xmlns=\"urn:InitPaymentGateway\">\n"
            f"      <Result>{resp_data.get('ResultCode', 0)}</Result>\n"
            f"    </reverseTransactionResponse>"
        )
        return Response(content=envelope(soap_resp), media_type=SOAP_CONTENT_TYPE)

    payload = await request.json()
    ref_num = payload.get("RefNum") or payload.get("refNum") or ""
    tx = await transactions.load_by_authority(session, project, ref_num)
    resp_data = await adapter.refund(tx, payload)
    tx.raw_response = resp_data
    await session.commit()
    if tx.status == TransactionStatus.refunded:
        schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_REFUND)
    return JSONResponse(content=resp_data)
