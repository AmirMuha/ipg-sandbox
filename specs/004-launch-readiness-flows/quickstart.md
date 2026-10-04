# Quickstart & Validation Guide: Launch Readiness Flows (004-launch-readiness-flows)

This guide provides runnable test scenarios verifying all launch flows: login, hosted checkout simulation, usage tracking, quota hard-blocking, and plan upgrade.

---

## Prerequisites

1. Engine running on `http://localhost:8080`:
   ```bash
   cd apps/engine && poetry run poe dev
   # or with pnpm:
   pnpm --filter ipg-sandbox-engine dev
   ```
2. Dashboard running on `http://localhost:3000`:
   ```bash
   pnpm --filter ipg-sandbox-dashboard dev
   ```

---

## Scenario 1: User Registration & Login Flow

### 1.1 Register New Account
```bash
curl -i -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-merchant@example.com",
    "password": "Password123!",
    "full_name": "Test Merchant"
  }'
```
**Expected**: HTTP `201 Created`, returns `user` and `project` objects, includes `Set-Cookie: ipg_session=...`.

### 1.2 Verify Authenticated Session
```bash
curl -s http://localhost:8080/api/v1/auth/me \
  -b "ipg_session=<SESSION_TOKEN>"
```
**Expected**: HTTP `200 OK`, returns user profile and workspace initialized with `tier: "developer"`, `daily_requests_cap: 100`, `max_active_adapters: 2`.

---

## Scenario 2: Usage Tracking & Daily Quota Rejection (HTTP 429)

### 2.1 Inspect Initial Usage
```bash
curl -s http://localhost:8080/api/v1/meters \
  -b "ipg_session=<SESSION_TOKEN>"
```
**Expected**: `requests_today` starts at `0`, `daily_requests_cap: 100`.

### 2.2 Trigger Daily Limit
Send 100 requests to payment endpoints, then issue request 101:
```bash
curl -i -X POST http://localhost:8080/api/v1/zarinpal/pg/v4/payment/request.json \
  -b "ipg_session=<SESSION_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "test-merchant",
    "amount": 500000,
    "callback_url": "http://localhost:3000/callback",
    "description": "Test order"
  }'
```
**Expected**:
- HTTP `429 Too Many Requests`
- Headers: `X-RateLimit-Remaining: 0`, `Retry-After: ...`
- Body: `{"error": {"code": "daily_quota_exceeded", ...}}`

---

## Scenario 3: Gateway Adapter Ceiling (Max 2 for Developer Tier)

### 3.1 Attempt Enabling a 3rd Gateway on Developer Plan
Assuming 2 gateways are already enabled, attempt enabling a 3rd:
```bash
curl -i -X PATCH http://localhost:8080/api/v1/adapters/behpardakht \
  -b "ipg_session=<SESSION_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```
**Expected**:
- HTTP `403 Forbidden`
- Body: `{"error": {"code": "adapter_limit_exceeded", "message": "Developer plan is limited to 2 active payment gateways..."}}`

---

## Scenario 4: Plan Upgrade via Live Zarinpal Integration

### 4.1 Initiate Upgrade
```bash
curl -s -X POST http://localhost:8080/api/v1/billing/upgrade \
  -b "ipg_session=<SESSION_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"tier": "team", "period": "monthly"}'
```
**Expected**:
- Returns `payment_url` pointing to `https://payment.zarinpal.com/pg/StartPay/{authority}` (or sandbox mock).

### 4.2 Complete Callback Verification
```bash
curl -i -s "http://localhost:8080/api/v1/billing/callback?Authority={AUTHORITY}&Status=OK" \
  -b "ipg_session=<SESSION_TOKEN>"
```
**Expected**:
- HTTP `302 Redirect` to `/dashboard/settings?payment=success`.
- `GET /api/v1/billing/subscription` reports `tier: "team"`, `status: "active"`.
- `GET /api/v1/meters` reports `daily_requests_cap: 0` (unlimited), `max_active_adapters: 0` (all allowed).

---

## Scenario 5: Hosted Payment Simulation Page & Redirection

### 5.1 Initiate Simulated Payment
```bash
curl -s -X POST http://localhost:8080/api/v1/zarinpal/pg/v4/payment/request.json \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "test-merchant",
    "amount": 250000,
    "callback_url": "http://localhost:3000/merchant/callback",
    "description": "Simulated item"
  }'
```
**Expected**: Returns `code: 100` and `authority: A000...`. Checkout link is `http://localhost:8080/checkout/{authority}`.

### 5.2 Open Checkout Page in Browser
- Navigate to `http://localhost:8080/checkout/{authority}`
- Verify:
  - Gateway branding (ZarinPal logo, colors)
  - Amount in Rial (250,000 ریال)
  - Actions: "تایید و پرداخت" (Confirm) and "انصراف" (Cancel)
- Click "Pay": Browser auto-submits POST back to `http://localhost:3000/merchant/callback?Authority=A000...&Status=OK`.
