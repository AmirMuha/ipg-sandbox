---
description: "Task list for comprehensive Iranian IPG gateway adapters suite implementation"
---

# Tasks: Comprehensive Iranian IPG Gateway Adapters Suite

**Input**: Design documents from `/specs/003-implement-ipg-adapters/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/adapter-surfaces.md`, `quickstart.md`)

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/adapter-surfaces.md

**Organization**: Tasks are grouped by user story (P1 to P5) with foundational prerequisites to enable independent, incremental delivery and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initial model and typing updates across engine and dashboard

- [x] T001 Expand `Provider` enum with all 10 new gateways (`saman`, `sadad`, `parsian`, `pasargad`, `asan_pardakht`, `pardakht_novin`, `irankish`, `sizpay`, `fanava`, `sarmayeh`) in `apps/engine/src/models/enums.py`
- [x] T002 [P] Update dashboard TypeScript provider union type and adapter schemas in `apps/dashboard/src/lib/api.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and helpers required by all gateway adapters

**⚠️ CRITICAL**: Must complete before implementing gateway adapters

- [x] T003 Implement deterministic cardholder metadata generator (masked PAN using bank BINs `603799`, `621986`, `622106`, `502229`, `585983`, `627412`, `639607`, `603770`, 12-digit RRN, and 6-digit trace number) in `apps/engine/src/adapters/metadata.py`
- [x] T004 [P] Implement permissive and strict cryptographic signature helper (RSA PKCS#1 v1.5 with SHA1/SHA256 & HMAC) in `apps/engine/src/adapters/crypto.py`
- [x] T005 [P] Create unit tests for metadata and cryptographic helpers in `apps/engine/tests/unit/test_adapters_metadata.py`
- [x] T006 Implement multi-gateway auto-submitting POST form callback and hosted checkout renderer in `apps/engine/src/checkout/page.py`

**Checkpoint**: Foundation ready — gateway adapter implementations can begin.

---

## Phase 3: User Story 1 - Top-Tier Banking PSP Gateway Simulation (Priority: P1) 🎯 MVP

**Goal**: Deliver full drop-in emulation for the 5 most popular Iranian bank PSPs (Saman SEP, Sadad Melli, Parsian PEC, Pasargad PEP, Asan Pardakht) supporting initiation, hosted checkout, Shaparak POST callbacks, and verification.

**Independent Test**: Execute `apps/engine/tests/contract/test_top_tier_psps.py` asserting initiation, token generation, callback POST body, and verification for each of the 5 top-tier PSPs.

### Tests for User Story 1

- [x] T007 [P] [US1] Create contract tests for top-tier banking PSPs (Saman, Sadad, Parsian, Pasargad, Asan Pardakht) in `apps/engine/tests/contract/test_top_tier_psps.py`

### Implementation for User Story 1

- [x] T008 [P] [US1] Implement Saman (SEP) adapter with credential scheme `("terminal_id",)` in `apps/engine/src/adapters/saman/adapter.py`
- [x] T009 [US1] Implement Saman (SEP) REST and SOAP routes (token request `/onlinepg/onlinepg`, checkout `/checkout/{token}`, verification `/verifyTxn`, reversal `/reverseTxn`, and WSDL endpoint) in `apps/engine/src/adapters/saman/routes.py`
- [x] T010 [P] [US1] Implement Sadad Bank Melli adapter with credential scheme `("terminal_id", "merchant_id", "terminal_key")` in `apps/engine/src/adapters/sadad/adapter.py`
- [x] T011 [US1] Implement Sadad REST routes (`/api/v0/Request/PaymentRequest`, checkout `/checkout/{token}`, callback POST, and `/api/v0/Advice/Verify`) in `apps/engine/src/adapters/sadad/routes.py`
- [x] T012 [P] [US1] Implement Parsian PEC adapter with credential scheme `("pin",)` in `apps/engine/src/adapters/parsian/adapter.py`
- [x] T013 [US1] Implement Parsian PEC WSDL file and SOAP endpoints (`SalePaymentRequest`, `ConfirmPayment`, `ReversalProcess`) in `apps/engine/src/adapters/parsian/routes.py` and `apps/engine/src/adapters/parsian/parsian.wsdl`
- [x] T014 [P] [US1] Implement Pasargad PEP adapter with credential scheme `("merchant_code", "terminal_code")` in `apps/engine/src/adapters/pasargad/adapter.py`
- [x] T015 [US1] Implement Pasargad PEP REST routes (`/api/payment/purchase`, `/api/payment/verify`) with optional RSA signature verification in `apps/engine/src/adapters/pasargad/routes.py`
- [x] T016 [P] [US1] Implement Asan Pardakht (AP) adapter with credential scheme `("merchant_id", "username", "password")` in `apps/engine/src/adapters/asan_pardakht/adapter.py`
- [x] T017 [US1] Implement Asan Pardakht REST and SOAP routes (`/Token`, `/Verify`, and WSDL) in `apps/engine/src/adapters/asan_pardakht/routes.py`
- [x] T018 [US1] Register top-tier PSP routers in `apps/engine/src/api/app.py` and seed default adapter configs in database

**Checkpoint**: User Story 1 complete — all 5 top-tier Iranian banking PSPs are fully functional and testable.

---

## Phase 4: User Story 2 - Specialized Bank and Institutional PSP Adapters (Priority: P2)

**Goal**: Deliver authentic emulation for specialized institutional PSPs (Pardakht Novin / PNA, IranKish, Fanava Card, Bank Sarmayeh).

**Independent Test**: Run `apps/engine/tests/contract/test_specialized_psps.py` asserting initiation and verify payloads against official schemas.

### Tests for User Story 2

- [x] T019 [P] [US2] Create contract tests for specialized PSPs (Pardakht Novin, IranKish, Fanava, Sarmayeh) in `apps/engine/tests/contract/test_specialized_psps.py`

### Implementation for User Story 2

- [x] T020 [P] [US2] Implement Pardakht Novin (PNA) adapter with credential scheme `("merchant_id", "password")` in `apps/engine/src/adapters/pardakht_novin/adapter.py`
- [x] T021 [US2] Implement Pardakht Novin routes and WSDL service in `apps/engine/src/adapters/pardakht_novin/routes.py`
- [x] T022 [P] [US2] Implement IranKish adapter with credential scheme `("terminal_id", "acceptor_id", "pass_phrase")` in `apps/engine/src/adapters/irankish/adapter.py`
- [x] T023 [US2] Implement IranKish REST routes (`/api/v1/token`, `/api/v1/verify`) in `apps/engine/src/adapters/irankish/routes.py`
- [x] T024 [P] [US2] Implement Fanava Card adapter with credential scheme `("merchant_id", "password")` in `apps/engine/src/adapters/fanava/adapter.py`
- [x] T025 [US2] Implement Fanava Card routes and SOAP endpoints in `apps/engine/src/adapters/fanava/routes.py`
- [x] T026 [P] [US2] Implement Bank Sarmayeh adapter with credential scheme `("merchant_id", "terminal_id", "password")` in `apps/engine/src/adapters/sarmayeh/adapter.py`
- [x] T027 [US2] Implement Bank Sarmayeh routes in `apps/engine/src/adapters/sarmayeh/routes.py`
- [x] T028 [US2] Register specialized PSP routers in `apps/engine/src/api/app.py` and seed default configs in database

**Checkpoint**: User Stories 1 & 2 complete — all 9 banking PSPs fully operational.

---

## Phase 5: User Story 3 - Payment Facilitator (Pardakht-Yar) Adapters (Priority: P3)

**Goal**: Deliver modern REST payment facilitator emulation for SizPay, while aligning ZarinPal and IDPay with shared metadata generators.

**Independent Test**: Execute `apps/engine/tests/contract/test_payment_facilitators.py` asserting JSON request/response formats and multi-status verification codes (100 vs 101).

### Tests for User Story 3

- [x] T029 [P] [US3] Create contract tests for payment facilitators (SizPay, ZarinPal, IDPay) in `apps/engine/tests/contract/test_payment_facilitators.py`

### Implementation for User Story 3

- [x] T030 [P] [US3] Implement SizPay adapter with credential scheme `("merchant_id", "terminal_id", "username", "password")` in `apps/engine/src/adapters/sizpay/adapter.py`
- [x] T031 [US3] Implement SizPay REST routes (`/api/Payment/Token`, `/api/Payment/Confirm`) in `apps/engine/src/adapters/sizpay/routes.py`
- [x] T032 [P] [US3] Refactor ZarinPal and IDPay adapters to utilize centralized `metadata.py` for cardholder PAN and RRN in `apps/engine/src/adapters/zarinpal/adapter.py` and `apps/engine/src/adapters/idpay/adapter.py`
- [x] T033 [US3] Register SizPay router in `apps/engine/src/api/app.py` and seed default config in database

**Checkpoint**: User Stories 1, 2, & 3 complete — all 13 adapters implemented.

---

## Phase 6: User Story 4 - Universal Scenario Simulation Across All Gateways (Priority: P4)

**Goal**: Enable protocol-accurate error and lifecycle simulations (approved, declined, timeout, refund, pending settle, verify failure) across all 13 gateways.

**Independent Test**: Execute `apps/engine/tests/integration/test_all_adapters_scenarios.py` verifying that every adapter returns authentic status codes for all 6 scenarios.

### Implementation for User Story 4

- [x] T034 [P] [US4] Implement universal gateway scenario mapping matrix (approve, decline, timeout, refund, pending_settle, verify_fail) in `apps/engine/src/scenarios/adapter_mappings.py`
- [x] T035 [US4] Wire scenario mapping into initiation, callback, and verification across all 13 adapter route handlers in `apps/engine/src/scenarios/outcomes.py`
- [x] T036 [US4] Enforce idempotent duplicate verification rejection per gateway (e.g. ZarinPal 101, SEP -6, Sadad 102) in `apps/engine/src/services/transactions.py`
- [x] T037 [US4] Implement integration scenario matrix tests covering all 13 gateways × 6 scenarios in `apps/engine/tests/integration/test_all_adapters_scenarios.py`

**Checkpoint**: User Story 4 complete — all 13 gateways accurately simulate realistic failure modes and lifecycles.

---

## Phase 7: User Story 5 - Gateway-Branded Hosted Checkout Experience (Priority: P5)

**Goal**: Provide realistic visual identity, Persian/English localization, and interactive scenario controls for all 13 hosted checkout pages.

**Independent Test**: Run `apps/engine/tests/unit/test_checkout_branding.py` verifying that every adapter's checkout HTML contains authentic logos, titles, and action controls.

### Implementation for User Story 5

- [x] T038 [P] [US5] Add visual branding styles, SVG logos, and Persian titles for all 13 gateways in `apps/engine/src/checkout/styles.py`
- [x] T039 [US5] Implement interactive scenario action buttons and auto-submitting POST form templates in `apps/engine/src/checkout/page.py`
- [x] T040 [US5] Add unit tests for checkout page rendering and language negotiation (FA/EN) in `apps/engine/tests/unit/test_checkout_branding.py`

**Checkpoint**: User Story 5 complete — interactive checkout pages match gateway styling.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Dashboard alignment, documentation, and end-to-end quickstart validation

- [x] T041 [P] Update dashboard provider catalog and gateway badges in `apps/dashboard/src/app/[locale]/(marketing)/providers/page.tsx`
- [x] T042 [P] Update dashboard SimulateModal dropdown to list all 13 gateways in `apps/dashboard/src/components/SimulateModal.tsx`
- [x] T043 [P] Update engine and gateway API documentation in `docs/README.md`
- [x] T044 Execute complete quickstart validation suite per `specs/003-implement-ipg-adapters/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Story 1 (Phase 3 - P1)**: Depends on Foundational completion.
- **User Story 2 (Phase 4 - P2)**: Depends on Foundational completion; can run in parallel with US1.
- **User Story 3 (Phase 5 - P3)**: Depends on Foundational completion; can run in parallel with US1/US2.
- **User Story 4 (Phase 6 - P4)**: Depends on US1, US2, and US3 adapter routes being in place.
- **User Story 5 (Phase 7 - P5)**: Depends on Foundational checkout renderer (T006).
- **Polish (Phase 8)**: Depends on all user story phases being complete.

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel.
- **Phase 2**: T003, T004, and T005 can run in parallel.
- **Phase 3 (US1)**: Adapter implementations T008, T010, T012, T014, T016 can all run in parallel across separate files.
- **Phase 4 (US2)**: Adapter implementations T020, T022, T024, T026 can run in parallel across separate files.
- **Phase 5 (US3)**: T030 and T032 can run in parallel.
- **Phase 8**: T041, T042, and T043 can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1: Saman, Sadad, Parsian, Pasargad, Asan Pardakht).
3. Validate Top-Tier PSP contract tests (`pytest apps/engine/tests/contract/test_top_tier_psps.py`).
4. **Deliver MVP**: The 5 most critical banking PSPs in Iran are now fully operational.

### Incremental Delivery

1. Foundation + US1 → Top-Tier Banking PSPs working (MVP).
2. Add US2 → Specialized & Institutional PSPs working (PNA, IranKish, Fanava, Sarmayeh).
3. Add US3 → SizPay added; ZarinPal & IDPay aligned.
4. Add US4 → Universal 13×6 scenario matrix validated.
5. Add US5 → Branded hosted checkout screens for all 13 gateways.
6. Phase 8 → Dashboard dropdowns & documentation polished.

## Phase 9: Convergence

- [x] T045 Implement top-tier banking PSP adapters, routes, WSDLs, and tests (Saman, Sadad, Parsian, Pasargad, Asan Pardakht) per US1 (missing)
- [x] T046 Implement specialized institutional PSP adapters, routes, and tests (Pardakht Novin, IranKish, Fanava, Sarmayeh) per US2 (missing)
- [x] T047 Implement SizPay adapter, routes, tests, and refactor ZarinPal/IDPay to use centralized metadata per US3 (missing)
- [x] T048 Update Provider union type to include all 13 gateways in apps/dashboard/src/lib/api.ts per FR-001 (partial)
- [x] T049 Register all 10 new gateway routers in apps/engine/src/api/app.py and seed default configs per FR-002 (partial)
- [x] T050 Implement universal gateway scenario mapping matrix and wire it into all adapter routes per FR-008 (missing)
- [x] T051 Enforce idempotent duplicate verification rejection in apps/engine/src/services/transactions.py per FR-011 (missing)
- [x] T052 Add visual branding styles, interactive scenario controls, and auto-submitting POST forms to checkout page per FR-004 and FR-005 (partial)
- [x] T053 Update dashboard provider catalog, SimulateModal fallback, and docs/README.md per plan: Polish (missing)
