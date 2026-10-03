# Tasks: Backend API and Dashboard UI Alignment

**Input**: Design documents from `/specs/002-backend-api-alignment/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/control-api.md`, `quickstart.md`
**Tests**: Automated tests included for backend routes and UI smoke verification per project engineering standard.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Types & Contracts)

**Purpose**: Establish typed data contracts across the engine and dashboard client.

- [X] T001 [P] Define TypeScript DTOs and API response interfaces (`PaymentSimulationRequest`, `PaymentSimulationResponse`, `ProjectAnalyticsOverview`, `WebhookPingResponse`, `PaginatedResult`) in `apps/dashboard/src/lib/api.ts`
- [X] T002 [P] Add internationalization strings for simulation modal, filters, ping button, and delete actions to `apps/dashboard/src/i18n/messages/en.json`
- [X] T003 [P] Add internationalization strings for simulation modal, filters, ping button, and delete actions to `apps/dashboard/src/i18n/messages/fa.json`

---

## Phase 2: Foundational (Engine Core Enhancements)

**Purpose**: Core engine model and helper prerequisites needed by multiple user stories.

- [X] T004 Add computed `checkout_url` helper to `_transaction_body` in `apps/engine/src/api/routes/transactions.py` using adapter endpoint prefix and authority token
- [X] T005 Update `delete_transaction` in `apps/engine/src/api/routes/transactions.py` to cascade-delete associated `WebhookDelivery` records referencing the transaction before deleting the row

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Interactive and Automated Payment Simulation (Priority: P1) 🎯 MVP

**Goal**: Enable developers to initiate payment simulations from the dashboard with options for interactive checkout or instant automated settlement.

**Independent Test**: Trigger simulation via API and UI; verify transaction is created with correct `checkout_url`, and when `auto_complete=true`, advances immediately to `settled`.

### Tests for User Story 1

- [X] T006 [P] [US1] Create integration test for `POST /api/v1/transactions/simulate` covering both `auto_complete=false` and `auto_complete=true` in `apps/engine/tests/integration/test_simulation.py`

### Implementation for User Story 1

- [X] T007 [US1] Implement `POST /api/v1/transactions/simulate` endpoint in `apps/engine/src/api/routes/transactions.py` validating adapter, amount, and scenario, supporting instant confirmation when `auto_complete=true`
- [X] T008 [US1] Add `simulateTransaction` client function to `apps/dashboard/src/lib/api.ts`
- [X] T009 [P] [US1] Create `SimulateModal.tsx` component in `apps/dashboard/src/components/SimulateModal.tsx` with gateway selection, Rial amount input with Toman helper, scenario dropdown, callback URL input, and dual actions (Launch Checkout vs Instant Settle)
- [X] T010 [US1] Wire the "Simulate Payment" header button in `apps/dashboard/src/components/Shell.tsx` to open `SimulateModal.tsx`

**Checkpoint**: User Story 1 is functional: users can simulate transactions from the dashboard and open checkout or auto-settle.

---

## Phase 4: User Story 2 - Accurate System-Wide Analytics and Metrics (Priority: P2)

**Goal**: Provide accurate database-wide transaction totals, success rate, status breakdown, and conversion funnel statistics.

**Independent Test**: Seed >50 transactions and verify `GET /api/v1/analytics/overview` and dashboard `StatCards.tsx` reflect all retained transactions rather than only page 1.

### Tests for User Story 2

- [X] T011 [P] [US2] Create integration test for `GET /api/v1/analytics/overview` verifying volume sum, success rate calculation, status counts, and funnel stages in `apps/engine/tests/integration/test_analytics.py`

### Implementation for User Story 2

- [X] T012 [US2] Implement `GET /api/v1/analytics/overview` in `apps/engine/src/api/routes/analytics.py` with SQL aggregation for volume, status counts, scenario breakdown, and lifecycle funnel
- [X] T013 [US2] Mount `analytics_router` in `apps/engine/src/api/routes/__init__.py` under `/api/v1`
- [X] T014 [US2] Add `getAnalyticsOverview` client function to `apps/dashboard/src/lib/api.ts`
- [X] T015 [US2] Update `StatCards.tsx` in `apps/dashboard/src/components/StatCards.tsx` to accept and render true project-wide metrics from `ProjectAnalyticsOverview`
- [X] T016 [US2] Update `TransactionsPage` in `apps/dashboard/src/app/[locale]/(console)/transactions/page.tsx` to fetch `getAnalyticsOverview()` and pass it to `StatCards`

**Checkpoint**: User Stories 1 and 2 work independently: overview cards display true database aggregates.

---

## Phase 5: User Story 3 - Transaction Search, Filtering, and Pagination (Priority: P3)

**Goal**: Enable free-text search across authority/reference/description, combined filtering by adapter and status, and full multi-page pagination.

**Independent Test**: Filter and search transactions by query string `q`, adapter, and status, and paginate through results with correct `page`, `page_size`, and `total_pages`.

### Tests for User Story 3

- [X] T017 [P] [US3] Create integration test for `GET /api/v1/transactions` with search query `q`, `status`, `adapter`, date range, and pagination in `apps/engine/tests/integration/test_search.py`

### Implementation for User Story 3

- [X] T018 [US3] Update `list_transactions` in `apps/engine/src/api/routes/transactions.py` to support `q` (ILIKE search on `authority`, `app_reference`, `description`), `from_date`, `to_date`, and return `total_pages`
- [X] T019 [US3] Update `listTransactions` client function in `apps/dashboard/src/lib/api.ts` to accept `q`, `adapter`, `from_date`, `to_date`
- [X] T020 [P] [US3] Create `TransactionFilters.tsx` in `apps/dashboard/src/components/TransactionFilters.tsx` with search input, status dropdown, adapter dropdown, and URL search param synchronization
- [X] T021 [P] [US3] Create `PaginationControls.tsx` in `apps/dashboard/src/components/PaginationControls.tsx` with page indicators, previous/next buttons, and page size selector
- [X] T022 [US3] Integrate `TransactionFilters` and `PaginationControls` into `apps/dashboard/src/app/[locale]/(console)/transactions/page.tsx`

**Checkpoint**: User Stories 1, 2, and 3 functional: users can search, filter, and paginate through transactions.

---

## Phase 6: User Story 4 - Webhook Delivery Management and Connectivity Testing (Priority: P4)

**Goal**: Provide a diagnostic ping endpoint to test webhook endpoint reachability with strict timeout, and expose default webhook URL configuration in UI.

**Independent Test**: Trigger a webhook test ping from the dashboard to a local endpoint and confirm latency, response code, and delivery log are recorded.

### Tests for User Story 4

- [X] T023 [P] [US4] Create integration test for `POST /api/v1/project/webhook-ping` testing responsive targets, connection timeouts, and missing URLs in `apps/engine/tests/integration/test_webhook_ping.py`

### Implementation for User Story 4

- [X] T024 [US4] Implement `POST /api/v1/project/webhook-ping` in `apps/engine/src/api/routes/deliveries.py` sending `sandbox.ping` payload with 3-second timeout and logging delivery
- [X] T025 [US4] Add `pingWebhook` client function to `apps/dashboard/src/lib/api.ts`
- [X] T026 [P] [US4] Create `WebhookPingButton.tsx` in `apps/dashboard/src/components/WebhookPingButton.tsx` with loading indicator and inline response toast
- [X] T027 [US4] Add `WebhookPingButton` and default webhook URL input to `apps/dashboard/src/app/[locale]/(console)/webhooks/page.tsx`
- [X] T028 [US4] Add project-level default webhook URL management to `apps/dashboard/src/app/[locale]/(console)/settings/page.tsx`

**Checkpoint**: User Stories 1 through 4 functional: webhooks can be inspected, configured, and tested.

---

## Phase 7: User Story 5 - Transaction Detail Actions and Hosted Checkout Access (Priority: P5)

**Goal**: Allow inspecting transactions with direct links to hosted checkout and ability to delete/purge records.

**Independent Test**: Open an initiated transaction detail page, follow the hosted checkout button, and test transaction deletion.

### Implementation for User Story 5

- [X] T029 [US5] Update `TransactionDetailPage` in `apps/dashboard/src/app/[locale]/(console)/transactions/[id]/page.tsx` to render "Open Gateway Checkout" linking to `tx.checkout_url` when status is `initiated` or `pending`
- [X] T030 [US5] Add `DeleteTransactionButton.tsx` in `apps/dashboard/src/components/DeleteTransactionButton.tsx` calling `deleteTransaction(id)` with confirmation and router redirect
- [X] T031 [US5] Integrate `DeleteTransactionButton` into `apps/dashboard/src/app/[locale]/(console)/transactions/[id]/page.tsx`

**Checkpoint**: All 5 user stories are functional and independently testable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: System verification, end-to-end smoke testing, and regression protection.

- [X] T032 Update smoke test suite in `apps/dashboard/tests/smoke.test.mjs` to verify analytics overview, simulation endpoint, and search query parameters
- [X] T033 Run full engine test suite via `pnpm run test` and verify all tests pass
- [X] T034 Run monorepo linting via `pnpm run lint` and verify zero errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion — blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2. Can be delivered as initial MVP.
- **Phase 4 (US2)**: Depends on Phase 2. Independent of US1.
- **Phase 5 (US3)**: Depends on Phase 2. Independent of US1/US2.
- **Phase 6 (US4)**: Depends on Phase 2. Independent of US1/US2/US3.
- **Phase 7 (US5)**: Depends on Phase 2 and US1 (benefits from `checkout_url`).
- **Phase 8 (Polish)**: Depends on all user stories being complete.

### Parallel Opportunities

- **Setup Phase**: T001, T002, T003 can run in parallel across frontend and translations.
- **Story Implementation**:
  - Once Phase 2 is complete, US1 (Simulation), US2 (Analytics), US3 (Search), and US4 (Webhooks) can be implemented in parallel by different workers.
  - Component tasks within stories marked `[P]` (e.g. T009, T010, T020, T021, T026, T030) are decoupled from backend route tasks.

---

## Implementation Strategy: MVP First

1. **Sprint 1 (MVP)**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (US1 - Simulation).
   - Delivers interactive and automated payment simulation directly from the dashboard.
2. **Sprint 2 (Analytics & Navigation)**: Phase 4 (US2 - Analytics) + Phase 5 (US3 - Search/Filter/Pagination).
   - Solves inaccurate overview stats and navigation over growing transaction histories.
3. **Sprint 3 (Diagnostics & Cleanup)**: Phase 6 (US4 - Webhooks) + Phase 7 (US5 - Detail actions) + Phase 8 (Polish).
   - Completes full diagnostic suite and end-to-end smoke test coverage.
