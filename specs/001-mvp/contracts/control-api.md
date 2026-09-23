# Contract: Control API (dashboard + headless/CI interface) (Phase 1)

**Feature**: specs/001-mvp | **Date**: 2026-09-23
**Purpose**: The single interface the dashboard consumes — everything the UI can do, a script can do (FR-010 headless parity). Base: `{ENGINE_URL}/api/v1`. JSON in/out; machine-readable errors `{code, message, details?}`.

**Auth scoping**

- Local self-host: no auth (FR-014).
- Hosted demo: session cookie from `demo/` layer; every handler scopes queries by `project_id` from the session (FR-014 isolation).

## Endpoints

### Transactions

| Method + path | Purpose |
|---------------|---------|
| `GET /transactions?status=&adapter=&page=&page_size=` | List (newest first, ≤ project.history_cap retained) |
| `GET /transactions/{id}` | Detail incl. raw_request/raw_response, resolved scenario, delivery summaries |
| `POST /transactions` | Optional pre-seed: `{adapter, amount_rial, forced_scenario?, app_reference?, callback_url?, return_url?}` → returns initiate info (CI can pin scenario before initiating) |
| `PATCH /transactions/{id}` | Update `forced_scenario` (dashboard force control / CI) |
| `DELETE /transactions/{id}` | Manual purge (does not affect cap semantics) |

**Scenario hint for CI without pre-seed**: emulated adapter initiate requests honor optional header `X-Sandbox-Scenario: approve|decline|timeout|refund|pending_settle|verify_fail` as the per-transaction force (research R5).

### Scenario defaults & adapters

| Method + path | Purpose |
|---------------|---------|
| `GET /project` / `PATCH /project` | Read/update `default_scenario`, delays (`pending_settle_delay_s`, `timeout_delay_s`), `webhook_retry_*`, `history_cap` |
| `GET /adapters` / `PATCH /adapters/{id}` | Per-adapter enable + test credentials + status |
| `POST /adapters/{id}/test` | Self-check that the emulated surface responds (misconfig → clear error, edge case) |

### Webhook deliveries

| Method + path | Purpose |
|---------------|---------|
| `GET /deliveries?transaction_id=&result=` | Delivery history: target, timestamp, outcome, payload, attempt (US3.3) |
| `POST /deliveries/{id}/retry` | Force immediate re-delivery attempt |
| `PUT /project/webhook-url` | Project-level default callback target |

### Usage meters

| Method + path | Purpose |
|---------------|---------|
| `GET /meters` | `requests_total`, `transactions_total`, `history_retained`, `webhook_attempts` (FR-011 counters; no billing fields) |

### Demo-only (served by `demo/` layer, not core engine)

| Method + path | Purpose |
|---------------|---------|
| `POST /demo/signup` | `{email}` → magic link issued (rate-limited, spam-throttled) |
| `POST /demo/verify` | `{token}` → session cookie, binds visitor's Project |
| `POST /demo/logout` | Clear session |

Local mode: these routes are absent/disabled (no login path exists locally).

## Error codes (subset)

`validation_error` · `unsupported_operation` · `invalid_credentials` (clear message to caller + dashboard — edge case) · `not_found` · `rate_limited` · `scenario_invalid` · `session_required` (demo only).

## Behavioral guarantees

- All list endpoints are pagination-safe and return only the caller's `project_id` rows (demo isolation).
- Scenario PATCH affects only future initiations that resolve to it; per-transaction force always beats project default (edge-case precedence).
- Response for every mutating call includes the resulting resource representation (machine-assertable for CI, US5.1).
