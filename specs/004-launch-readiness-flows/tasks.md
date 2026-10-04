---
description: "Task list for Launch Readiness Flows implementation"
---

# Tasks: Launch Readiness Flows (004-launch-readiness-flows)

**Input**: Design documents from `/specs/004-launch-readiness-flows/`
(`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration and environment variables for launch flows

- [X] T001 Update environment configuration examples with OAuth and Zarinpal keys in `.env.example`
- [X] T002 [P] Extend configuration parser and validation in `apps/engine/src/config.py` for OAuth credentials, Zarinpal merchant credentials, and session cookie parameters

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database models, migration, and core authentication primitives required before any story implementation

**⚠️ CRITICAL**: Must complete before user story implementation begins

- [X] T003 [P] Create `User` and `UserSession` SQLAlchemy models in `apps/engine/src/models/auth.py` quoting verbatim constraints: `email` VARCHAR(255) unique lowercase, `password_hash` VARCHAR(255) nullable, `auth_provider` VARCHAR(32) ('local', 'github', 'google'), `oauth_id` VARCHAR(255) nullable, and `token_hash` VARCHAR(64) unique
- [X] T004 [P] Create `Subscription` SQLAlchemy model in `apps/engine/src/models/billing.py` quoting verbatim constraints: `tier` VARCHAR(32), `status` VARCHAR(32) ('pending', 'active', 'expired', 'cancelled'), `amount_rial` BIGINT, and `zarinpal_authority` VARCHAR(64) unique
- [X] T005 Extend `Project` and `UsageMeter` models in `apps/engine/src/models/models.py` with `tier` VARCHAR(32) default 'developer', `daily_requests_cap` INTEGER default 100, `max_active_adapters` INTEGER default 2, `requests_today` INTEGER default 0, and `window_started_at` TIMESTAMPTZ default now()
- [X] T006 Create Alembic migration script in `apps/engine/alembic/versions/0007_launch_readiness_tables.py` creating `users`, `user_sessions`, `subscriptions` tables and altering `projects` and `usage_meters`
- [X] T007 [P] Implement password hashing and token generation service in `apps/engine/src/services/auth.py` using stdlib `hashlib.scrypt` (N=16384, r=8, p=1) and `secrets.token_hex(32)`
- [X] T008 [P] Implement session validation and current-user dependency in `apps/engine/src/api/scoping.py` supporting `ipg_session` cookie and `Authorization: Bearer` token

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Hosted Payment Checkout Simulation (Priority: P1) 🎯 MVP

**Goal**: Complete, authentic simulated checkout flow with gateway branding, 15-minute timeout enforcement, and reliable merchant callbacks

**Independent Test**: Initiate a payment transaction for Zarinpal or Behpardakht, navigate to `http://localhost:8080/checkout/{authority}`, confirm or cancel payment, and verify browser redirects back to merchant callback URL with correct outcome parameters.

### Implementation for User Story 1

- [X] T009 [P] [US1] Unit tests for checkout session expiry and action form rendering in `apps/engine/tests/unit/test_checkout_page.py`
- [X] T010 [US1] Add 15-minute expiration check and auto-expiry transition to `TransactionStatus.expired` in `apps/engine/src/services/transactions.py`
- [X] T011 [US1] Enhance cancellation redirect with gateway-authentic return parameters in `apps/engine/src/checkout/page.py` and adapter routes
- [X] T012 [US1] Verify multi-gateway branded theme styling and bilingual FA/EN labels in `apps/engine/src/checkout/styles.py` and pass `provider=self.provider` across adapters

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 - User Login & Access Control (Priority: P1)

**Goal**: Allow developers to register and login via Google OAuth, GitHub OAuth, or email/password, isolating private project resources

**Independent Test**: Register a new user via `POST /api/v1/auth/register`, verify `POST /api/v1/auth/login` sets `ipg_session` cookie, access protected `/api/v1/auth/me`, and verify dashboard middleware redirects unauthenticated requests away from `/console`.

### Implementation for User Story 2

- [X] T013 [P] [US2] Contract and integration tests for register, login, me, and logout in `apps/engine/tests/contract/test_auth_api.py`
- [X] T014 [US2] Implement register, login, me, and logout endpoints in `apps/engine/src/api/auth.py` adhering to `specs/004-launch-readiness-flows/contracts/auth-api.md`
- [X] T015 [US2] Implement GitHub and Google OAuth2 authorization code exchange flows in `apps/engine/src/services/oauth.py` using `httpx`
- [X] T016 [US2] Implement OAuth initiation and callback routes (`/oauth/github`, `/oauth/google`) in `apps/engine/src/api/auth.py`
- [X] T017 [US2] Register auth router under `/api/v1/auth` in `apps/engine/src/api/app.py`
- [X] T018 [US2] Connect `LoginForm` in `apps/dashboard/src/app/[locale]/(marketing)/login/LoginForm.tsx` to `/api/v1/auth/login` and render field error alerts
- [X] T019 [US2] Update dashboard middleware in `apps/dashboard/src/middleware.ts` to inspect `ipg_session` cookie and guard `/console` routes with redirection to `/login`

**Checkpoint**: User Stories 1 and 2 functional and testable independently

---

## Phase 5: User Story 3 - Plan Selection & Purchase Flow (Priority: P2)

**Goal**: Allow users to select the Team Plan on the pricing page and complete subscription purchase via live Zarinpal gateway checkout

**Independent Test**: Issue `POST /api/v1/billing/upgrade`, retrieve Zarinpal authority URL, verify settlement callback via `GET /api/v1/billing/callback`, and confirm workspace tier transitions to `team`.

### Implementation for User Story 3

- [X] T020 [P] [US3] Unit and contract tests for Zarinpal upgrade initiation and callback in `apps/engine/tests/unit/test_billing_service.py`
- [X] T021 [US3] Implement Zarinpal PGv4 client (`payment/request.json` and `payment/verify.json`) in `apps/engine/src/services/billing.py`
- [X] T022 [US3] Implement billing endpoints (`POST /api/v1/billing/upgrade`, `GET /api/v1/billing/callback`, `GET /api/v1/billing/subscription`) in `apps/engine/src/api/billing.py` per `specs/004-launch-readiness-flows/contracts/billing-api.md`
- [X] T023 [US3] Register billing router under `/api/v1/billing` in `apps/engine/src/api/app.py`
- [X] T024 [US3] Connect upgrade CTA buttons in `apps/dashboard/src/app/[locale]/(marketing)/pricing/page.tsx` via `UpgradeButton.tsx` to `/api/v1/billing/upgrade`
- [X] T025 [US3] Display active subscription tier, status, and expiration in `apps/dashboard/src/app/[locale]/(console)/settings/page.tsx`

**Checkpoint**: User Stories 1, 2, and 3 functional and testable independently

---

## Phase 6: User Story 4 - Usage Tracking & Quota Metering (Priority: P2)

**Goal**: Accurately meter daily request counts, lifetime transactions, and active gateways, displaying consumption metrics in the console

**Independent Test**: Issue API requests, invoke `GET /api/v1/meters`, and confirm `requests_today` and `requests_remaining_today` increment atomically and match tier allowances.

### Implementation for User Story 4

- [X] T026 [P] [US4] Integration tests for 24-hour rolling request window and atomic meter increments in `apps/engine/tests/contract/test_quota_enforcement.py`
- [X] T027 [US4] Implement atomic daily request tracking and 24h window reset helper in `apps/engine/src/services/cap.py`
- [X] T028 [US4] Update `GET /api/v1/meters` handler in `apps/engine/src/api/routes/__init__.py` to return `tier`, `requests_today`, `daily_requests_cap`, `requests_remaining_today`, `active_adapters_count`, and `window_resets_at` per `specs/004-launch-readiness-flows/contracts/quota-enforcement.md`
- [X] T029 [US4] Add usage quota progress bar and request counters in `apps/dashboard/src/app/[locale]/(console)/settings/page.tsx`

**Checkpoint**: User Stories 1, 2, 3, and 4 functional and testable independently

---

## Phase 7: User Story 5 - Limitations & Restrictions Enforcement (Priority: P3)

**Goal**: Strictly enforce free tier daily request cap (HTTP 429) and active gateway adapter ceiling (max 2)

**Independent Test**: Send 101 requests on a Developer tier workspace and verify request 101 returns HTTP 429 with rate-limit headers; attempt enabling a 3rd gateway and verify HTTP 403 Forbidden.

### Implementation for User Story 5

- [X] T030 [P] [US5] Contract tests for HTTP 429 quota exhaustion and HTTP 403 adapter ceiling in `apps/engine/tests/contract/test_quota_enforcement.py`
- [X] T031 [US5] Implement request quota check and atomic increment in `apps/engine/src/services/cap.py` rejecting excess requests with HTTP 429 and rate-limit headers
- [X] T032 [US5] Add adapter ceiling validation in `PATCH /api/v1/adapters/{id}` in `apps/engine/src/api/routes/__init__.py` rejecting attempts > max_active_adapters with HTTP 403
- [X] T033 [US5] Render rate limit warning banner and upgrade pathway in `apps/dashboard/src/app/[locale]/(console)/settings/page.tsx`

**Checkpoint**: All 5 user stories functional, enforced, and verified

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Client bindings, documentation, and end-to-end smoke verification

- [X] T034 [P] Update TypeScript API interfaces and client methods in `apps/dashboard/src/lib/api.ts` for auth, subscription, and extended meter contracts
- [X] T035 Execute runnable validation scenarios from `specs/004-launch-readiness-flows/quickstart.md`
- [X] T036 Run comprehensive test suites: `pytest` in `apps/engine` and `pnpm test` in `apps/dashboard`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Independent, start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational. Can run in parallel with User Story 2.
- **User Story 2 (Phase 4)**: Depends on Foundational. Unlocks user workspace isolation.
- **User Story 3 (Phase 5)**: Depends on User Story 2 (requires authenticated user).
- **User Story 4 (Phase 6)**: Depends on Foundational and User Story 2.
- **User Story 5 (Phase 7)**: Depends on User Story 4 (meters must exist to be enforced).
- **Polish (Phase 8)**: Depends on all user stories complete.

### User Story Dependencies

```text
Foundational (Phase 2)
  ├── US1: Checkout Simulation (P1) [Independent]
  └── US2: User Login & Auth (P1)
        ├── US3: Zarinpal Purchase (P2)
        └── US4: Usage Metering (P2)
              └── US5: Limitations 429 (P3)
```

---

## Parallel Opportunities

- **Phase 1**: T001 and T002 can be executed in parallel.
- **Phase 2**: T003, T004, T007, and T008 can be executed in parallel.
- **Phase 3 & 4**: US1 (Checkout simulation) and US2 (Auth) can be worked on concurrently by separate developers.
- **Phase 5 & 6**: US3 (Billing) and US4 (Usage tracking) can run in parallel once US2 is complete.

---

## Implementation Strategy

### MVP Scope (User Story 1 + User Story 2)
1. Complete Setup (Phase 1) + Foundational (Phase 2).
2. Complete US1 (Hosted checkout simulation) to guarantee transaction testing works.
3. Complete US2 (User login & session control) to secure the workspace console.
4. Stop and validate: users can sign up, log in, and simulate payments.

### Incremental Delivery to Launch
5. Add US3 (Live Zarinpal billing) → Users can purchase Team plans.
6. Add US4 (Usage metering) → Real-time visibility into usage.
7. Add US5 (HTTP 429 & gateway caps) → Commercial restrictions enforced.
8. Run quickstart end-to-end tests → Project ready for public launch!
