# Test Matrix & Contracts: Client Payment Journeys

This document defines the interface contracts and assertion expectations tested by the E2E suite.

## 1. Authentication & Session Contracts

| Route / Surface | Action | Input | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `GET /en/console` | Unauthenticated navigation | None | HTTP 307 / redirect to `/en/login` |
| `POST /en/login` | Form submission (invalid) | Registered email, wrong password | Alert banner rendered, remains on `/en/login` |
| `POST /en/login` | Form submission (valid) | Registered email, correct password | Session cookie attached (`ipg_session`), redirects to `/en/console` |

---

## 2. API Key Management Contracts

| Route / Surface | Action | Input | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `POST /en/settings/api-keys` (Modal) | Key creation | Key name (`Production app`) | Modal reveals plaintext key with prefix `ipg_key_`; table displays masked `••••<last4>` |
| `GET /api/v1/auth/me` | API Request with active key | `Authorization: Bearer <secret>` | HTTP 200 OK, returns user profile data |
| `DELETE /en/settings/api-keys` | Key revocation | Click revoke + confirm | Row removed from table |
| `GET /api/v1/auth/me` | API Request with revoked key | `Authorization: Bearer <secret>` | HTTP 401 Unauthorized |

---

## 3. Payment Lifecycle Contracts

| Route / Surface | Action | Input | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `POST /transactions/simulate` (Modal) | Create interactive payment | Amount, adapter (`zarinpal`), order reference | Transaction row created in `initiated` status; checkout URL provided |
| `GET /zarinpal/checkout/{authority}` | Open hosted checkout | None | Hosted bank page displays amount, authority, and action buttons |
| `POST /zarinpal/checkout/{authority}` | Confirm payment | Action: `confirm` | Redirects to callback with `Status=OK`; status advances to `pending` |
| `POST /zarinpal/payment/verification` | Verify payment | Authority | HTTP 200 OK, `code: 100`, status advances to `settled` |
| `POST /zarinpal/checkout/{authority}` | Cancel payment | Action: `fail` | Redirects to callback with `Status=NOK`; status advances to `declined` |

---

## 4. Webhook & Callback Contracts

| Route / Surface | Action | Input | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `PATCH /api/v1/project` | Update webhook URL | `webhook_url: "http://127.0.0.1:3099/callback"` | Setting persisted; displayed in `/en/webhooks` |
| `POST /api/v1/project/webhook-ping` | Trigger test ping | None | HTTP 200 OK with `ok: true`, latency reported |
| Engine Dispatcher | Asynchronous settlement dispatch | Payment verified (`settled`) | HTTP POST sent to callback server; delivery row visible in `/en/webhooks` with event `payment.approved` |

---

## 5. Transaction Operations Contracts

| Route / Surface | Action | Input | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `GET /en/console` (Search) | Search filter | `q=<authority>` | Exactly 1 matching transaction row displayed in table |
| `GET /en/console` (Filter) | Status filter | `status=settled` | All visible rows have status badge `Settled` |
| `GET /en/console/[id]` | Inspect transaction | Click transaction row link | Detail page displays authority, amount, adapter, raw request/response |
| `DELETE /en/console/[id]` | Delete transaction | Click delete + confirm | Transaction purged; redirect to console; subsequent API fetch returns 404 |
