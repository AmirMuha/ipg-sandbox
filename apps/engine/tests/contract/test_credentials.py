"""T080: credential rejection is consistent — absent, empty and mismatched all fail.

Before this, each route checked only `supplied == ""`, so an omitted credential fell through
as `None` and any value was accepted; a wrong merchant id still created a payment. The spec
edge case (`spec.md:109`) requires a clear error for invalid or unknown credentials.

The fixture configures `merchant_id="test-merchant"` and `api_key="test-idpay-key"`, so those
are the only values that must be accepted.
"""

import pytest


@pytest.mark.parametrize(
    "payload,extra_headers",
    [
        pytest.param({"amount": 1000, "currency": "IRR"}, {}, id="omitted"),
        pytest.param({"merchant_id": "", "amount": 1000, "currency": "IRR"}, {}, id="empty"),
        pytest.param(
            {"merchant_id": "attacker-wrong-merchant", "amount": 1000, "currency": "IRR"},
            {},
            id="mismatched",
        ),
    ],
)
def test_zarinpal_rejects_bad_merchant_id(client, payload, extra_headers):
    resp = client.post("/zarinpal/request/payment", json=payload, headers=extra_headers)

    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "invalid_credentials"


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="omitted"),
        pytest.param({"X-API-KEY": ""}, id="empty"),
        pytest.param({"X-API-KEY": "attacker-wrong-key"}, id="mismatched"),
    ],
)
def test_idpay_rejects_bad_api_key(client, headers):
    resp = client.post(
        "/idpay/payment",
        headers=headers,
        json={"order_id": "cred-check", "amount": 1000},
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "invalid_credentials"


def test_zarinpal_accepts_the_configured_merchant_id(client):
    """The happy path still works — validation must not reject the real credential."""
    resp = client.post(
        "/zarinpal/request/payment",
        json={"merchant_id": "test-merchant", "amount": 1000, "currency": "IRR"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["code"] == 100


def test_idpay_accepts_the_configured_api_key(client):
    resp = client.post(
        "/idpay/payment",
        headers={"X-API-KEY": "test-idpay-key"},
        json={"order_id": "cred-ok", "amount": 1000},
    )

    assert resp.status_code == 200, resp.text
    assert "id" in resp.json()


def test_rejected_credential_creates_no_transaction(client):
    """A 401 must not leave a half-created row behind."""
    before = len(client.get("/api/v1/transactions").json()["items"])

    client.post(
        "/zarinpal/request/payment",
        json={"merchant_id": "attacker-wrong-merchant", "amount": 1000, "currency": "IRR"},
    )

    after = client.get("/api/v1/transactions").json()["items"]
    assert len(after) == before


@pytest.mark.parametrize(
    "path,provider",
    [
        pytest.param("/zarinpal/payment/nonexistent-op", "zarinpal", id="zarinpal"),
        pytest.param("/idpay/nonexistent-op", "idpay", id="idpay"),
    ],
)
def test_unknown_operation_is_explicitly_unsupported(client, path, provider):
    """T081: an operation the adapter does not emulate says so, rather than answering `not_found`.

    `not_found` is indistinguishable from a mistyped URL; the spec and the adapter contract both
    require naming the adapter and the operation.
    """
    resp = client.post(path, json={})

    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert body["code"] == "unsupported_operation"
    assert provider in body["message"]


@pytest.mark.parametrize(
    "path,method",
    [
        pytest.param("/zarinpal/request/payment", "get", id="zarinpal"),
        pytest.param("/idpay/payment", "get", id="idpay"),
    ],
)
def test_wrong_method_on_a_real_operation_still_answers_405(client, path, method):
    """T081 must not swallow the 405 for a real operation reached with the wrong method."""
    resp = getattr(client, method)(path)

    assert resp.status_code == 405, resp.text
    assert resp.json()["code"] == "unsupported_operation"
