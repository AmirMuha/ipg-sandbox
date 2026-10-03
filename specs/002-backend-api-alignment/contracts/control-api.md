# Contract: Control API (Aligned Backend & Dashboard Interface)

**Feature**: `specs/002-backend-api-alignment` | **Date**: 2026-10-03  
**Base URL**: `{ENGINE_URL}/api/v1`  
**Protocol**: HTTP/1.1 JSON in/out, UTF-8. Error format: `{ "code": string, "message": string, "details"?: object }`

---

## 1. Analytics & Overview Endpoints

### `GET /analytics/overview`
Returns true project-wide totals and payment lifecycle conversion funnel statistics computed across all retained records.

- **Request**: No body / query parameters. Scoped by authenticated/active `project_id`.
- **Response 200 OK**:
  ```json
  {
    "total_volume_rial": 485000000,
    "total_transactions": 148,
    "success_rate_percent": 93.9,
    "status_breakdown": {
      "settled": 139,
      "approved": 0,
      "pending": 3,
      "initiated": 0,
      "declined": 6,
      "failed": 0,
      "expired": 0,
      "refunded": 0
    },
    "scenario_distribution": {
      "approve": 130,
      "decline": 6,
      "timeout": 3,
      "pending_settle": 6,
      "verify_fail": 3,
      "refund": 0
    },
    "funnel": {
      "initiated": 148,
      "hosted": 144,
      "callback": 142,
      "settled": 139
    },
    "webhooks": {
      "total_deliveries": 154,
      "delivered": 148,
      "failed": 6,
      "pending": 0
    },
    "gateways": {
      "configured_total": 3,
      "active_total": 3
    }
  }
  ```

---

## 2. Transactions Endpoints

### `POST /transactions/simulate`
Creates a realistic payment simulation with support for both interactive manual checkout and instant automated completion.

- **Request 201 Created**:
  ```json
  {
    "adapter": "zarinpal",
    "amount_rial": 2500000,
    "forced_scenario": "approve",
    "callback_url": "http://localhost:3000/api/payment/callback",
    "description": "Order #9401 — Premium Plan",
    "app_reference": "ORD-9401",
    "auto_complete": false
  }
  ```
- **Validation**:
  - `adapter`: must match an enabled adapter provider name (`zarinpal`, `idpay`, `behpardakht`) or valid adapter UUID.
  - `amount_rial`: integer >= 0.
  - `forced_scenario`: valid `ScenarioOutcome` enum or `null`.
  - `callback_url`: valid absolute URL or `null`.
  - `auto_complete`: boolean (default `false`).
- **Response 201 Created**:
  ```json
  {
    "transaction": {
      "id": "e4b37f10-912e-4b2a-9cb8-0174fa901234",
      "project_id": "6fda3e05-ba38-4cb0-97b9-9c377a2b7de1",
      "adapter_id": "45c9651e-db74-4140-ac78-766c87fffd37",
      "amount_rial": 2500000,
      "currency": "IRR",
      "status": "initiated",
      "forced_scenario": "approve",
      "effective_scenario": "approve",
      "authority": "A000000000000000000000000000009401",
      "app_reference": "ORD-9401",
      "description": "Order #9401 — Premium Plan",
      "callback_url": "http://localhost:3000/api/payment/callback",
      "return_url": null,
      "due_at": null,
      "created_at": "2026-10-03T12:00:00Z",
      "updated_at": "2026-10-03T12:00:00Z",
      "checkout_url": "http://localhost:8080/zarinpal/checkout/A000000000000000000000000000009401"
    },
    "checkout_url": "http://localhost:8080/zarinpal/checkout/A000000000000000000000000000009401",
    "execution_mode": "interactive",
    "callback_dispatched": false
  }
  ```
- **When `auto_complete=true`**:
  - Immediately transitions transaction through `checkout_confirm_status(tx)` and verification.
  - Dispatches settlement callback worker if `callback_url` is present.
  - Returns `execution_mode: "auto_completed"`, `transaction.status: "settled"` (or scenario target), and `callback_dispatched: true`.

---

### `GET /transactions`
List transactions with search, multi-criteria filtering, and full pagination metadata.

- **Query Parameters**:
  - `q`: string (case-insensitive search matching `authority`, `app_reference`, `description`)
  - `status`: `TransactionStatus` enum
  - `adapter`: `Provider` enum (`zarinpal`, `idpay`, `behpardakht`)
  - `from_date`: ISO datetime string
  - `to_date`: ISO datetime string
  - `page`: integer >= 1 (default 1)
  - `page_size`: integer 1-100 (default 20)
- **Response 200 OK**:
  ```json
  {
    "items": [
      {
        "id": "e4b37f10-912e-4b2a-9cb8-0174fa901234",
        "project_id": "6fda3e05-ba38-4cb0-97b9-9c377a2b7de1",
        "adapter_id": "45c9651e-db74-4140-ac78-766c87fffd37",
        "amount_rial": 2500000,
        "currency": "IRR",
        "status": "settled",
        "forced_scenario": "approve",
        "effective_scenario": "approve",
        "authority": "A000000000000000000000000000009401",
        "app_reference": "ORD-9401",
        "description": "Order #9401 — Premium Plan",
        "callback_url": "http://localhost:3000/api/payment/callback",
        "return_url": null,
        "due_at": null,
        "created_at": "2026-10-03T12:00:00Z",
        "updated_at": "2026-10-03T12:00:05Z",
        "checkout_url": "http://localhost:8080/zarinpal/checkout/A000000000000000000000000000009401"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  }
  ```

---

### `DELETE /transactions/{transaction_id}`
Permanently deletes an individual transaction and cascades removal to all associated delivery logs.

- **Response 200 OK**: Returns deleted transaction body including `"deleted": true`.
- **Response 404 Not Found**: If transaction does not exist or belongs to another project.

---

## 3. Webhooks Diagnostic Endpoints

### `POST /project/webhook-ping`
Dispatches a synthetic test ping event to verify that an external endpoint is reachable and responsive.

- **Request 200 OK**:
  ```json
  {
    "target_url": "http://localhost:3000/api/webhook"
  }
  ```
  *(If `target_url` is omitted or null, defaults to `project.webhook_url`)*
- **Validation**:
  - `target_url` (or fallback) must be configured and valid HTTP(S). If neither exists, returns `422 validation_error: "No webhook URL configured or provided"`.
- **Response 200 OK**:
  ```json
  {
    "ok": true,
    "target_url": "http://localhost:3000/api/webhook",
    "status_code": 200,
    "latency_ms": 38,
    "error": null
  }
  ```
- **Error Response 200 OK (Connection Failed)**:
  ```json
  {
    "ok": false,
    "target_url": "http://localhost:3000/bad-port",
    "status_code": null,
    "latency_ms": 3004,
    "error": "Connection refused / Connect timeout"
  }
  ```

---

## 4. Project Configuration Endpoints

### `PATCH /project`
Updates project-wide settings.

- **Patchable Fields**:
  - `default_scenario`: `ScenarioOutcome`
  - `pending_settle_delay_s`: integer in `[0, 299]`
  - `timeout_delay_s`: integer in `[0, 299]`
  - `history_cap`: integer `>= 1`
  - `webhook_retry_max`: integer `>= 1`
  - `webhook_retry_backoff_s`: list of non-negative integers
  - `webhook_url`: absolute HTTP(S) URL or null
- **Response 200 OK**: Returns updated project configuration.
