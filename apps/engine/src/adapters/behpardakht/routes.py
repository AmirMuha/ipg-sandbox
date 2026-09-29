"""Behpardakht (Mellat) SOAP routes (T023) — contracts/adapter-surfaces.md §3."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import parse_qs, urlencode

from fastapi import APIRouter, Depends, Header, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import (
    STAGE_NOTIFY,
    STAGE_REFUND,
    STAGE_SETTLE,
)
from src.adapters.behpardakht.adapter import BehpardakhtAdapter
from src.api.db import get_session
from src.api.errors import not_found
from src.api.routes import current_project
from src.models import (
    AdapterConfig,
    Project,
    Provider,
    ScenarioOutcome,
    Transaction,
    TransactionStatus,
)
from src.scenarios.outcomes import (
    apply_initiate_outcome,
    checkout_confirm_status,
    set_due_at,
)
from src.services import transactions
from src.webhooks.worker import schedule_delivery

router = APIRouter(prefix="/behpardakht", tags=["behpardakht"])
WSDL_PATH = Path(__file__).parent / "behpardakht.wsdl"

_SOAP_FAULT = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">\n'
    "  <soapenv:Body>\n"
    "    <soapenv:Fault>\n"
    "      <faultcode>sandbox:UnsupportedOperation</faultcode>\n"
    "      <faultstring>Unsupported operation: {op}</faultstring>\n"
    "    </soapenv:Fault>\n"
    "  </soapenv:Body>\n"
    "</soapenv:Envelope>"
)

_BP_PAY_RESPONSE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">\n'
    "  <soapenv:Body>\n"
    '    <bpPaymentRequestResponse xmlns="http://interfaces.core.sw.bps.com/">\n'
    "      <ResCode>{res_code}</ResCode>\n"
    "      <RefId>{ref_id}</RefId>\n"
    "      <RedirectUrl>{redirect_url}</RedirectUrl>\n"
    "    </bpPaymentRequestResponse>\n"
    "  </soapenv:Body>\n"
    "</soapenv:Envelope>"
)

_BP_VERIFY_RESPONSE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">\n'
    "  <soapenv:Body>\n"
    '    <bpPaymentVerificationResponse xmlns="http://interfaces.core.sw.bps.com/">\n'
    "      <ResCode>{res_code}</ResCode>\n"
    "    </bpPaymentVerificationResponse>\n"
    "  </soapenv:Body>\n"
    "</soapenv:Envelope>"
)

_BP_REVERSE_RESPONSE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">\n'
    "  <soapenv:Body>\n"
    '    <bpReverseTransactionResponse xmlns="http://interfaces.core.sw.bps.com/">\n'
    "      <ResCode>{res_code}</ResCode>\n"
    "    </bpReverseTransactionResponse>\n"
    "  </soapenv:Body>\n"
    "</soapenv:Envelope>"
)


async def get_adapter(
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> BehpardakhtAdapter:
    stmt = select(AdapterConfig).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == Provider.behpardakht,
        AdapterConfig.enabled.is_(True),
    )
    config = await session.scalar(stmt)
    if config is None:
        raise not_found("adapter behpardakht")
    return BehpardakhtAdapter(config)


def _append_query(base_url: str, params: dict[str, Any]) -> str:
    qs = urlencode(params)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{qs}"


def _parse_soap_body(xml_bytes: bytes) -> tuple[str, dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    body = None
    for child in root:
        if child.tag.endswith("Body"):
            body = child
            break
    if body is None or len(body) == 0:
        return "", {}
    op_elem = body[0]
    op_name = op_elem.tag.split("}")[-1] if "}" in op_elem.tag else op_elem.tag
    params = {}
    for param in op_elem:
        name = param.tag.split("}")[-1] if "}" in param.tag else param.tag
        params[name] = param.text or ""
    return op_name, params


@router.get("/MellatPaymentGateway")
async def get_wsdl(request: Request) -> Response:
    if "wsdl" in request.query_params or "WSDL" in request.query_params:
        content = WSDL_PATH.read_text(encoding="utf-8")
        return Response(content=content, media_type="text/xml; charset=utf-8")
    return Response(
        content="<error>Use ?wsdl to view service description</error>",
        media_type="text/xml; charset=utf-8",
        status_code=400,
    )


@router.post("/MellatPaymentGateway")
async def handle_soap(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[BehpardakhtAdapter, Depends(get_adapter)],
    x_sandbox_scenario: Annotated[str | None, Header()] = None,
) -> Response:
    body_bytes = await request.body()
    try:
        op_name, params = _parse_soap_body(body_bytes)
    except Exception:
        fault_xml = _SOAP_FAULT.format(op="MalformedXml")
        return Response(content=fault_xml, status_code=500, media_type="text/xml; charset=utf-8")

    if op_name == "bpPaymentRequest":
        term_id = params.get("terminalId")
        user_name = params.get("userName")
        user_pass = params.get("userPassword")
        amount_str = params.get("amount")

        if not term_id or not user_name or not user_pass:
            resp_xml = _BP_PAY_RESPONSE.format(res_code=21, ref_id="", redirect_url="")
            return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

        if not amount_str or not amount_str.isdigit():
            resp_xml = _BP_PAY_RESPONSE.format(res_code=11, ref_id="", redirect_url="")
            return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

        amount_rial = int(amount_str)
        order_id = params.get("orderId", "")
        call_back_url = params.get("callBackUrl", "")

        tx = await transactions.initiate(
            session,
            project,
            adapter.config,
            amount_rial=amount_rial,
            header=x_sandbox_scenario,
            app_reference=order_id,
            callback_url=call_back_url,
            description=params.get("additionalData", ""),
            currency="IRR",
            raw_request=params,
        )

        if await apply_initiate_outcome(tx, project) is ScenarioOutcome.timeout:
            resp_xml = _BP_PAY_RESPONSE.format(
                res_code=59,
                ref_id="",
                redirect_url="",
            )
            tx.raw_response = {"ResCode": 59, "RefId": "", "RedirectUrl": ""}
            await session.commit()
            return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

        resp_dict = await adapter.create_payment(tx, params)
        tx.raw_response = resp_dict
        await session.commit()

        resp_xml = _BP_PAY_RESPONSE.format(
            res_code=resp_dict["ResCode"],
            ref_id=resp_dict["RefId"],
            redirect_url=resp_dict["RedirectUrl"],
        )
        return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

    elif op_name == "bpPaymentVerification":
        sale_order_id = params.get("saleOrderId", "")
        sale_ref_id = params.get("saleReferenceId", "")
        order_id = params.get("orderId", "")

        # Lookup transaction
        stmt = (
            select(Transaction)
            .where(
                Transaction.project_id == project.id,
                or_(
                    Transaction.authority == sale_ref_id,
                    Transaction.authority == sale_order_id,
                    Transaction.app_reference == order_id,
                    Transaction.app_reference == sale_order_id,
                ),
            )
            .limit(1)
        )
        tx = await session.scalar(stmt)
        if tx is None:
            resp_xml = _BP_VERIFY_RESPONSE.format(res_code=24)
            return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

        resp_dict = await adapter.verify(tx, params)
        tx.raw_response = resp_dict
        await session.commit()
        if tx.status == TransactionStatus.settled:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_SETTLE)
        elif tx.status == TransactionStatus.declined:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_NOTIFY)

        resp_xml = _BP_VERIFY_RESPONSE.format(res_code=resp_dict["ResCode"])
        return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

    elif op_name == "bpReverseTransaction":
        sale_order_id = params.get("saleOrderId", "")
        sale_ref_id = params.get("saleReferenceId", "")
        order_id = params.get("orderId", "")

        stmt = (
            select(Transaction)
            .where(
                Transaction.project_id == project.id,
                or_(
                    Transaction.authority == sale_ref_id,
                    Transaction.authority == sale_order_id,
                    Transaction.app_reference == order_id,
                    Transaction.app_reference == sale_order_id,
                ),
            )
            .limit(1)
        )
        tx = await session.scalar(stmt)
        if tx is None:
            resp_xml = _BP_REVERSE_RESPONSE.format(res_code=24)
            return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

        resp_dict = await adapter.refund(tx, params)
        tx.raw_response = resp_dict
        await session.commit()
        if tx.status == TransactionStatus.refunded:
            schedule_delivery(request.app.state.session_factory, project.id, tx.id, STAGE_REFUND)

        resp_xml = _BP_REVERSE_RESPONSE.format(res_code=resp_dict["ResCode"])
        return Response(content=resp_xml, media_type="text/xml; charset=utf-8")

    # Unsupported operation -> SOAP Fault
    fault_xml = _SOAP_FAULT.format(op=op_name or "Unknown")
    return Response(content=fault_xml, status_code=500, media_type="text/xml; charset=utf-8")


@router.get("/checkout/{ref_id}", response_class=HTMLResponse)
async def checkout_view(
    ref_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
    adapter: Annotated[BehpardakhtAdapter, Depends(get_adapter)],
    lang: str = "fa",
) -> HTMLResponse:
    tx = await transactions.load_by_authority(session, project, ref_id)
    html = await adapter.checkout_page(tx, lang=lang)
    return HTMLResponse(content=html)


@router.post("/checkout/{ref_id}")
async def checkout_action(
    request: Request,
    ref_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    project: Annotated[Project, Depends(current_project)],
) -> RedirectResponse:
    body_bytes = await request.body()
    parsed_form = parse_qs(body_bytes.decode("utf-8"))
    action_list = parsed_form.get("action", ["confirm"])
    action = action_list[0] if action_list else "confirm"

    tx = await transactions.load_by_authority(session, project, ref_id)
    target_url = tx.callback_url or tx.return_url or "/"
    sale_ref_id = 100000 + (tx.amount_rial % 900000)

    if action == "confirm":
        if (target := checkout_confirm_status(tx)) is not None:
            if tx.effective_scenario is ScenarioOutcome.pending_settle:
                set_due_at(tx, project)
            await transactions.advance(session, tx, target)
        res_code = "0"
    elif action == "fail":
        await transactions.advance(session, tx, TransactionStatus.declined)
        res_code = "11"
    else:  # abandon
        await transactions.advance(session, tx, TransactionStatus.pending)
        await transactions.advance(session, tx, TransactionStatus.expired)
        res_code = "17"

    redirect_target = _append_query(
        target_url,
        {
            "ResCode": res_code,
            "RefId": tx.authority,
            "SaleOrderId": tx.app_reference or "",
            "SaleReferenceId": sale_ref_id,
        },
    )
    return RedirectResponse(url=redirect_target, status_code=302)
