"""Quickstart §4: Forced pending->settle timing and scheduler sweep (T034).

Asserts:
1. Status is `pending` immediately after checkout confirm, with `due_at` set.
2. Synchronous verify settles after the configured delay.
3. Project override via `PATCH /api/v1/project` changes delay for future transactions.
4. Background DB sweep settles due rows even without verify being called.
"""

import time

from fastapi.testclient import TestClient


def test_pending_settle_timing_and_override(client: TestClient):
    """Timing verification for pending_settle scenario (Quickstart §4)."""
    # 1. Set delay to 1 second for predictable timing test
    patch_resp = client.patch(
        "/api/v1/project",
        json={"pending_settle_delay_s": 1, "timeout_delay_s": 1},
    )
    assert patch_resp.status_code == 200

    # 2. Initiate with pending_settle
    init_resp = client.post(
        "/zarinpal/request/payment",
        headers={"X-Sandbox-Scenario": "pending_settle"},
        json={
            "amount": 10000,
            "return_url": "http://localhost:3000/return",
        },
    )
    authority = init_resp.json()["authority"]

    # 3. Checkout confirm
    confirm_resp = client.post(
        f"/zarinpal/checkout/{authority}",
        data={"action": "confirm"},
        follow_redirects=False,
    )
    assert confirm_resp.status_code == 302

    # 4. Immediately check status — must be pending, not settled yet
    txs = client.get("/api/v1/transactions").json()["items"]
    matched = next(t for t in txs if t["authority"] == authority)
    assert matched["status"] == "pending"
    assert matched["due_at"] is not None

    # 5. Verify waits for delay then settles
    start_time = time.monotonic()
    verify_resp = client.post(
        "/zarinpal/payment/verification",
        json={"authority": authority},
    )
    elapsed = time.monotonic() - start_time
    assert verify_resp.status_code == 200
    assert verify_resp.json()["code"] == 100
    assert elapsed >= 0.8  # waited close to the 1s delay

    # 6. Status is now settled
    txs = client.get("/api/v1/transactions").json()["items"]
    matched = next(t for t in txs if t["authority"] == authority)
    assert matched["status"] == "settled"

    # 7. Override to 0s via PATCH /api/v1/project
    client.patch("/api/v1/project", json={"pending_settle_delay_s": 0})

    # Second transaction settles immediately
    init2 = client.post(
        "/zarinpal/request/payment",
        headers={"X-Sandbox-Scenario": "pending_settle"},
        json={"amount": 20000, "return_url": "http://localhost:3000/return"},
    )
    auth2 = init2.json()["authority"]
    client.post(f"/zarinpal/checkout/{auth2}", data={"action": "confirm"}, follow_redirects=False)

    start_fast = time.monotonic()
    v2 = client.post("/zarinpal/payment/verification", json={"authority": auth2})
    elapsed_fast = time.monotonic() - start_fast
    assert v2.status_code == 200
    assert elapsed_fast < 0.5

    # Reset to default
    client.patch("/api/v1/project", json={"pending_settle_delay_s": 5, "timeout_delay_s": 30})


def test_scheduler_background_sweep(client: TestClient):
    """Background scheduler sweeps due rows without verify being called."""
    # Pre-seed a transaction
    resp = client.post(
        "/api/v1/transactions",
        json={
            "adapter": "zarinpal",
            "amount_rial": 50000,
            "forced_scenario": "pending_settle",
        },
    )
    tx_id = resp.json()["id"]
    authority = resp.json()["authority"]

    # Set delay to 1s
    client.patch("/api/v1/project", json={"pending_settle_delay_s": 1})

    # Checkout confirm sets due_at to now + 1s and status=pending
    client.post(
        f"/zarinpal/checkout/{authority}",
        data={"action": "confirm"},
        follow_redirects=False,
    )

    # Immediately check: status is pending
    tx_body = client.get(f"/api/v1/transactions/{tx_id}").json()
    assert tx_body["status"] == "pending"

    # Wait for scheduler to sweep (sweep runs every 1.0s)
    # Poll up to 3 seconds for status to change to settled
    settled = False
    for _ in range(30):
        time.sleep(0.1)
        cur = client.get(f"/api/v1/transactions/{tx_id}").json()
        if cur["status"] == "settled":
            settled = True
            break

    assert settled, "Scheduler did not transition due pending transaction to settled"

    # Reset to default
    client.patch("/api/v1/project", json={"pending_settle_delay_s": 5})
