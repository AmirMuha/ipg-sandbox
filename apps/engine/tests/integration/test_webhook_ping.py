"""POST /api/v1/project/webhook-ping integration tests (T023, US4).

A diagnostic is only useful if a failure is legible: the endpoint must distinguish "your
endpoint is down" from "the engine is down", and must never leave the UI hanging.
"""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient


class _ReceiverHandler(BaseHTTPRequestHandler):
    hits: list[tuple[str, bytes]] = []
    status = 200

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        _ReceiverHandler.hits.append((self.path, self.rfile.read(length)))
        self.send_response(_ReceiverHandler.status)
        self.end_headers()

    def log_message(self, *args):
        pass  # silence log spam in test output


@pytest.fixture
def receiver():
    _ReceiverHandler.hits.clear()
    _ReceiverHandler.status = 200
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ReceiverHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/webhook", _ReceiverHandler.hits
    server.shutdown()
    server.server_close()


def test_ping_reaches_a_live_receiver(client: TestClient, receiver):
    url, hits = receiver

    resp = client.post("/api/v1/project/webhook-ping", json={"target_url": url})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["target_url"] == url
    assert data["status_code"] == 200
    assert data["error"] is None
    assert isinstance(data["latency_ms"], int)

    # It must actually POST a body, not just probe the port.
    assert len(hits) == 1
    assert b"webhook.ping" in hits[0][1]


def test_ping_reports_a_non_2xx_response_as_a_failure(client: TestClient, receiver):
    url, _ = receiver
    _ReceiverHandler.status = 500

    data = client.post("/api/v1/project/webhook-ping", json={"target_url": url}).json()

    assert data["ok"] is False
    assert data["status_code"] == 500
    assert "500" in data["error"]


def test_ping_on_an_unreachable_target_still_returns_200(client: TestClient):
    """A dead endpoint is a diagnosis, not a server error."""
    resp = client.post(
        "/api/v1/project/webhook-ping", json={"target_url": "http://127.0.0.1:9/nope"}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert data["status_code"] is None
    assert data["error"]
    assert data["latency_ms"] < 3000  # gave up at the 3s timeout, not the 5s delivery one


def test_ping_falls_back_to_the_project_webhook_url(client: TestClient, receiver):
    url, hits = receiver
    client.put("/api/v1/project/webhook-url", json={"webhook_url": url})

    data = client.post("/api/v1/project/webhook-ping", json={}).json()

    assert data["ok"] is True
    assert data["target_url"] == url
    assert len(hits) == 1


def test_ping_without_any_configured_url_is_422(client: TestClient):
    resp = client.post("/api/v1/project/webhook-ping", json={})

    assert resp.status_code == 422
    assert resp.json()["message"] == "No webhook URL configured or provided"


def test_ping_rejects_a_non_http_target(client: TestClient):
    """Trust boundary: refuse to be turned into a file:// or internal-scheme prober."""
    resp = client.post("/api/v1/project/webhook-ping", json={"target_url": "file:///etc/passwd"})
    assert resp.status_code == 422


def test_ping_does_not_record_a_delivery_row(client: TestClient, receiver):
    """A diagnostic must not pollute the webhook stats it exists to help debug."""
    url, _ = receiver
    before = client.get("/api/v1/analytics/overview").json()["webhooks"]["total_deliveries"]

    client.post("/api/v1/project/webhook-ping", json={"target_url": url})

    after = client.get("/api/v1/analytics/overview").json()["webhooks"]["total_deliveries"]
    assert after == before
