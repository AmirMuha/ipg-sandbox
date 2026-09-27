"""T007 spike (research R4): hand-authored Behpardakht WSDL is loadable and usable by a real client.

Exit criteria: a reference `zeep` client loads the WSDL, constructs requests for
`bpPaymentRequest` / `bpPaymentVerification`, and deserializes responses.

ponytail: transport stubbed with a canned SOAP reply — this spike tests the WSDL, not the
not-yet-built server (T023). The canned success body is correct for the client's own request, so it
is not a fake pass. Schema content is asserted directly because zeep does not type-check scalars.
"""

from pathlib import Path

import pytest
from requests import Response
from zeep import Client
from zeep.exceptions import ValidationError

WSDL = Path(__file__).parents[2] / "src" / "adapters" / "behpardakht" / "behpardakht.wsdl"

REQUEST = {
    "terminalId": 123456,
    "userName": "sandbox",
    "userPassword": "sandbox",
    "orderId": 1001,
    "amount": 50000,
    "localDate": "20260924",
    "localTime": "120000",
    "additionalData": "",
    "callBackUrl": "http://localhost:3000/callback",
    "payerId": 0,
}

VERIFY = {
    "terminalId": 123456,
    "userName": "sandbox",
    "userPassword": "sandbox",
    "orderId": 1001,
    "saleOrderId": 1001,
    "saleReferenceId": 987654,
}


_ENVELOPE = (
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
    "<soapenv:Body>{}</soapenv:Body></soapenv:Envelope>"
)


class _StubTransport:
    """Stands in for a live endpoint: returns a canned reply for the request just serialized."""

    def __init__(self, payload: str):
        self.body = _ENVELOPE.format(payload)
        self.envelopes = []

    def post_xml(self, address, envelope, headers):
        from zeep.wsdl.utils import etree_to_string

        self.envelopes.append(etree_to_string(envelope))
        response = Response()
        response.status_code = 200
        response._content = self.body.encode()
        response.headers["Content-Type"] = "text/xml; charset=utf-8"
        return response


def _client(body: str) -> tuple[Client, _StubTransport]:
    client = Client(str(WSDL))
    transport = _StubTransport(body)
    client.transport = transport
    client.settings.raw_response = False
    return client, transport


def test_wsdl_loads_with_exactly_the_in_scope_operations():
    """Fails if the WSDL loses an operation or grows one outside the documented subset."""
    client = Client(str(WSDL))
    in_scope = {
        "bpPaymentRequest",
        "bpPaymentVerification",
        "bpReverseTransaction",
    }
    assert set(client.service._operations) == in_scope
    # The portType is checked too: an operation declared there but not bound is still out of scope.
    for port_type in client.wsdl.port_types.values():
        assert set(port_type.operations) == in_scope
    assert (
        client.service._binding_options["address"]
        == "http://localhost:8080/behpardakht/MellatPaymentGateway"
    )


def test_schema_keeps_in_scope_signatures():
    """Guards the declared request/response types, which zeep does not enforce on scalars.

    Without this, widening e.g. `amount` from xsd:long to xsd:string would leave every other
    test green while silently changing what the endpoint accepts.
    """
    client = Client(str(WSDL))
    ns = "http://interfaces.core.sw.bps.com/"

    def fields(element_name):
        elements = client.get_element(f"{{{ns}}}{element_name}").type.elements
        assert all(not child.is_optional for _, child in elements), element_name
        return [(name, child.type.name) for name, child in elements]

    assert fields("bpPaymentRequest") == [
        ("terminalId", "long"),
        ("userName", "string"),
        ("userPassword", "string"),
        ("orderId", "long"),
        ("amount", "long"),
        ("localDate", "string"),
        ("localTime", "string"),
        ("additionalData", "string"),
        ("callBackUrl", "string"),
        ("payerId", "long"),
    ]
    verify_fields = [
        ("terminalId", "long"),
        ("userName", "string"),
        ("userPassword", "string"),
        ("orderId", "long"),
        ("saleOrderId", "long"),
        ("saleReferenceId", "long"),
    ]
    assert fields("bpPaymentVerification") == verify_fields
    assert fields("bpReverseTransaction") == verify_fields
    assert fields("bpPaymentRequestResponse") == [
        ("ResCode", "int"),
        ("RefId", "string"),
        ("RedirectUrl", "string"),
    ]
    assert fields("bpPaymentVerificationResponse") == [("ResCode", "int")]
    assert fields("bpReverseTransactionResponse") == [("ResCode", "int")]


def test_payment_request_constructs_and_parses_response():
    client, transport = _client(
        '<bpPaymentRequestResponse xmlns="http://interfaces.core.sw.bps.com/">'
        "<ResCode>0</ResCode><RefId>REF-778899</RefId>"
        "<RedirectUrl>http://localhost:8080/behpardakht/checkout/REF-778899</RedirectUrl>"
        "</bpPaymentRequestResponse>"
    )

    result = client.service.bpPaymentRequest(**REQUEST)

    # Multi-field response type -> object with attributes.
    assert result.ResCode == 0
    assert result.RefId == "REF-778899"
    assert result.RedirectUrl.endswith("/checkout/REF-778899")
    sent = transport.envelopes[0]
    for field in REQUEST:
        assert field.encode() in sent, field
    assert b"amount>50000<" in sent


def test_payment_verification_constructs_and_parses_response():
    client, transport = _client(
        '<bpPaymentVerificationResponse xmlns="http://interfaces.core.sw.bps.com/">'
        "<ResCode>0</ResCode></bpPaymentVerificationResponse>"
    )

    result = client.service.bpPaymentVerification(**VERIFY)

    # Single-element response type -> zeep collapses it to the bare value.
    assert result == 0
    sent = transport.envelopes[0]
    for field in VERIFY:
        assert field.encode() in sent, field


def test_reverse_transaction_constructs_and_parses_response():
    client, transport = _client(
        '<bpReverseTransactionResponse xmlns="http://interfaces.core.sw.bps.com/">'
        "<ResCode>0</ResCode></bpReverseTransactionResponse>"
    )

    result = client.service.bpReverseTransaction(**VERIFY)

    assert result == 0
    assert b"saleReferenceId>987654<" in transport.envelopes[0]


def test_required_request_fields_are_enforced():
    """A request type accepting a partial message would mean the schema lost its elements."""
    client = Client(str(WSDL))
    with pytest.raises(ValidationError):
        client.service.bpPaymentRequest(terminalId=123456, userName="sandbox")
