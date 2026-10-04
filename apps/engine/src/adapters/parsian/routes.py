"""Parsian PEC emulated routes (T013) — contracts/adapter-surfaces.md §1.3."""

from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import STAGE_NOTIFY, STAGE_REFUND, STAGE_SETTLE
from src.adapters.checkout_flow import apply_checkout_action
from src.adapters.parsian.adapter import ParsianAdapter
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
from src.api.errors import not_found
from src.api.routes import current_project
from src.checkout.page import render_auto_submit_post_form
from src.models import AdapterConfig, Project, Provider, TransactionStatus
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/parsian", tags=["parsian"])
WSDL_PATH = Path(__file__).parent / "parsian.wsdl"


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> ParsianAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.parsian,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("parsian adapter")
    return ParsianAdapter(config)


@router.get("/EShopService.asmx")
async def eshop_wsdl(request: Request) -> Response:
    return wsdl_file_response(WSDL_PATH, request)


@router.post("/EShopService.asmx")
async def eshop_soap(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[ParsianAdapter, Depends(get_adapter)],
) -> Response:
    raw = await request.body()
    try:
        op_name, params = parse_body(raw)
    except MalformedEnvelope:
        return malformed_fault()

    if op_name == "SalePaymentRequest":
        amount = int(params.get("Amount", "0") or "0")
        order_id = str(params.get("OrderId", "") or "")
        cb = str(params.get("ReffererAddress", "") or "")
        tx = await transactions.initiate(
            session,
            project,
            adapter.config,
            amount_rial=amount,
            app_reference=order_id,
            callback_url=cb,
            raw_request=params,
        )
        resp = await adapter.create_payment(tx, params)
        tx.raw_response = resp
        await session.commit()

        body = (
            '    <SalePaymentRequestResponse xmlns="https://pec.shaparak.ir/pecpaymentgateway/">\n'
            "      <SalePaymentRequestResult>\n"
            f"        <Token>{resp['Token']}</Token>\n"
            f"        <Status>{resp['Status']}</Status>\n"
            "      </SalePaymentRequestResult>\n"
            "    </SalePaymentRequestResponse>"
        )
        return Response(content=envelope(body), media_type=SOAP_CONTENT_TYPE)

    elif op_name == "ConfirmPayment":
        token = str(params.get("Token", "") or "")
        tx = await transactions.load_by_authority(session, project, token)
        resp = await adapter.verify(tx, params)
        tx.raw_response = resp
        await session.commit()

        if tx.status == TransactionStatus.settled:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
        elif tx.status == TransactionStatus.declined:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

        body = (
            '    <ConfirmPaymentResponse xmlns="https://pec.shaparak.ir/pecpaymentgateway/">\n'
            "      <ConfirmPaymentResult>\n"
            f"        <Status>{resp['Status']}</Status>\n"
            f"        <RRN>{resp['RRN']}</RRN>\n"
            f"        <CardNumberMasked>{resp['CardNumberMasked']}</CardNumberMasked>\n"
            "      </ConfirmPaymentResult>\n"
            "    </ConfirmPaymentResponse>"
        )
        return Response(content=envelope(body), media_type=SOAP_CONTENT_TYPE)

    elif op_name == "ReversalProcess":
        token = str(params.get("Token", "") or "")
        tx = await transactions.load_by_authority(session, project, token)
        resp = await adapter.refund(tx, params)
        tx.raw_response = resp
        await session.commit()

        if tx.status == TransactionStatus.refunded:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_REFUND)

        body = (
            '    <ReversalProcessResponse xmlns="https://pec.shaparak.ir/pecpaymentgateway/">\n'
            "      <ReversalProcessResult>\n"
            f"        <Status>{resp['Status']}</Status>\n"
            "      </ReversalProcessResult>\n"
            "    </ReversalProcessResponse>"
        )
        return Response(content=envelope(body), media_type=SOAP_CONTENT_TYPE)

    return fault(op_name or "Unknown")


@router.get("/checkout/{token}", response_class=HTMLResponse)
async def checkout_view(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[ParsianAdapter, Depends(get_adapter)],
    lang: str = "fa",
) -> HTMLResponse:
    tx = await transactions.load_by_authority(session, project, token)
    html = await adapter.checkout_page(tx, lang=lang)
    return HTMLResponse(content=html)


@router.post("/payment")
async def payment_post_entry(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[ParsianAdapter, Depends(get_adapter)],
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
    adapter: Annotated[ParsianAdapter, Depends(get_adapter)],
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
