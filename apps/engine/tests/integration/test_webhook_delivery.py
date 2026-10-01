"""Webhook delivery integration tests (T036, SC-005, US3 acceptance 1-3).

Tests:
1. Delivery latency < 5s to a live receiver, payload format and delivered status.
2. Unreachable target -> failed rows + retries per project policy, all attempts visible.
3. Filtering and pagination on GET /api/v1/deliveries.
4. Project-level default webhook URL via PUT /api/v1/project/webhook-url.
5. Manual retry via POST /api/v1/deliveries/{id}/retry.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient


class _ReceiverHandler(BaseHTTPRequestHandler):
    hits: list[tuple[str, bytes, float]] = []

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length)
        _ReceiverHandler.hits.append((self.path, body, time.monotonic()))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass  # silence log spam in test output


@pytest.fixture
def receiver():
    """Live HTTP receiver on an ephemeral port."""
    _ReceiverHandler.hits.clear()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ReceiverHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/webhook"
    yield {"url": url, "hits": _ReceiverHandler.hits}
    server.shutdown()
    server.server_close()


def _poll_deliveries(
    client: TestClient, tx_id: str, expected_count: int, timeout_s: float = 3.0
) -> list[dict]:
    """Poll GET /api/v1/deliveries until expected_count rows are no longer pending or timeout."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        items = client.get(f"/api/v1/deliveries?transaction_id={tx_id}").json()["items"]
        if len(items) >= expected_count and all(item["result"] != "pending" for item in items):
            return items
        time.sleep(0.05)
    return client.get(f"/api/v1/deliveries?transaction_id={tx_id}").json()["items"]


def test_delivery_success_and_latency(client: TestClient, receiver):
    """SC-005: Delivery to live receiver succeeds, latency < 5s, payload matches."""
    start_time = time.monotonic()

    # 1. Initiate with callback_url pointing to receiver
    init_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "test-merchant",
            "amount": 50000,
            "callback_url": receiver["url"],
            "return_url": "http://localhost:3000/return",
        },
    )
    authority = init_resp.json()["authority"]

    # 2. Checkout confirm
    client.post(f"/zarinpal/checkout/{authority}", data={"action": "confirm"})

    # 3. Verify -> transitions to settled -> triggers delivery
    verify_resp = client.post(
        "/zarinpal/payment/verification",
        json={"authority": authority},
    )
    assert verify_resp.status_code == 200

    tx_id = client.get("/api/v1/transactions").json()["items"][0]["id"]

    # 4. Wait for delivery
    deliveries = _poll_deliveries(client, tx_id, expected_count=1)
    elapsed = time.monotonic() - start_time

    assert len(deliveries) == 1
    assert deliveries[0]["result"] == "delivered"
    assert deliveries[0]["response_status"] == 200
    assert deliveries[0]["target_url"] == receiver["url"]
    assert deliveries[0]["stage"] == "settle"
    assert elapsed < 5.0  # SC-005 latency budget

    # Receiver received the payload
    assert len(receiver["hits"]) == 1
    received_body = json.loads(receiver["hits"][0][1].decode("utf-8"))
    assert received_body["Status"] == "OK"
    assert received_body["Authority"] == authority
    assert "PaymentID" in received_body


def test_unreachable_target_retries_and_visibility(client: TestClient):
    """US3.2 / SC-005: Unreachable target records failed rows + retries (no silent loss)."""
    # Configure fast zero-delay retries for predictable test execution
    client.patch(
        "/api/v1/project",
        json={"webhook_retry_max": 3, "webhook_retry_backoff_s": [0, 0, 0]},
    )

    dead_url = "http://127.0.0.1:1/unreachable"
    init_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "test-merchant",
            "amount": 30000,
            "callback_url": dead_url,
            "return_url": "http://localhost:3000/return",
        },
    )
    authority = init_resp.json()["authority"]
    client.post(f"/zarinpal/checkout/{authority}", data={"action": "confirm"})
    client.post("/zarinpal/payment/verification", json={"authority": authority})

    tx_id = client.get("/api/v1/transactions").json()["items"][0]["id"]

    # Poll for all 3 attempts
    deliveries = _poll_deliveries(client, tx_id, expected_count=3, timeout_s=4.0)

    assert len(deliveries) == 3
    # Ordered newest first by created_at DESC
    attempts = [d["attempt"] for d in reversed(deliveries)]
    assert attempts == [1, 2, 3]
    for d in deliveries:
        assert d["result"] == "failed"
        assert d["error"] is not None
        assert d["target_url"] == dead_url

    # Check meters
    meters = client.get("/api/v1/meters").json()
    assert meters["webhook_attempts"] >= 3

    # Reset project settings
    client.patch(
        "/api/v1/project",
        json={"webhook_retry_max": 3, "webhook_retry_backoff_s": [1, 2, 4]},
    )


def test_project_default_webhook_url(client: TestClient, receiver):
    """PUT /api/v1/project/webhook-url provides fallback target when tx has no callback_url."""
    # 1. Set project webhook_url
    put_resp = client.put(
        "/api/v1/project/webhook-url",
        json={"webhook_url": receiver["url"]},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["webhook_url"] == receiver["url"]

    # 2. Initiate WITHOUT callback_url
    init_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "test-merchant",
            "amount": 40000,
            "return_url": "http://localhost:3000/return",
        },
    )
    authority = init_resp.json()["authority"]
    client.post(f"/zarinpal/checkout/{authority}", data={"action": "confirm"})
    client.post("/zarinpal/payment/verification", json={"authority": authority})

    tx_id = client.get("/api/v1/transactions").json()["items"][0]["id"]
    deliveries = _poll_deliveries(client, tx_id, expected_count=1)

    assert len(deliveries) == 1
    assert deliveries[0]["result"] == "delivered"
    assert deliveries[0]["target_url"] == receiver["url"]

    # Clear project webhook_url
    client.put("/api/v1/project/webhook-url", json={"webhook_url": None})


def test_manual_retry_endpoint(client: TestClient, receiver):
    """POST /api/v1/deliveries/{id}/retry triggers immediate re-attempt."""
    # 1. Create a failed delivery row pointing to a bad port
    client.patch("/api/v1/project", json={"webhook_retry_max": 1})
    bad_url = "http://127.0.0.1:1/dead"
    init_resp = client.post(
        "/zarinpal/request/payment",
        json={
            "merchant_id": "test-merchant",
            "amount": 60000,
            "callback_url": bad_url,
        },
    )
    authority = init_resp.json()["authority"]
    client.post(f"/zarinpal/checkout/{authority}", data={"action": "confirm"})
    client.post("/zarinpal/payment/verification", json={"authority": authority})

    tx_id = client.get("/api/v1/transactions").json()["items"][0]["id"]
    deliveries = _poll_deliveries(client, tx_id, expected_count=1)
    assert deliveries[0]["result"] == "failed"
    delivery_id = deliveries[0]["id"]

    # 2. Re-point transaction's target by setting project webhook-url, or update tx
    # Note: delivery.target_url is what retry uses
    # Retry against the dead URL will produce another failed row with attempt 2
    retry_resp = client.post(f"/api/v1/deliveries/{delivery_id}/retry")
    assert retry_resp.status_code == 200
    body = retry_resp.json()
    assert body["attempt"] == 2
    assert body["result"] == "failed"

    # Total deliveries for this tx is now 2
    all_d = client.get(f"/api/v1/deliveries?transaction_id={tx_id}").json()["items"]
    assert len(all_d) == 2

    # Reset
    client.patch("/api/v1/project", json={"webhook_retry_max": 3})


def test_deliveries_filtering_and_validation(client: TestClient):
    """Validation errors on deliveries endpoints."""
    # Invalid webhook_url format -> 422
    r1 = client.put("/api/v1/project/webhook-url", json={"webhook_url": "not-a-url"})
    assert r1.status_code == 422
    assert r1.json()["code"] == "validation_error"

    # Missing field -> 422
    r2 = client.put("/api/v1/project/webhook-url", json={})
    assert r2.status_code == 422

    # Non-existent delivery retry -> 404
    missing_id = "00000000-0000-0000-0000-000000000000"
    r3 = client.post(f"/api/v1/deliveries/{missing_id}/retry")
    assert r3.status_code == 404
    assert r3.json()["code"] == "not_found"
