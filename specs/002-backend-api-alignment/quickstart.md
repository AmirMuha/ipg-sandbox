# Quickstart Validation Guide: Backend API and Dashboard UI Alignment

**Feature**: `specs/002-backend-api-alignment` | **Date**: 2026-10-03  
**Target Services**: Engine (`http://localhost:8080`), Dashboard (`http://localhost:3000`)

This guide provides runnable curl and browser validation scenarios to prove that the backend API changes and dashboard UI components align and satisfy all requirements in [spec.md](./spec.md).

---

## Prerequisites

1. PostgreSQL database running:
   ```bash
   docker compose up -d postgres
   ```
2. Engine running locally:
   ```bash
   cd apps/engine && .venv/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8080
   ```
3. Dashboard built and running:
   ```bash
   cd apps/dashboard && pnpm dev
   ```

---

## Validation Scenario 1: Verify System-Wide Analytics & Funnel Overview

**Objective**: Confirm `GET /api/v1/analytics/overview` returns project-wide aggregates and funnel stages rather than relying on first-page pagination.

```bash
curl -s http://localhost:8080/api/v1/analytics/overview | python3 -m json.tool
```

**Expected Outcome**:
- Status: `200 OK`
- JSON payload contains:
  - `total_volume_rial`: integer sum of all transactions
  - `total_transactions`: total count of all transactions
  - `success_rate_percent`: percentage between `0.0` and `100.0`
  - `funnel`: `{ "initiated": int, "hosted": int, "callback": int, "settled": int }`
  - `gateways`: active and configured gateway counts

---

## Validation Scenario 2: Interactive Payment Simulation & Hosted Checkout

**Objective**: Verify `POST /api/v1/transactions/simulate` generates a transaction and returns an accessible hosted checkout URL.

```bash
curl -s -X POST http://localhost:8080/api/v1/transactions/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "adapter": "zarinpal",
    "amount_rial": 2500000,
    "forced_scenario": "approve",
    "description": "Validation test #1",
    "app_reference": "VAL-001",
    "auto_complete": false
  }' | python3 -m json.tool
```

**Expected Outcome**:
- Status: `201 Created`
- Response contains `checkout_url` formatted as `http://localhost:8080/zarinpal/checkout/{authority}`.
- Navigating to the `checkout_url` in a browser renders the Shaparak mock gateway portal.
- Submitting `action=confirm` redirects back with approved verification.

---

## Validation Scenario 3: One-Click Automated Payment Simulation

**Objective**: Verify instant end-to-end simulation advances transaction through checkout and verification in one action.

```bash
curl -s -X POST http://localhost:8080/api/v1/transactions/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "adapter": "idpay",
    "amount_rial": 1500000,
    "forced_scenario": "approve",
    "callback_url": "http://localhost:3000/api/callback",
    "description": "Instant test #2",
    "app_reference": "VAL-002",
    "auto_complete": true
  }' | python3 -m json.tool
```

**Expected Outcome**:
- Status: `201 Created`
- `execution_mode`: `"auto_completed"`
- `transaction.status`: `"settled"`
- `callback_dispatched`: `true`

---

## Validation Scenario 4: Transaction Search, Filtering, and Pagination

**Objective**: Verify text search across authority and references, plus status and provider filtering.

1. **Search by reference**:
   ```bash
   curl -s "http://localhost:8080/api/v1/transactions?q=VAL-001" | python3 -m json.tool
   ```
   **Expected**: Only transactions matching `"VAL-001"` in `app_reference`, `authority`, or `description` are returned; `total` reflects total matching count.

2. **Combined filtering**:
   ```bash
   curl -s "http://localhost:8080/api/v1/transactions?adapter=zarinpal&status=settled&page=1&page_size=10" | python3 -m json.tool
   ```
   **Expected**: Only settled Zarinpal transactions returned; `page_size: 10`, `total_pages` computed.

---

## Validation Scenario 5: Webhook Connectivity Test ("Ping")

**Objective**: Verify test webhook dispatch and diagnostic response.

```bash
# Test with a mock listener or local dashboard
curl -s -X POST http://localhost:8080/api/v1/project/webhook-ping \
  -H "Content-Type: application/json" \
  -d '{ "target_url": "http://localhost:3000/api/test-webhook" }' | python3 -m json.tool
```

**Expected Outcome**:
- Response contains `{ "ok": bool, "target_url": string, "status_code": int|null, "latency_ms": int, "error": string|null }`.
- Request completes within 3.0 seconds even if target is unreachable.

---

## Validation Scenario 6: Transaction Purge & Cascade Check

**Objective**: Verify individual transaction deletion and clean cascade.

```bash
# 1. Create a disposable transaction
TX_ID=$(curl -s -X POST http://localhost:8080/api/v1/transactions/simulate \
  -H "Content-Type: application/json" \
  -d '{"adapter":"zarinpal","amount_rial":1000}' | python3 -c "import sys, json; print(json.load(sys.stdin)['transaction']['id'])")

# 2. Delete it
curl -s -X DELETE "http://localhost:8080/api/v1/transactions/$TX_ID" | python3 -m json.tool

# 3. Confirm 404 on subsequent get
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/api/v1/transactions/$TX_ID"
```

**Expected Outcome**:
- Delete returns `200 OK`.
- Subsequent `GET` returns `404 Not Found`.

---

## Validation Scenario 7: Automated Test Suite

Run engine and dashboard integration tests to verify no regressions:

```bash
pnpm run test
pnpm run lint
```

**Expected Outcome**: All engine unit/integration tests and dashboard smoke tests pass cleanly.
