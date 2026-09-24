---

description: "Task list for Payment Gateway Sandbox (IPG Sandbox) MVP"
---

# Tasks: Payment Gateway Sandbox (IPG Sandbox) MVP

**Input**: Design documents from `/specs/001-mvp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (adapter-surfaces.md, control-api.md), quickstart.md

**Tests**: INCLUDED — explicitly requested by the feature specification (SC-003 "pass scripted checks", SC-004 headless pass/fail, quickstart.md validation scenarios) and mandated by research R12's test strategy.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md structure: `engine/` (Python), `dashboard/` (Next.js), `demo/` (hosted-demo layer), repo root for compose/LICENSE/README.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create monorepo structure per plan.md (`engine/`, `dashboard/`, `demo/`, `docker-compose.yml`, `.env.example`) at repository root
- [X] T002 Initialize engine Python 3.12 project at `engine/pyproject.toml` with FastAPI, SQLAlchemy 2, Alembic, httpx, zeep, pytest (research R1)
- [X] T003 [P] Initialize dashboard Next.js 14 App Router project at `dashboard/package.json` with next-intl and Tailwind (research R8)
- [X] T004 [P] Add AGPL-3.0 `LICENSE` at repository root and set license metadata in `engine/pyproject.toml` and `dashboard/package.json` (FR-015)
- [X] T005 [P] Configure linting/formatting: ruff config at `engine/ruff.toml`, eslint+prettier config at `dashboard/.eslintrc.json`
- [X] T006 Write `docker-compose.yml` at repository root: services `engine`, `dashboard`, `postgres:16`, with `extra_hosts: host.docker.internal:host-gateway` on engine (research R6/R11); commit `.env.example` with port/DB/delay overrides

**Checkpoint**: Repo skeleton exists; empty services defined

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Timeboxed Behpardakht WSDL spike: hand-authored WSDL skeleton for in-scope ops served from `engine/src/adapters/behpardakht/`, with exit-criteria check (reference zeep client completes initiate→verify) in `engine/tests/contract/test_behpardakht_spike.py`; record pass/fail outcome in `specs/001-mvp/research.md` notes (research R4 — FIRST engineering task, top schedule risk)
- [X] T008 Create SQLAlchemy models Project, AdapterConfig, Transaction, UsageMeter + enums (ScenarioOutcome, status, provider, api_unit) at `engine/src/models/` per data-model.md, enforcing verbatim constraints: `history_cap ≥ 1`; delays `≥ 0 and < 300`; `amount_rial ≥ 0`; one enabled AdapterConfig per `(project_id, provider)`; transitions only along the state-machine diagram (illegal transition raises, never silently mutates)
- [X] T009 Configure Alembic at `engine/alembic.ini` + `engine/alembic/` and generate initial migration covering the T008 models (indexes: `(project_id, created_at DESC)`, `(status, due_at)`, unique `(project_id, authority)`, partial-unique enabled `(project_id, provider)`)
- [X] T010 [P] Implement settings/env config at `engine/src/config.py` validating: `history_cap ≥ 1`, all delay knobs `≥ 0 and < 300`, defaults `pending_settle_delay_s = 5`, webhook retry max bounded (data-model.md, research R5/R11)
- [X] T011 Implement FastAPI app skeleton with machine-readable error envelope `{code, message, details?}` at `engine/src/api/app.py` and `engine/src/api/errors.py`; error codes per contracts/control-api.md (`validation_error`, `unsupported_operation`, `invalid_credentials`, `not_found`, `rate_limited`, `scenario_invalid`, `session_required`)
- [X] T012 Implement abstract adapter interface `create_payment`, `verify`, `refund`, `checkout_page`, `callback_payload(stage, tx)` at `engine/src/adapters/base.py`; each adapter declares route prefix, credential scheme, and `api_unit` (research R2)
- [X] T013 Implement scenario resolution at `engine/src/scenarios/resolve.py`: order = per-transaction force → project `default_scenario` → built-in `approve`; honors `X-Sandbox-Scenario` request header at initiate (edge-case precedence; research R5)
- [X] T014 Implement history-cap enforcement + UsageMeter bump in ONE database transaction on Transaction insert at `engine/src/services/cap.py`: after insert `DELETE` oldest rows beyond `history_cap` per `project_id`; `transactions_total` keeps counting, `history_retained = min(transactions_total, history_cap)` (FR-006/FR-011, data-model.md)
- [X] T015 Implement read-only control API endpoints at `engine/src/api/routes/`: `GET /api/v1/project`, `GET /api/v1/adapters`, `GET /api/v1/transactions` (paginated, newest first), `GET /api/v1/transactions/{id}` (incl. raw_request/raw_response), `GET /api/v1/meters` (counters only — no billing fields) per contracts/control-api.md
- [X] T016 Run `docker compose up -d` and verify all services healthy + `GET /api/v1/project` returns seeded default project (specs/001-mvp/quickstart.md §1 smoke)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Free local drop-in simulation (Priority: P1) 🎯 MVP

**Goal**: Developer runs the sandbox locally at zero cost, swaps endpoint URL + test credentials, and completes a full approved payment: initiate → hosted checkout → return → verify — across all three adapters.

**Independent Test**: quickstart.md §1–2 — one-command bootstrap, then approve flow with no signup/paywall; adapter contract tests green.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US1] Contract tests for Zarinpal surface (initiate/checkout/callback/verify paths, in-scope-only errors) at `engine/tests/contract/test_zarinpal_surface.py` per contracts/adapter-surfaces.md §1
- [ ] T018 [P] [US1] Contract tests for IDPay surface at `engine/tests/contract/test_idpay_surface.py` per contracts/adapter-surfaces.md §2
- [ ] T019 [P] [US1] Contract tests for Behpardakht SOAP subset parsed by zeep client at `engine/tests/contract/test_behpardakht_surface.py` per contracts/adapter-surfaces.md §3 (upgrades the T007 spike to full contract)
- [ ] T020 [P] [US1] Integration test: first approved payment end-to-end (initiate → checkout confirm → redirect → verify success, transaction `settled`/`approved` recorded) at `engine/tests/integration/test_first_payment.py` per quickstart §2

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement Zarinpal adapter at `engine/src/adapters/zarinpal/`: `POST {prefix}/request/payment`, `GET {prefix}/checkout/{authority}`, `GET {prefix}/callback/{authority}`, `POST {prefix}/payment/verification`; api_unit conversion at boundary, Rial canonical storage (contracts §1, clarification 4)
- [ ] T022 [P] [US1] Implement IDPay adapter at `engine/src/adapters/idpay/`: `POST {prefix}/payment`, `GET {prefix}/payment/start/{id}`, `POST {prefix}/payment/verify` per contracts §2
- [ ] T023 [US1] Promote spike to full Behpardakht adapter at `engine/src/adapters/behpardakht/`: `bpPaymentRequest`, `bpPaymentVerification`, `bpReverseTransaction` served as SOAP at `POST {prefix}/MellatPaymentGateway` (+ `?wsdl`); all other operations → SOAP fault `sandbox:UnsupportedOperation` (contracts §3, research R4 exit criteria)
- [ ] T024 [US1] Implement hosted checkout page rendering at `engine/src/checkout/`: confirm / fail / abandon controls, FA default with RTL, amount display only — never collects card data (contracts §5, FR-012)
- [ ] T025 [US1] Implement Transaction initiation + state machine at `engine/src/services/transactions.py`: `amount_rial ≥ 0` validation, legal transitions only per data-model.md, `effective_scenario` resolved via T013 at initiate, wire T014 cap+meters on insert
- [ ] T026 [US1] Implement `POST /api/v1/transactions` (pre-seed with `forced_scenario?`) and `DELETE /api/v1/transactions/{id}` at `engine/src/api/routes/transactions.py`; store raw_request/raw_response for dashboard detail (control-api.md, US4.4)
- [ ] T027 [US1] Run independent validation: specs/001-mvp/quickstart.md §1–2 timed, T017–T020 all green — **STOP and VALIDATE US1 before proceeding**

**Checkpoint**: User Story 1 fully functional and testable independently (MVP!)

---

## Phase 4: User Story 2 - Forced lifecycle scenarios (Priority: P2)

**Goal**: Force approve / decline / timeout / refund / pending→settle / verify-fail per transaction or as project default, from dashboard API or CI header, with correct timing.

**Independent Test**: quickstart §3–4 — 18/18 outcome×adapter matrix exits 0; pending→settle resolves ≈5 s after checkout.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T028 [P] [US2] Integration test: full scenario matrix — 6 outcomes (`approve, decline, timeout, refund, pending_settle, verify_fail`) × 3 adapters, assert contract-defined response per cell, machine-readable PASS/FAIL exit code at `engine/tests/integration/test_scenario_matrix.py` (SC-003)
- [ ] T029 [P] [US2] Unit tests: scenario precedence (per-transaction force beats project default beats built-in approve), illegal state transitions raise, timeout delay bounded `< 300` at `engine/tests/unit/test_scenarios.py`

### Implementation for User Story 2

- [ ] T030 [US2] Implement outcome logic shared across adapters at `engine/src/scenarios/outcomes.py`: decline → failure codes at verify; verify_fail → checkout succeeds, verify fails; timeout → bounded delay then timeout/exception response; refund → settle then `refunded`; pending_settle → `pending` then settled after `due_at` (FR-004, spec US2 acceptance 1–4)
- [ ] T031 [US2] Implement in-process scheduler over DB-backed `due_at` at `engine/src/scenarios/scheduler.py`: sweep `(status, due_at)` index for pending→settle (default +5 s), timeout completion, and abandoned-checkout expiry → `expired` (persisted due-times survive restart; research R5, data-model.md state machine)
- [ ] T032 [US2] Implement scenario/delay controls at `engine/src/api/routes/`: `PATCH /api/v1/transactions/{id}` (`forced_scenario`) and `PATCH /api/v1/project` (`default_scenario`, `pending_settle_delay_s`, `timeout_delay_s`, `webhook_retry_*`, `history_cap`) per contracts/control-api.md; PATCH affects only future initiations
- [ ] T033 [US2] Wire `X-Sandbox-Scenario` header into adapter initiate path (`engine/src/adapters/base.py` → `engine/src/scenarios/resolve.py`) so CI can force a scenario without a pre-created row (research R5, control-api.md)
- [ ] T034 [US2] Run independent validation: specs/001-mvp/quickstart.md §3 (18/18 green) and §4 (pending ≈5 s, overridable) — **STOP and VALIDATE US2**

**Checkpoint**: US1 + US2 both work independently; scenario coverage metric (SC-003) demonstrably met

---

## Phase 5: User Story 3 - Webhook / callback delivery (Priority: P3)

**Goal**: Deliver simulated webhooks/callbacks to configured localhost URLs in each gateway's REAL callback payload format, with retry/backoff and complete attempt history (no silent loss).

**Independent Test**: specs/001-mvp/quickstart.md §5 — receiver gets real-format payload < 5 s; killing the receiver yields visible `failed` rows + retries.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T035 [P] [US3] Snapshot contract tests: one golden payload per (adapter × stage) with real gateway field names at `engine/tests/contract/test_callback_payloads.py`; drift fails CI (research R7, clarification 2)
- [ ] T036 [P] [US3] Integration test: delivery latency ≥95% < 5 s to live receiver, unreachable target → `failed` row + retries per project policy, all attempts visible at `engine/tests/integration/test_webhook_delivery.py` (SC-005, no-silent-loss edge case)

### Implementation for User Story 3

- [ ] T037 [US3] Add WebhookDelivery model (fields: target_url, stage, payload, attempt, result `delivered|failed|pending`, response_status, error) at `engine/src/models/webhook.py` + Alembic migration at `engine/alembic/versions/`; every attempt INSERTed pending then UPDATEd with result (data-model.md)
- [ ] T038 [US3] Implement per-adapter payload builders `callback_payload(stage, tx)` at `engine/src/webhooks/payloads.py` emitting each real gateway's callback field names for in-scope stages (research R7)
- [ ] T039 [US3] Implement delivery worker at `engine/src/webhooks/worker.py`: async POST to callback_url / project webhook URL (incl. `host.docker.internal`), bounded retry with backoff from `Project.webhook_retry_max`/`webhook_retry_backoff_s`, persistent attempt rows (research R6, FR-007)
- [ ] T040 [US3] Implement delivery endpoints at `engine/src/api/routes/deliveries.py`: `GET /api/v1/deliveries?transaction_id=&result=`, `POST /api/v1/deliveries/{id}/retry`, `PUT /api/v1/project/webhook-url` per contracts/control-api.md
- [ ] T041 [US3] Trigger deliveries from outcome transitions in `engine/src/scenarios/outcomes.py` (settle/refund/notify stages) and run independent validation: quickstart.md §5 — **STOP and VALIDATE US3**

**Checkpoint**: US1–US3 independently functional; async settlement flows testable

---

## Phase 6: User Story 4 - Transaction dashboard with scenario controls (Priority: P4)

**Goal**: Professional Linear-dark bilingual (FA/EN, RTL) dashboard: transaction list/detail, force scenarios, inspect webhook deliveries, manage adapters — pure control-API client.

**Independent Test**: quickstart §7 — rows show adapter/amount(Rial)/status/scenario/timestamps; force `decline` from UI honored by next payment; FA ⇄ EN flips layout RTL/LTR with functional parity.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T042 [P] [US4] Playwright smoke: FA/EN switch with RTL flip, transactions list renders, force scenario from UI affects next payment, delivery detail visible at `dashboard/tests/smoke.spec.ts` (SC-006, quickstart §7)

### Implementation for User Story 4

- [ ] T043 [P] [US4] Scaffold dashboard app shell + Linear-dark theme tokens (CSS variables) + typed control-API client (NO direct DB access) at `dashboard/src/app/layout.tsx`, `dashboard/src/styles/theme.css`, `dashboard/src/lib/api.ts` (research R8)
- [ ] T044 [P] [US4] Implement i18n with next-intl: `fa.json`/`en.json` catalogs, locale middleware, document `dir` swap (RTL for `fa`), Tailwind logical properties (ms/me/start/end) at `dashboard/src/i18n/` and `dashboard/src/middleware.ts` (FR-009, research R8)
- [ ] T045 [US4] Implement transactions list + detail pages at `dashboard/src/app/transactions/`: columns adapter, amount (Rial canonical), status, scenario applied, timestamps; detail shows raw_request/raw_response + delivery summaries (US4 acceptance 1 & 4)
- [ ] T046 [P] [US4] Implement scenario controls UI (per-transaction force + project default + delay knobs) at `dashboard/src/components/ScenarioControls.tsx` calling `PATCH /transactions/{id}` and `PATCH /project` (US4 acceptance 3, FR-005)
- [ ] T047 [P] [US4] Implement webhook deliveries view (target, timestamp, outcome, payload, attempt) at `dashboard/src/app/webhooks/` with retry button (US3.3 via UI, FR-008)
- [ ] T048 [US4] Implement settings/adapters page (enable, test credentials, `POST /adapters/{id}/test` self-check with clear misconfig errors) at `dashboard/src/app/settings/` (FR-008, edge case)
- [ ] T049 [US4] Run independent validation: specs/001-mvp/quickstart.md §7 all four checks — **STOP and VALIDATE US4**

**Checkpoint**: US1–US4 independently functional; bilingual dashboard usable

---

## Phase 7: User Story 5 - CI-friendly headless use + free hosted demo (Priority: P5)

**Goal**: Entire sandbox drivable non-interactively from a pipeline (machine-readable PASS/FAIL, exit code, one adapter < 5 min); public demo gated by free email signup + rate limiting with per-visitor isolation.

**Independent Test**: quickstart §6 and §8 — CI script exits 0 in < 5 min; demo blocks simulation until magic-link verify; second session sees only its own data; hammering returns `rate_limited`.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T050 [P] [US5] Headless CI runner at `scripts/ci-scenario-run.sh`: drives initiate/scenarios/webhook asserts non-interactively for one adapter, emits machine-readable PASS/FAIL per step, exit code contract, total runtime < 5 min (SC-004, quickstart §6, FR-010)
- [ ] T051 [P] [US5] Integration tests: demo signup blocked-until-verify, visitor A cannot read visitor B rows (`session_required` / scoped queries), signup + simulate spam → `rate_limited` at `engine/tests/integration/test_demo_gate.py` (FR-014, clarification 1)

### Implementation for User Story 5

- [ ] T052 [US5] Add VisitorSession model (email citext, magic_link_token_hash single-use expiring, verified_at; local projects have NONE) at `engine/src/models/visitor.py` + Alembic migration at `engine/alembic/versions/` (data-model.md)
- [ ] T053 [US5] Implement demo layer at `demo/src/`: `POST /demo/signup` (rate-limited, spam-throttled per email), `POST /demo/verify` (magic link → session cookie binding visitor Project), `POST /demo/logout`; dev transport logs link, prod SMTP via env (research R10, control-api.md demo routes); routes absent in local profile (FR-014)
- [ ] T054 [US5] Enforce visitor isolation: project_id scoping on EVERY control-API query under the demo profile at `engine/src/api/scoping.py` (strict tenant key from session; research R10)
- [ ] T055 [US5] Wire `--profile demo` in `docker-compose.yml`: demo service in front of engine+dashboard images, rate limiting at proxy, per-visitor project creation on verify (FR-013/FR-014, research R10)
- [ ] T056 [US5] Run independent validation: specs/001-mvp/quickstart.md §6 (exit 0, < 5 min) and §8 (gate, isolation, rate limit) — **STOP and VALIDATE US5**

**Checkpoint**: All five stories independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057 [P] Write root `README.md` mirroring quickstart.md: one-command bootstrap, drop-in swap instructions, FA/EN mention, AGPL note (FR-015)
- [ ] T058 [P] History-cap validation test: insert >1000 transactions, assert `history_retained == history_cap`, `transactions_total` still counting, oldest dropped/newest intact at `engine/tests/integration/test_history_cap.py` (FR-006, quickstart §9)
- [ ] T059 [P] Simulation-guard test: engine makes NO outbound calls to real gateways (only configured callback/webhook targets) and no card-data fields exist in models/schemas at `engine/tests/unit/test_simulation_guard.py` (FR-012)
- [ ] T060 Run full quickstart validation §1–9 end-to-end incl. compose cold-start timing vs SC-001's < 10 min budget; fix any gaps found (quickstart.md)
- [ ] T061 Final pass: ruff/eslint clean, all contract+integration+Playwright suites green, `.env.example` complete, license headers present

---

## Phase 9: Convergence

**Purpose**: Gaps found by assessing the implemented code against spec.md, plan.md and tasks.md
after Phases 1–2 landed. Findings were verified against the code before being recorded; three
candidate findings were dropped because inspection showed them already satisfied (T012 declares
route prefix / credential scheme / api_unit; `config.py` covers all four project knobs).
Constitution is an unfilled template, so constitution checks were skipped.

- [ ] T062 Make the documented one-command bootstrap work end to end: land a minimal `dashboard/` Next.js skeleton so `docker compose up -d` brings ALL services healthy on a clean checkout, then re-run T016's assertion. Today `dashboard/src` does not exist, so the dashboard image cannot build and T016's "all services healthy" was never met — only `engine` + `postgres` were verified. **Overlaps T043**: completing T043 satisfies this; if T043 lands first this reduces to running the check per T016 (partial)
- [ ] T063 Reconcile the stale tracker on the base branch: `dev` still records T007–T016 unchecked while `feat/mvp-foundation` has them complete, so a future implement run on `dev` would redo finished work. Sequence: land the branch, then bring `specs/001-mvp/tasks.md` on the base in line with the completed work. Merge itself is a human action, not this task (missing)
- [ ] T064 Add the `notify` and `settle` callback stages to the adapter interface at `engine/src/adapters/base.py` per T038 (`stage: notify | settle | refund` in data-model.md, "callback notify" in contracts §4). Only `initiate/return/verify/refund` are declared today, so this blocks T038's payload builders (partial)
- [ ] T065 Mask or omit `AdapterConfig.credentials` on control-API responses served under the demo profile at `engine/src/api/routes/__init__.py` per FR-014. `_adapter_body` returns them verbatim — acceptable while values are test-only, but it becomes a real credential-display surface once T055 exposes `/adapters` to visitor sessions (partial)
- [ ] T066 Record the Behpardakht fidelity gap in README positioning per research R4's exit criteria ("if not, fall back to documented-subset fidelity and note the gap in README positioning"): the spike passed via the `zeep` reference client, not the required Iranian Mellat client lib, and the WSDL follows the contract's operation names (`bpPaymentRequest`) which differ from real PGW (`bpPayRequest`, comma-joined `return` responses). No README exists yet (missing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories; T007 (WSDL spike) runs FIRST within this phase (research R4 open item)
- **User Stories (Phase 3–7)**: All depend on Foundational completion
  - Sequential priority order recommended for single developer: P1 → P2 → P3 → P4 → P5
  - Stories are independently testable; parallelizable if staffed
- **Polish (Phase 8)**: Depends on all desired user stories being complete (T057–T059 can start as soon as their subject story lands)

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — no dependencies on other stories
- **US2 (P2)**: Starts after Foundational; consumes US1's initiate path but is independently testable via the matrix suite
- **US3 (P3)**: Starts after Foundational; attaches to outcome transitions from US1/US2 but delivery machinery is self-contained
- **US4 (P4)**: Starts after Foundational; pure control-API consumer — can be built against Foundational read endpoints + US2's PATCH endpoints (dashboard degrades gracefully: scenario controls enable as endpoints land)
- **US5 (P5)**: Headless runner (T050) needs US2's matrix; demo layer (T052–T055) needs only Foundational + scoping

### Within Each User Story

- Tests first (must FAIL before implementation)
- Models → services → endpoints → integration
- Story checkpoint validated before moving to next priority

### Parallel Opportunities

- Setup: T003, T004, T005 parallel with T002 (different files)
- Foundational: T010 parallel with T008/T009 (config vs models)
- US1: T017–T020 (four test files) parallel; T021+T022 (Zarinpal/IDPay adapters) parallel
- US2: T028, T029 parallel
- US3: T035, T036 parallel
- US4: T043+T044 parallel scaffold; T046+T047 parallel components
- US5: T050, T051 parallel
- Polish: T057, T058, T059 parallel
- Cross-staffing: after Foundational, US1 ∥ US4-scaffold ∥ US5-demo-layer are file-disjoint

---

## Parallel Example: User Story 1

```bash
# Launch all four US1 test files together (write FIRST, expect FAIL):
Task: "Contract tests Zarinpal surface → engine/tests/contract/test_zarinpal_surface.py"
Task: "Contract tests IDPay surface → engine/tests/contract/test_idpay_surface.py"
Task: "Contract tests Behpardakht SOAP → engine/tests/contract/test_behpardakht_surface.py"
Task: "Integration first approved payment → engine/tests/integration/test_first_payment.py"

# Then implement adapters in parallel (independent files):
Task: "Zarinpal adapter → engine/src/adapters/zarinpal/"
Task: "IDPay adapter → engine/src/adapters/idpay/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — T007 WSDL spike first)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: quickstart §1–2 + T017–T020 green
5. Publishable demo point: free local drop-in approve flow works

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. + US1 → test independently → deploy/demo (**MVP!**)
3. + US2 → 18/18 matrix green → deploy/demo (testing tool story lands)
4. + US3 → webhook fidelity + retry visible → deploy/demo (async flows)
5. + US4 → bilingual dashboard → deploy/demo (credibility/differentiator)
6. + US5 → CI runner + gated hosted demo → **launch-ready** (public repo + demo)
7. Polish → quickstart §1–9 full pass → release

### Parallel Team Strategy

1. Team completes Setup + Foundational together (T007 is the serial risk item)
2. Once Foundational is done:
   - Developer A: US1 (adapters) → then US2 (scenarios)
   - Developer B: US4 (dashboard scaffold + i18n, file-disjoint from engine)
   - Developer C: US5 demo layer (disjoint) + US3 webhook machinery after US2 transitions exist
3. Stories complete and integrate via the control API contract only

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story; Setup/Foundational/Polish have no story label
- Each user story is independently completable and testable; checkpoints are gates
- Tests requested by spec (SC-003/SC-004, quickstart) — verify they fail before implementing
- Commit after each task or logical group
- Constraint quotes in task descriptions are binding (history_cap ≥ 1, delays < 300, amount_rial ≥ 0, state-machine-only transitions, single-use magic tokens, counters-without-billing)
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
