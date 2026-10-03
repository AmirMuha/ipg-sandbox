"""GET /api/v1/transactions search, filter and pagination tests (T017, US3).

Everything here is about one thing: a user with 200 transactions needs to find the one they
are looking at, and the counts they see have to agree with the rows they get.
"""

import time

from fastapi.testclient import TestClient


def _seed(client: TestClient, **overrides) -> str:
    resp = client.post(
        "/api/v1/transactions/simulate",
        json={"adapter": "zarinpal", "amount_rial": 1_000_000, **overrides},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["transaction"]["id"]


def _list(client: TestClient, **params) -> dict:
    resp = client.get("/api/v1/transactions", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_search_matches_app_reference(client: TestClient):
    _seed(client, app_reference="ORD-9401")
    _seed(client, app_reference="ORD-1234")

    data = _list(client, q="ORD-9401")
    assert data["total"] == 1
    assert data["items"][0]["app_reference"] == "ORD-9401"


def test_search_matches_authority_and_description(client: TestClient):
    authority = _seed(client, description="Premium Plan")
    _seed(client, description="Basic Plan")

    assert _list(client, q=authority)["total"] == 0  # ids are uuids, not authorities
    assert _list(client, q="Premium")["total"] == 1
    assert _list(client, q="premium")["total"] == 1  # case-insensitive


def test_search_with_no_match_returns_empty_page_not_error(client: TestClient):
    _seed(client, app_reference="ORD-1")

    data = _list(client, q="nothing-matches-this")
    assert data["total"] == 0
    assert data["items"] == []
    assert data["total_pages"] == 0


def test_like_wildcards_in_search_are_escaped(client: TestClient):
    """A literal `%` must not turn into "match everything"."""
    _seed(client, app_reference="ORD-1")
    _seed(client, app_reference="ORDX1")

    # `_` is a single-char wildcard in SQL LIKE; unescaped it would match ORD-1 via ORDX1.
    assert _list(client, q="ORD_1")["total"] == 0
    assert _list(client, q="ORD-1")["total"] == 1


def test_status_filter(client: TestClient):
    _seed(client, forced_scenario="approve", auto_complete=True)
    _seed(client, forced_scenario="approve")

    assert _list(client, status="settled")["total"] == 1
    assert _list(client, status="initiated")["total"] == 1


def test_adapter_filter(client: TestClient):
    _seed(client, adapter="zarinpal")
    _seed(client, adapter="idpay")

    data = _list(client, adapter="idpay")
    assert data["total"] == 1


def test_status_and_adapter_filters_combine(client: TestClient):
    _seed(client, adapter="zarinpal", forced_scenario="approve", auto_complete=True)
    _seed(client, adapter="zarinpal")
    _seed(client, adapter="idpay", forced_scenario="approve", auto_complete=True)

    assert _list(client, adapter="zarinpal", status="settled")["total"] == 1
    assert _list(client, adapter="zarinpal")["total"] == 2


def test_date_range_filter(client: TestClient):
    _seed(client, app_reference="OLD")
    row = _seed(client, app_reference="NEW")

    created = _list(client)["items"][0]["created_at"]

    from_now = _list(client, from_date=created)
    assert from_now["total"] == 1
    assert from_now["items"][0]["app_reference"] == "NEW"

    until_then = _list(client, to_date=created)
    assert until_then["total"] == 2  # both share a timestamp at second granularity
    assert row


def test_pagination_reports_total_pages(client: TestClient):
    for i in range(25):
        _seed(client, app_reference=f"ORD-{i}")

    first = _list(client, page=1, page_size=10)
    assert first["total"] == 25
    assert first["total_pages"] == 3
    assert len(first["items"]) == 10
    assert first["page"] == 1

    last = _list(client, page=3, page_size=10)
    assert len(last["items"]) == 5


def test_past_the_last_page_is_empty_not_an_error(client: TestClient):
    _seed(client)

    data = _list(client, page=99, page_size=10)
    assert data["items"] == []
    assert data["total"] == 1  # the count is of matches, not of the page returned


def test_filters_apply_before_pagination(client: TestClient):
    """`total` must count the filtered set, or the page count lies."""
    _seed(client, app_reference="KEEP-1", adapter="zarinpal")
    _seed(client, app_reference="KEEP-2", adapter="zarinpal")
    _seed(client, app_reference="DROP-1", adapter="idpay")

    data = _list(client, q="KEEP", page_size=1)
    assert data["total"] == 2
    assert data["total_pages"] == 2
    assert len(data["items"]) == 1


def test_invalid_page_is_rejected(client: TestClient):
    resp = client.get("/api/v1/transactions", params={"page": 0})
    assert resp.status_code == 422

    resp = client.get("/api/v1/transactions", params={"page_size": 500})
    assert resp.status_code == 422


def test_delete_removes_the_transaction_and_its_deliveries(client: TestClient):
    """US5: purging a record must not leave orphaned delivery logs behind."""
    tx_id = _seed(
        client,
        forced_scenario="approve",
        auto_complete=True,
        callback_url="http://localhost:9/hook",
    )
    # Delivery is fire-and-forget, so the row may not exist the instant simulate returns.
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        deliveries = client.get("/api/v1/deliveries", params={"transaction_id": tx_id}).json()
        if deliveries["total"]:
            break
        time.sleep(0.05)
    assert deliveries["total"] >= 1

    resp = client.delete(f"/api/v1/transactions/{tx_id}")

    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    assert resp.json()["id"] == tx_id
    assert client.get(f"/api/v1/transactions/{tx_id}").status_code == 404
    # The cascade: no delivery row may outlive its transaction.
    assert client.get("/api/v1/deliveries", params={"transaction_id": tx_id}).json()["total"] == 0


def test_deleting_an_unknown_transaction_is_404(client: TestClient):
    import uuid

    resp = client.delete(f"/api/v1/transactions/{uuid.uuid4()}")
    assert resp.status_code == 404
