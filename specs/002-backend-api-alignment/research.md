# Technical Research: Backend API and Dashboard UI Alignment

**Feature**: `002-backend-api-alignment` | **Date**: 2026-10-03

## Research Summary

This document captures technical decisions resolving gaps between the Iranian Payment Gateway Sandbox engine (FastAPI + SQLAlchemy) and its bilingual Next.js dashboard UI. All decisions satisfy the project's 1,000-transaction retention cap, local self-hosted zero-external-network rule, and bilingual FA (RTL) / EN (LTR) requirements.

---

### Decision 1: Aggregated Analytics & Lifecycle Conversion Funnel Architecture

- **Context**: `StatCards.tsx` calculates volume, approved/declined counts, and success rate client-side over only the first 50 transactions loaded on page 1. With hundreds of records, displayed metrics are inaccurate. Furthermore, the UI design features a payment lifecycle conversion funnel (Initiated → Gateway Hosted → Callback Received → Verified/Settled) and scenario distribution metrics.
- **Decision**: Implement a single SQL aggregation endpoint `GET /api/v1/analytics/overview`.
- **Query Strategy**:
  - Run a single multi-aggregate query on `Transaction` filtered by `project_id == project.id`:
    - `total_volume_rial`: `coalesce(sum(amount_rial), 0)`
    - `total_transactions`: `count(id)`
    - Status breakdown: `count(case(status == 'settled' or status == 'approved', 1))` for successful, `count(case(status == 'declined' or status == 'failed', 1))` for failed, `count(case(status == 'pending', 1))` for pending, etc.
    - Funnel lifecycle stages:
      - `initiated`: total count
      - `hosted`: count of transactions that transitioned past initiation or have checkout interaction (`status != 'initiated'`)
      - `callback`: count of transactions with associated webhook deliveries or return attempts
      - `settled`: count with status `settled` or `approved`
    - Scenario distribution: counts grouped by `effective_scenario`
  - Run a secondary aggregate query on `WebhookDelivery` joined to `Transaction`:
    - `total_deliveries`: `count(WebhookDelivery.id)`
    - `failed_deliveries`: `count(case(WebhookDelivery.result == 'failed', 1))`
- **Rationale**: With a bounded history cap of 1,000 transactions, this aggregation executes in < 3ms on PostgreSQL and < 1ms on SQLite. Caching or background worker aggregation would add state invalidation complexity for no measurable performance gain.
- **Alternatives Considered**:
  - *Client-side aggregation over all pages*: Would require fetching all 1,000 records on every dashboard load, transferring excessive JSON payloads.
  - *Redis / Materialized View*: Over-engineering for a local sandbox bounded at 1,000 rows. Violates YAGNI and adds operational dependencies.

---

### Decision 2: Payment Simulation Workflow API

- **Context**: The dashboard header features a prominent "Simulate Payment" CTA that currently only navigates to `/transactions`. In `spec.md` (FR-001, FR-002, FR-011), the user selected "Both interactive checkout portal & one-click auto-complete".
- **Decision**: Expose `POST /api/v1/transactions/simulate` accepting:
  - `adapter`: provider name (`zarinpal`, `idpay`, `behpardakht`) or adapter UUID
  - `amount_rial`: integer >= 0
  - `forced_scenario`: target scenario outcome or null
  - `callback_url`: optional override URL
  - `description`: optional order description
  - `app_reference`: optional order reference
  - `auto_complete`: boolean (default `false`)
- **Execution Flow**:
  - When `auto_complete = false`:
    - Initiates transaction in database using existing adapter logic.
    - Returns transaction body including canonical `checkout_url` (`http://localhost:8080/{prefix}/checkout/{authority}`).
  - When `auto_complete = true`:
    - Initiates transaction in database.
    - Immediately simulates hosted checkout confirmation (`checkout_confirm_status(tx)`).
    - If scenario is `approve` or `pending_settle`, advances transaction to target state.
    - Dispatches webhook delivery worker task for the settle stage if callback URL is present.
    - Returns final transaction body with updated status.
- **Rationale**: Providing a dedicated simulation endpoint keeps headless client simulation clean and enables both manual visual browser testing (via checkout URL) and instant automated verification for CI/developer testing.
- **Alternatives Considered**:
  - *Reusing `POST /api/v1/transactions` directly*: That endpoint is documented in `contracts/control-api.md` as low-level pre-seeding. Adding high-level simulation flags like `auto_complete` is cleaner on a dedicated `/simulate` route while keeping pre-seed focused on raw fixture insertion.

---

### Decision 3: Transaction List Free-Text Search and Multi-Criteria Filtering

- **Context**: `GET /api/v1/transactions` only supports exact `status` and `adapter` filters. Finding specific transactions by order reference or authority token requires manual scanning.
- **Decision**: Enhance `GET /api/v1/transactions` with:
  - `q`: optional free-text search string (case-insensitive search across `authority`, `app_reference`, and `description`).
  - `status`: optional `TransactionStatus` filter.
  - `adapter`: optional provider name or adapter ID.
  - `from_date`: optional ISO datetime string (`Transaction.created_at >= from_date`).
  - `to_date`: optional ISO datetime string (`Transaction.created_at <= to_date`).
  - `page`: 1-based page number (default 1).
  - `page_size`: items per page (default 20, max 100).
  - Return payload:
    ```json
    {
      "items": [...],
      "page": 1,
      "page_size": 20,
      "total": 142,
      "total_pages": 8
    }
    ```
- **Rationale**: Using SQLAlchemy `or_(Transaction.authority.ilike(f"%{q}%"), Transaction.app_reference.ilike(f"%{q}%"), Transaction.description.ilike(f"%{q}%"))` provides fast, portable search across both PostgreSQL and SQLite without requiring full-text search extensions.
- **Alternatives Considered**:
  - *Client-side filtering*: Fails because transactions are paginated server-side; client-side filtering would only search the current 20 or 50 loaded records.

---

### Decision 4: Webhook Connectivity Test ("Ping") Endpoint

- **Context**: Developers need to verify that their local application's webhook listener is reachable and responding with HTTP 200 before running full payment scenarios.
- **Decision**: Implement `POST /api/v1/project/webhook-ping`.
- **Request Body**:
  - `target_url`: optional string (defaults to `project.webhook_url` if omitted).
- **Behavior**:
  - Validates that `target_url` is an absolute HTTP/HTTPS URL.
  - Constructs a standardized ping event payload:
    ```json
    {
      "event": "sandbox.ping",
      "project_id": "...",
      "timestamp": "2026-10-03T12:00:00Z",
      "message": "IPG Sandbox webhook connectivity test",
      "sandbox_version": "0.1.0"
    }
    ```
  - Sends an HTTP POST with `httpx.AsyncClient` with a strict `timeout=3.0` seconds.
  - Returns structured diagnostics:
    ```json
    {
      "ok": true,
      "target_url": "http://localhost:3000/api/webhook",
      "status_code": 200,
      "latency_ms": 42,
      "error": null
    }
    ```
  - Optionally logs the ping attempt as a `WebhookDelivery` record with `stage="ping"`.
- **Rationale**: Allows instant debugging of local firewall, port, or route issues in the developer's application without altering transaction history.

---

### Decision 5: Transaction Detail Actions and Hosted Checkout Link

- **Context**: `transactions/[id]/page.tsx` displays transaction details and allows scenario patching, but lacks:
  1. A direct link or button to open the hosted checkout portal if the transaction is pending payment.
  2. An action to permanently delete/purge an individual transaction.
- **Decision**:
  - Include computed `checkout_url` in `_transaction_body`:
    `f"http://localhost:8080{adapter.endpoint_path_prefix}/checkout/{tx.authority}"`
  - In `TransactionDetailPage`, if `tx.status` is in `("initiated", "pending")` and checkout is applicable, render a button "Open Gateway Checkout" linking to `tx.checkout_url`.
  - Add a "Delete Transaction" action calling `deleteTransaction(id)` with router redirect back to `/transactions`.
  - On the backend, ensure `DELETE /api/v1/transactions/{id}` cascades or explicitly cleans up associated `WebhookDelivery` records before deleting the transaction row.

---

### Decision 6: Dashboard Frontend Component Architecture

- **Context**: Dashboard UI needs to integrate the new API capabilities cleanly into the existing Next.js App Router structure.
- **Components to add / update**:
  - `apps/dashboard/src/components/SimulateModal.tsx`:
    - Client component dialog triggered from `Shell.tsx` "Simulate Payment" button.
    - Fields: Gateway selector, Amount (Rial + live Toman equivalent helper), Scenario selector, Callback URL, Description.
    - Dual actions: "Launch Gateway Checkout" (opens checkout URL in new tab) and "Simulate Instantly" (runs `auto_complete=true` and refreshes table).
  - `apps/dashboard/src/components/StatCards.tsx`:
    - Updated to take `ProjectAnalyticsOverview` loaded server-side from `getAnalyticsOverview()`.
    - Renders exact database-wide volume, success rate, active adapters, and callback deliveries.
  - `apps/dashboard/src/components/TransactionFilters.tsx`:
    - Search input (`q`), status dropdown, adapter dropdown, and page controls.
    - Uses Next.js `useRouter` / `useSearchParams` for URL-driven state (`?q=...&status=...&page=...`).
  - `apps/dashboard/src/components/WebhookPingButton.tsx`:
    - Action button in `webhooks/page.tsx` and `settings/page.tsx` to trigger connectivity ping with inline result toast.
