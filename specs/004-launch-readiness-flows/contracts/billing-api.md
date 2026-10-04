# Billing & Plan Purchase API Contract (004-launch-readiness-flows)

Base path: `/api/v1/billing`

---

## 1. Initiate Plan Upgrade (Zarinpal)

`POST /api/v1/billing/upgrade`

Requires authentication (`Cookie: ipg_session=...` or `Authorization: Bearer ...`).

### Request

```json
{
  "tier": "team",
  "period": "monthly"
}
```

### Response (200 OK)

```json
{
  "subscription_id": "c1d2e3f4-a5b6-7890-abcd-1234567890ef",
  "amount_rial": 1990000,
  "authority": "A00000000000000000000000000000123456",
  "payment_url": "https://payment.zarinpal.com/pg/StartPay/A00000000000000000000000000000123456"
}
```

Client redirects user's browser to `payment_url`.

### Error Responses

- `400 Bad Request`: `{"error": {"code": "invalid_tier", "message": "Unknown tier or tier is already active."}}`
- `502 Bad Gateway`: `{"error": {"code": "gateway_unreachable", "message": "Failed to connect to Zarinpal payment service."}}`

---

## 2. Zarinpal Settlement Callback

`GET /api/v1/billing/callback?Authority={authority}&Status={OK|NOK}`

Invoked by Zarinpal after the user completes payment on Zarinpal's gateway.

### Processing Logic
1. If `Status != "OK"`, mark subscription `status = "cancelled"` and redirect browser to `/dashboard/settings?payment=cancelled`.
2. If `Status == "OK"`:
   - Call Zarinpal `verify.json` with authority and amount (1,990,000 Rial).
   - If verification returns `code == 100` or `101`:
     - Update `subscription`: `status = "active"`, `zarinpal_ref_id = <ref>`, `started_at = now()`, `expires_at = now() + 30 days`.
     - Update `project`: `tier = "team"`, `daily_requests_cap = 0`, `max_active_adapters = 0`.
     - Redirect browser to `/dashboard/settings?payment=success`.
   - If verification returns error code (e.g. -51, -52):
     - Redirect browser to `/dashboard/settings?payment=failed&code=...`.

---

## 3. Current Subscription Status

`GET /api/v1/billing/subscription`

### Response (200 OK)

```json
{
  "tier": "team",
  "status": "active",
  "amount_toman": 199000,
  "started_at": "2026-10-04T12:00:00Z",
  "expires_at": "2026-11-03T12:00:00Z",
  "entitlements": {
    "daily_requests_limit": "unlimited",
    "active_adapters_limit": "all",
    "history_retention_days": 30
  }
}
```
