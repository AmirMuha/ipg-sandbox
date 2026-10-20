# Tasks: Client Payment Journeys — End-to-End Proof

**Input**: Design documents from `specs/008-client-e2e-tests/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/test-matrix.md`, `quickstart.md`

**Tests**: This feature IS an end-to-end test suite proving the product from a merchant client's perspective. All tasks specify test assets, runner scripts, and validation steps.

**Organization**: Tasks are grouped by user story (US1 through US5) to enable incremental development, execution, and validation.

## Format: `[TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run or be implemented in parallel
- **[Story]**: User story label mapping directly to `spec.md` (e.g., US1, US2, US3)

---

## Phase 1: Setup (Test Infrastructure & Harness)

**Purpose**: Test runners, local callback receiver, and shared client test helpers.

- [x] T001 [P] Configure Playwright settings (120s timeout, 30s assertions, serial mode, retain trace on failure) in `apps/web/playwright.config.ts`
- [x] T002 [P] Implement loopback Webhook Callback server with `POST /callback` and `GET /__received` endpoints in `apps/web/tests/e2e/callback-server.mjs`
- [x] T003 [P] Implement test client helpers (merchant generation, registration, login form automation, session cookies, payment verification helper) in `apps/web/tests/e2e/helpers.ts`
- [x] T004 Create ephemeral environment orchestration script with SQLite DB init, background engine/web services, callback server, and trap cleanup in `apps/web/tests/run_e2e.sh`
- [x] T005 [P] Register `test:e2e` execution script in `apps/web/package.json`

---

## Phase 2: Foundational (Platform Entry & Auth Protection)

**Purpose**: Verify unauthenticated guards and basic account session mechanics before testing payment business logic.

- [x] T006 [P] [US5] Implement unauthenticated access redirect test from `/en/console` to `/en/login` in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T007 [US5] Implement authentication test verifying invalid credential rejection and valid credential login redirect in `apps/web/tests/e2e/client-payments.spec.ts`

**Checkpoint**: Merchant can reliably sign in and reach the console dashboard.

---

## Phase 3: User Story 1 - Merchant Completes Payment End-to-End (Priority: P1) 🎯 MVP

**Goal**: Prove payment initiation, hosted gateway checkout, shopper confirmation, backend verification, and console settlement updates.

**Independent Test**: Execute full payment cycle for merchant and observe `settled` badge in console transaction table.

- [x] T008 [US1] Implement browser test for creating payment via console modal with amount and custom order reference in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T009 [US1] Implement browser test for hosted gateway checkout (`/zarinpal/checkout/{authority}`) verifying authority, amount, and confirm action redirect in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T010 [US1] Implement backend verification call (`POST /zarinpal/payment/verification`) asserting code 100 in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T011 [US1] Implement console reload assertion verifying transaction status badge transitions to `Settled` in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T012 [US1] Implement cancelled payment test verifying hosted checkout `fail` button marks transaction as `declined` in `apps/web/tests/e2e/client-payments.spec.ts`

**Checkpoint**: Full payment lifecycle is proven from creation to settlement and cancellation.

---

## Phase 4: User Story 2 - Client Provisions & Uses API Key (Priority: P1)

**Goal**: Prove API key generation, single reveal, programmatic Bearer auth, and revocation.

**Independent Test**: Create key in UI, call `/api/v1/auth/me` with Bearer token, revoke key, assert 401 rejection.

- [x] T013 [US2] Implement API key creation test via `/en/settings/api-keys` modal in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T014 [US2] Implement token format assertion (`ipg_key_` prefix) and single-reveal warning verification in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T015 [US2] Implement masked token table view assertion (`••••<last4>`) in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T016 [US2] Implement programmatic API test using active API key Bearer token against `/api/v1/auth/me` in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T017 [US2] Implement key revocation flow with confirmation button in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T018 [US2] Implement post-revocation rejection test verifying HTTP 401 on `/api/v1/auth/me` in `apps/web/tests/e2e/client-payments.spec.ts`

**Checkpoint**: API key management lifecycle works securely end-to-end.

---

## Phase 5: User Story 3 - Client Wires Webhooks & Sees Delivery Proof (Priority: P2)

**Goal**: Prove webhook URL configuration, diagnostic ping probe, settlement event dispatch, and dashboard delivery logging.

**Independent Test**: Settle a payment and assert delivery at callback endpoint and on `/en/webhooks`.

- [x] T019 [US3] Implement webhook URL configuration test in project settings (`/en/settings`) in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T020 [US3] Implement webhook ping probe test asserting HTTP 200 and latency measurement in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T021 [US3] Implement asynchronous settlement webhook dispatch assertion on `/en/webhooks` table in `apps/web/tests/e2e/client-payments.spec.ts`

**Checkpoint**: Client receives automated event notifications upon payment completion.

---

## Phase 6: User Story 4 - Transaction Search, Filter & Deletion (Priority: P2)

**Goal**: Prove search by authority, status filtering, detail page inspection, and record deletion.

**Independent Test**: Filter by query, view details page, and delete transaction with confirmation.

- [x] T022 [US4] Implement transaction search filter test using authority query in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T023 [US4] Implement transaction status dropdown filter test (`status=settled`) in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T024 [US4] Implement transaction detail view inspection test (`/en/console/{id}`) in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T025 [US4] Implement transaction delete flow with confirmation asserting HTTP 404 removal in `apps/web/tests/e2e/client-payments.spec.ts`

**Checkpoint**: Transactions can be searched, inspected, and cleaned up by the client.

---

## Phase 7: Gateways & Documentation Verification

**Purpose**: Verify gateway adapter cards, connection test buttons, and downloadable integration references.

- [x] T026 [P] Implement gateway adapter card inspection and credential test verification (`/en/gateways`) in `apps/web/tests/e2e/client-payments.spec.ts`
- [x] T027 [P] Make `apps/web/tests/run_e2e.sh` executable and verify execution permissions

---

## Phase 8: Polish & Validation Run

**Purpose**: Execute and validate the complete suite.

- [x] T028 Validate end-to-end suite execution via `bash apps/web/tests/run_e2e.sh`
- [x] T029 Confirm clean teardown with zero orphaned processes and removed temporary database files

---

## Dependencies & Execution Order

1. **Setup & Infrastructure (T001–T005)**: Required before running any tests.
2. **Foundational (T006–T007)**: Validates session handling for all subsequent stories.
3. **User Stories (T008–T025)**:
   - US1 (Payment lifecycle) is the primary MVP.
   - US2 (API keys) can execute independently after US5.
   - US3 (Webhooks) builds on US1 settlement flow.
   - US4 (Transactions) operates on payments created during test flows.
4. **Validation (T028–T029)**: Runs the entire suite.
