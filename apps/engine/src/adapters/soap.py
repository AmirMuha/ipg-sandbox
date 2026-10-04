"""Shared SOAP surface for the emulated SOAP gateways (FR-002).

Seven gateways speak SOAP/XML rather than JSON (behpardakht, parsian, irankish, fanava, sarmayeh,
and the SOAP legs of saman and asan_pardakht), and all seven need the same four things: parse an
inbound envelope into `(operation, params)`, wrap a response, render a Fault, and serve a WSDL.
`behpardakht` carried its own copy of all four until this module existed.

Parsing uses `defusedxml`, not `xml.etree`, because the request body is attacker-reachable input:
a plain parser expands entity references, which is an XXE/billion-laughs vector on a payments
sandbox that a merchant points real SDK traffic at.
"""

from pathlib import Path

from defusedxml.ElementTree import ParseError, fromstring
from fastapi import Request, Response

#: Every envelope here is SOAP 1.1, matching the hand-authored WSDLs served alongside the routes.
ENVELOPE_OPEN = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">\n'
    "  <soapenv:Body>\n"
)
ENVELOPE_CLOSE = "  </soapenv:Body>\n</soapenv:Envelope>"

SOAP_CONTENT_TYPE = "text/xml; charset=utf-8"


class MalformedEnvelope(ValueError):
    """Inbound body was not a parseable SOAP envelope."""


def _local_name(tag: str) -> str:
    """Strip the `{namespace}` QName prefix the wire always carries."""
    return tag.split("}")[-1] if "}" in tag else tag


def parse_body(raw: bytes) -> tuple[str, dict[str, str]]:
    """Return `(operation_name, {param_name: text})` from a SOAP request body.

    Raises `MalformedEnvelope` when the body is unparseable or carries no `Body` with an
    operation element, so callers answer with a Fault instead of a 500 stack trace.
    """
    try:
        root = fromstring(raw)
    except (ParseError, ValueError) as exc:
        raise MalformedEnvelope(str(exc)) from exc

    body = None
    for child in root:
        if _local_name(child.tag) == "Body":
            body = child
            break
    if body is None or len(body) == 0:
        raise MalformedEnvelope("SOAP Body is missing or empty")

    op_elem = body[0]
    params = {_local_name(p.tag): (p.text or "") for p in op_elem}
    return _local_name(op_elem.tag), params


def envelope(inner: str) -> str:
    """Wrap a gateway-specific response element in a SOAP 1.1 envelope."""
    return f"{ENVELOPE_OPEN}{inner}\n{ENVELOPE_CLOSE}"


def fault(op: str, status: int = 500, *, code: str = "sandbox:UnsupportedOperation") -> Response:
    """Render a SOAP Fault for an operation this adapter does not emulate."""
    body = (
        "    <soapenv:Fault>\n"
        f"      <faultcode>{code}</faultcode>\n"
        f"      <faultstring>Unsupported operation: {op}</faultstring>\n"
        "    </soapenv:Fault>"
    )
    return Response(content=envelope(body), status_code=status, media_type=SOAP_CONTENT_TYPE)


def malformed_fault() -> Response:
    """Render the Fault for an inbound body that would not parse."""
    return fault("MalformedXml", 500, code="soapenv:Client")


def wsdl_file_response(path: Path, request: Request) -> Response:
    """Serve a hand-authored WSDL on `?wsdl`, or explain the endpoint otherwise.

    SOAP clients (`zeep`, PHP `SoapClient`) issue a `GET ?wsdl` when constructed, so answering it
    is what lets a real SDK treat the sandbox as the gateway.
    """
    if "wsdl" in request.query_params or "WSDL" in request.query_params:
        return Response(content=path.read_text(encoding="utf-8"), media_type=SOAP_CONTENT_TYPE)
    return Response(
        content="<error>Use ?wsdl to view service description</error>",
        media_type=SOAP_CONTENT_TYPE,
        status_code=400,
    )
