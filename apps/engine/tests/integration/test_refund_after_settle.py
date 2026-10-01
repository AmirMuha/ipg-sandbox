"""T079: post-settle refund on the normal approve path, for all three adapters.

The existing refund coverage forces `X-Sandbox-Scenario: refund`, which parks the row in
`approved` — the one edge the state machine already allowed. The ordinary
`approve -> checkout -> verify -> settle -> refund` path was never exercised, which is why the
missing `settled -> refunded` edge shipped: IDPay and Behpardakht returned HTTP 500
(`illegal transaction transition`) and Zarinpal refused with `code -50` at HTTP 200.

contracts/adapter-surfaces.md calls refund "post-settle", so a plain approve flow must be
refundable. These tests drive exactly that.
"""

import pytest

from tests.contract.test_behpardakht_surface import _get_zeep_client

# (initiate path, confirm template, verify path, refund path, authority field, success predicate)
ADAPTERS = [
    pytest.param(
        "/zarinpal/request/payment",
        "/zarinpal/checkout/{ref}",
        "/zarinpal/payment/verification",
        "/zarinpal/payment/refund",
        "authority",
        lambda body: body.get("code") == 100,
        id="zarinpal",
    ),
    pytest.param(
        "/idpay/payment",
        "/idpay/payment/start/{ref}",
        "/idpay/payment/verify",
        "/idpay/payment/refund",
        "id",
        lambda body: body.get("status") == 200,
        id="idpay",
    ),
    pytest.param(
        None,  # Behpardakht is SOAP; driven separately below
        None,
        None,
        None,
        None,
        None,
        id="behpardakht-soap",
    ),
]


def _settle(client, initiate_path, confirm_template, verify_path, id_field):
    """Drive initiate -> checkout confirm -> verify. Returns the transaction id."""
    # T080 validates credential *values*, so these must carry the fixture's configured ones.
    init = client.post(
        initiate_path,
        headers={"X-API-KEY": "test-idpay-key"},
        json={
            "merchant_id": "test-merchant",
            "amount": 50000,
            "currency": "IRR",
            "order_id": "t079",
        },
    )
    assert init.status_code == 200, init.text
    ref = init.json()[id_field]

    client.post(confirm_template.format(ref=ref), data={"action": "confirm"})

    verify = client.post(verify_path, json={id_field: ref})
    assert verify.status_code == 200, verify.text
    return ref


@pytest.mark.parametrize(
    "initiate_path,confirm_template,verify_path,refund_path,id_field,is_success",
    ADAPTERS[:2],
)
def test_refund_after_settle_succeeds(
    client, initiate_path, confirm_template, verify_path, refund_path, id_field, is_success
):
    """A settled transaction refunds successfully instead of erroring."""
    ref = _settle(client, initiate_path, confirm_template, verify_path, id_field)

    resp = client.post(refund_path, json={id_field: ref})

    assert resp.status_code == 200, resp.text
    assert is_success(resp.json()), resp.text


@pytest.mark.parametrize(
    "initiate_path,confirm_template,verify_path,refund_path,id_field,is_success",
    ADAPTERS[:2],
)
def test_refund_marks_transaction_refunded(
    client, initiate_path, confirm_template, verify_path, refund_path, id_field, is_success
):
    """The row ends `refunded` — the transition is persisted, not just answered."""
    ref = _settle(client, initiate_path, confirm_template, verify_path, id_field)

    client.post(refund_path, json={id_field: ref})

    items = client.get("/api/v1/transactions").json()["items"]
    match = [t for t in items if (t.get("authority") == ref or t.get("id") == ref)]
    assert match, f"transaction {ref} not found in list"
    assert match[0]["status"] == "refunded"


@pytest.mark.parametrize(
    "initiate_path,confirm_template,verify_path,refund_path,id_field,is_success",
    ADAPTERS[:2],
)
def test_refund_is_not_replayable(
    client, initiate_path, confirm_template, verify_path, refund_path, id_field, is_success
):
    """A second refund on an already-refunded row is rejected, not silently re-applied."""
    ref = _settle(client, initiate_path, confirm_template, verify_path, id_field)
    assert is_success(client.post(refund_path, json={id_field: ref}).json())

    second = client.post(refund_path, json={id_field: ref})

    # Refused, but never as a 500 — the envelope still parses.
    assert second.status_code < 500, second.text
    assert not is_success(second.json()), second.text


def test_refunding_an_unsettled_transaction_is_rejected(client):
    """Refunding straight after initiate (still `initiated`) must not crash or succeed."""
    init = client.post(
        "/zarinpal/request/payment",
        json={"merchant_id": "test-merchant", "amount": 1000, "currency": "IRR"},
    )
    ref = init.json()["authority"]

    resp = client.post("/zarinpal/payment/refund", json={"authority": ref})

    assert resp.status_code < 500, resp.text
    assert resp.json().get("code") == -50


def test_behpardakht_soap_refund_after_settle(client):
    """Behpardakht over SOAP: `bpReverseTransaction` on a settled (not refund-scenario) row.

    The SOAP surface has no scenario header on the reverse call, so this drives the real client.
    A plain approve flow must reverse; before T079 this hit
    `illegal transaction transition 'settled' -> 'refunded'` and returned ResCode 45.
    """
    zeep = _get_zeep_client(client)

    init = zeep.service.bpPaymentRequest(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=7901,
        amount=200000,
        localDate="20261001",
        localTime="120000",
        additionalData="",
        callBackUrl="http://localhost:3000/callback",
        payerId=0,
    )
    assert init.ResCode == 0
    ref_id = init.RefId

    client.post(
        f"/behpardakht/checkout/{ref_id}",
        data={"action": "confirm"},
        follow_redirects=False,
    )

    verify = zeep.service.bpPaymentVerification(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=7901,
        saleOrderId=7901,
        saleReferenceId=int(ref_id),
    )
    assert verify == 0, "verification must settle before the refund is attempted"

    reverse = zeep.service.bpReverseTransaction(
        terminalId=123456,
        userName="sandbox",
        userPassword="sandbox",
        orderId=7901,
        saleOrderId=7901,
        saleReferenceId=int(ref_id),
    )

    assert reverse == 0, f"post-settle reverse failed with ResCode {reverse}"

    items = client.get("/api/v1/transactions").json()["items"]
    match = [t for t in items if t.get("authority") == ref_id]
    assert match and match[0]["status"] == "refunded"


# --- T076: the abandoned-checkout edge case --------------------------------------------------
# spec.md:111 — "Checkout page abandoned (user never returns) → transaction remains
# pending/open and is distinguishable from settled or expired transactions."
#
# contracts/adapter-surfaces.md:60 says abandon leaves "pending → expired per edge case", which
# cannot be reconciled with the spec sentence above. T082 records that contradiction; these
# tests pin the behaviour that is actually implemented so the decision has something to change.


@pytest.mark.parametrize(
    "initiate_path,confirm_template,id_field,cancel_marker",
    [
        pytest.param(
            "/zarinpal/request/payment",
            "/zarinpal/checkout/{ref}",
            "authority",
            "CANCELLED",
            id="zarinpal",
        ),
        # IDPay's real gateway signals cancellation as `status=2`, not a CANCELLED literal.
        pytest.param("/idpay/payment", "/idpay/payment/start/{ref}", "id", "status=2", id="idpay"),
    ],
)
def test_abandon_checkout_expires_and_is_distinguishable(
    client, initiate_path, confirm_template, id_field, cancel_marker
):
    """Abandoning checkout drives the row to `expired` and redirects with the cancel signal."""
    init = client.post(
        initiate_path,
        headers={"X-API-KEY": "test-idpay-key"},
        json={
            "merchant_id": "test-merchant",
            "amount": 7000,
            "currency": "IRR",
            "order_id": "t076",
        },
    )
    ref = init.json()[id_field]

    resp = client.post(
        confirm_template.format(ref=ref), data={"action": "abandon"}, follow_redirects=False
    )

    assert resp.status_code == 302
    assert cancel_marker in resp.headers["location"]

    items = client.get("/api/v1/transactions").json()["items"]
    match = [t for t in items if (t.get("authority") == ref or t.get("id") == ref)]
    assert match, f"transaction {ref} not found"
    assert match[0]["status"] == "expired"


def test_abandoned_checkout_is_not_settled_or_declined(client):
    """The row must be distinguishable from the other terminal outcomes (spec.md:111)."""
    init = client.post(
        "/zarinpal/request/payment",
        json={"merchant_id": "test-merchant", "amount": 8000, "currency": "IRR"},
    )
    ref = init.json()["authority"]
    client.post(f"/zarinpal/checkout/{ref}", data={"action": "abandon"}, follow_redirects=False)

    items = client.get("/api/v1/transactions").json()["items"]
    status = next(t["status"] for t in items if t.get("authority") == ref)

    assert status not in ("settled", "declined", "refunded", "failed")


def test_never_returned_checkout_stays_pending_or_open(client):
    """A checkout the user never completes must not silently settle or disappear.

    There is no expiry sweep for a row still in `initiated` (the scheduler only handles
    `pending` with a `due_at`), so the row simply remains open and inspectable.
    """
    init = client.post(
        "/zarinpal/request/payment",
        json={"merchant_id": "test-merchant", "amount": 9000, "currency": "IRR"},
    )
    ref = init.json()["authority"]

    items = client.get("/api/v1/transactions").json()["items"]
    match = [t for t in items if t.get("authority") == ref]

    assert match, "an abandoned checkout left no trace at all"
    assert match[0]["status"] == "initiated"
