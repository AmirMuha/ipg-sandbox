---
description: "Task list for 006-admin-ipg-visibility"
---

# Tasks: Admin IPG Visibility Control

**Input**: Design documents from `/specs/006-admin-ipg-visibility/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Test tasks ARE included. The spec's acceptance scenarios are the test oracle, and the
security properties (FR-001/002/003) are the kind that must be proven, not asserted.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and
delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

This is a two-app monorepo: `apps/engine/` (FastAPI) and `apps/web/` (Next.js). Paths below are
repo-relative and match plan.md.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration surface the whole feature depends on.

- [X] T001 Add `admin_emails` setting to `apps/engine/src/config.py`, parsed from the `ADMIN_EMAILS`
      env var as a comma-separated list, lowercased and stripped at parse time. Empty or unset yields
      an empty set — no admin, feature inert, never an auth bypass. No new dependency (stdlib `os`).
- [X] T002 Document `ADMIN_EMAILS` in `.env.example` with a comment that adding an admin requires a
      service restart.

**Note**: There is no migration, no new table, and no new package. This is deliberate — see
research.md D1. Do not add one.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The single read path and the admin guard. No user story can work without these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `apps/engine/src/services/provider_availability.py` with `platform_project(session)`
      returning the row where `user_id IS NULL`, per research.md D1. Returns `None` rather than
      raising when absent — the caller decides how to degrade (FR-023).
- [X] T004 [P] Add `get_offered_providers(session)` to `apps/engine/src/services/provider_availability.py`
      returning the sorted set of provider ids enabled on the platform project. Returns an empty set
      when the platform project is missing.
- [X] T005 [P] Add `is_offered(session, provider)` to `apps/engine/src/services/provider_availability.py`
      for the per-gateway check used by the checkout gate.
- [X] T006 Add `require_admin` dependency in `apps/engine/src/api/scoping.py`, resolving the current
      user via the existing `get_current_user`, then: no user → `session_required` 401; user email not
      in `settings.admin_emails` → `forbidden` 403. Reuse `hash_session_token`; do not re-implement
      session lookup. FR-001, FR-002, FR-003.
- [X] T007 Unit test the platform-project lookup in `apps/engine/tests/unit/test_provider_availability.py`:
      exactly one row has `user_id IS NULL`; user-owned projects are never selected; a database with
      no such row returns `None` and `get_offered_providers` returns an empty set rather than raising.
      This is the D1 assumption — if it fails, stop and fall back to a `GatewayState` table.
- [X] T008 [P] Unit test `require_admin` in `apps/engine/tests/unit/test_admin_guard.py`: allowlisted
      email passes; non-allowlisted signed-in user gets 403 with state unchanged; no session gets 401;
      allowlist matching is case-insensitive.

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 - Admin Controls Which Gateways Are Offered (Priority: P1) 🎯 MVP

**Goal**: Administrators are the only people who can change whether a gateway is offered platform-wide.

**Independent Test**: Sign in as an admin, withdraw a gateway, reload — state persisted. Then
attempt the same call as a non-admin and anonymously: both refused, state unchanged.

### Tests for User Story 1 ⚠️

> Write these FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Contract test the admin write path in
      `apps/engine/tests/contract/test_admin_providers.py`: allowlisted admin `PATCH
      /api/v1/admin/providers/{provider}` with `{"enabled": false}` → 200 and the state is persisted
      on the **platform** project; `{"enabled": true}` → 200; unknown provider → 404; non-boolean
      `enabled` → 422; non-admin → 403 with state unchanged; anonymous → 401 with state unchanged.
- [X] T010 [P] [US1] Contract test the last-gateway guard in
      `apps/engine/tests/contract/test_admin_providers.py`: with exactly one gateway offered,
      `PATCH {"enabled": false}` on it → 422 explaining at least one must stay offered, and it is
      still offered afterwards. FR-010.
- [X] T011 [P] [US1] Contract test the public read in
      `apps/engine/tests/contract/test_admin_providers.py`: `GET /api/v1/providers` returns
      `{"providers": [...], "count": N}` with no session, and reflects the admin's last write.

### Implementation for User Story 1

- [X] T012 [US1] Create the admin router in `apps/engine/src/api/admin_providers.py` with
      `GET /api/v1/providers` (unauthenticated, per research.md D5) and
      `PATCH /api/v1/admin/providers/{provider}` guarded by `require_admin` (T006). Return
      `{"providers": [...], "count": N}` from both.
- [X] T013 [US1] Implement the admin write in `apps/engine/src/api/admin_providers.py`: resolve the
      platform project's `AdapterConfig` for `{provider}`, set `enabled`, reject the write when it
      would leave zero gateways offered (FR-010), 404 on unknown provider. Do not accept
      `credentials` on this endpoint (FR-018).
- [X] T014 [US1] Register the admin router in `apps/engine/src/api/app.py` via `include_router`.
- [X] T015 [US1] Narrow `_PATCHABLE_ADAPTER` in `apps/engine/src/api/routes/__init__.py` to
      `{"credentials"}` and remove the `max_active_adapters` plan-limit block so `{"enabled": ...}`
      returns 422 with `details.allowed == ["credentials"]`. FR-017, FR-024. **Breaking change** —
      see T016.
- [X] T016 [US1] Update `apps/engine/tests/unit/test_ipg_toggle.py`: the existing
      `test_patch_adapter_unauthorized_in_demo_profile` and any assertion that a merchant enable
      succeeds must now expect 422. Do not delete the coverage — re-point it at the new contract.

### Admin UI for User Story 1 (added by /speckit-analyze C1)

> US1 scenario 1 requires the admin to "open the gateway management surface" and see every gateway
> with its state; FR-012 requires confirming the change in their language; SC-006 measures reaching
> the control in under 30 seconds. Without these the MVP is an API nobody can call.

- [X] T017 [P] [US1] Add the `forbidden` error code to `apps/engine/src/api/errors.py` and its
      constant, matching the `adapter_limit_exceeded` precedent — the set is explicitly extensible.
- [X] T018 [US1] Add `setPlatformProvider(provider, enabled)` to `apps/web/src/lib/api.ts` calling
      `PATCH /api/v1/admin/providers/{provider}` through the existing `CLIENT_API_BASE` path.
- [X] T019 [P] [US1] Add admin i18n keys to `apps/web/src/i18n/messages/fa.json` and
      `apps/web/src/i18n/messages/en.json`: `admin_providers` namespace with title, offered,
      withdrawn, saved, and last_gateway_guard strings. Both locales — T073 in this codebase was a
      bug for exactly this.
- [X] T020 [US1] Create `apps/web/src/components/AdminProviderList.tsx`: a client component listing
      every gateway with a toggle, calling T018, showing the saved confirmation (FR-012). Reuse the
      `AdapterSettings` panel and toggle styling — do not invent a second visual language.
- [X] T021 [US1] Create the admin route at
      `apps/web/src/app/[locale]/(console)/admin/providers/page.tsx` rendering `AdminProviderList`,
      and guard it so a non-admin is refused server-side before render (FR-004). Extend the guard in
      `apps/web/src/middleware.ts` — it currently only checks for a session cookie, which any signed-in
      merchant satisfies.

**Checkpoint**: User Story 1 functional — admin-only writes enforced AND reachable from a UI

---

## Phase 4: User Story 2 - Public Providers Page Reflects Gateway State (Priority: P2)

**Goal**: `/[locale]/providers` shows exactly the offered gateways, in both languages, uncached.

**Independent Test**: With a known state, load `/fa/providers` and `/en/providers` and compare the
set against `GET /api/v1/providers`.

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] Playwright test in `apps/web/tests/providers.spec.ts`: the page shows exactly
      the offered gateways; the same set appears in `fa` and `en` (FR-008); withdrawing a gateway
      while the page is open shows it gone on reload with no restart (SC-002, FR-022).
- [X] T023 [P] [US2] Playwright test in `apps/web/tests/providers.spec.ts`: the header count equals
      the number of cards rendered, and an empty offered set renders the page with no cards and no
      error (FR-023).

### Implementation for User Story 2

- [X] T024 [US2] Add `getPlatformProviders()` to `apps/web/src/lib/api.ts` calling
      `GET /api/v1/providers` through the existing `SERVER_API_BASE` path. No credentials sent.
- [X] T025 [US2] Filter the page in
      `apps/web/src/app/[locale]/(marketing)/providers/page.tsx`: keep the authored `GATEWAYS`
      array of 13 entries (research.md, "how the providers page filters") and filter it to offered
      ids. Add `export const dynamic = "force-dynamic"` — this page is already server-rendered and
      must not be cached (FR-022). Add `data-gateway-id={g.id}` to each rendered card: quickstart §7
      greps this attribute, so without it the project's own validation step cannot pass.
- [X] T026 [US2] Derive the header badges in the same file. Today they are literals — `۱۳ درگاه` and
      `۱۳ پایدار` at lines 270/272, and `۱۳ درگاه` in the `metadata.description` at line 9. All three
      must reflect the filtered list or the page claims thirteen while showing one.
- [X] T027 [US2] Handle the unreadable-state case in the same file: if the fetch fails, render the
      page with no gateways rather than falling back to the full list (FR-023).

**Checkpoint**: User Stories 1 and 2 both work — the visible half of the ask ships

---

## Phase 5: User Story 3 - Merchant Sees a Withdrawn Gateway (Priority: P2)

**Goal**: A merchant whose gateway was withdrawn sees why, and has no control to change it.

**Independent Test**: Withdraw a gateway, load a merchant's settings, confirm it is listed, marked
with the reason, and offers no switch.

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Test in `apps/engine/tests/contract/test_admin_providers.py`: `GET
      /api/v1/adapters` reports a derived `withdrawn_by_operator` flag per adapter, true exactly when
      the platform project has that gateway disabled. FR-016.
- [X] T029 [P] [US3] Playwright test in `apps/web/tests/settings.spec.ts` (new file; only
      `smoke.spec.ts` exists today): a withdrawn gateway is
      listed on the merchant's settings page, marked as withdrawn in the merchant's locale, with no
      control to change its availability; credentials editing still works (FR-018).

### Implementation for User Story 3

- [X] T030 [US3] Add the derived `withdrawn_by_operator` field to `_adapter_body` in
      `apps/engine/src/api/routes/__init__.py`, computed from the platform project. Derive it — do
      not store it on merchant rows (data-model.md, "Derived values").
- [X] T031 [US3] Remove the enable checkbox and `handleToggle` from
      `apps/web/src/components/AdapterSettings.tsx`, and render the locked withdrawn state with the
      reason when `withdrawn_by_operator` is true. FR-016, FR-017.
- [X] T032 [P] [US3] Add i18n keys to `apps/web/src/i18n/messages/fa.json` and
      `apps/web/src/i18n/messages/en.json` under `adapter_settings`: `withdrawn_by_operator`,
      `not_editable`, `withdrawn_badge`. Both locales, no hardcoded strings — T073 in this codebase
      was a bug for exactly this.
- [X] T033 [US3] Drop the `enabled` argument from `patchAdapter` in `apps/web/src/lib/api.ts` so the
      removed UI has no remaining caller.

**Checkpoint**: A withdrawal is never a silent failure for a merchant

---

## Phase 6: User Story 4 - Withdrawing Degrades Gracefully (Priority: P3)

**Goal**: Withdrawal never breaks an in-flight payment and never strands the platform at zero.

**Independent Test**: Withdraw a payment's gateway mid-flow; the payment completes and a new payment
through that gateway is refused.

### Tests for User Story 4 ⚠️

- [X] T034 [P] [US4] Test the availability gate in `apps/engine/tests/integration/test_first_payment.py`:
      a transaction already initiated on a gateway completes after that gateway is withdrawn
      (FR-011, SC-005); a new payment initiated after withdrawal is refused (FR-015).
- [X] T035 [P] [US4] Test concurrent admin writes in
      `apps/engine/tests/contract/test_admin_providers.py`: two admins writing the same gateway — the
      last write wins and both read back the resulting state (edge case, spec line 145).

### Implementation for User Story 4

- [X] T036 [US4] Gate `_resolve_adapter` in `apps/engine/src/api/routes/transactions.py` on the
      **platform** project's `AdapterConfig`, not the caller's. As written it filters only on
      `AdapterConfig.enabled.is_(True)` for the caller's own `project_id` — a per-project flag — so
      leaving it alone would let a merchant's row, not the platform's, decide availability and FR-015
      would not hold. Resolve the platform row separately via `is_offered` (T005) and require **both**
      the caller's row and the platform row to be enabled. Do not alter the 13 gateway routers.
- [X] T037 [US4] Verify the in-flight path is not gated — a transaction created before withdrawal
      must still reach its verify/settle steps. Gate only the entry point, never the completion path;
      confirm by reading the verify/settle handlers and asserting they never call `is_offered`. FR-011.

**Checkpoint**: All four stories independently functional

---

## Phase 7: Polish & Cross-Cutting

- [X] T038 [P] Confirm `max_active_adapters` is retained on `Project` but referenced nowhere that
      enforces it (FR-024). Leave the column; deleting it is a separate cleanup and a larger diff.
- [X] T039 Run the full quickstart validation in `specs/006-admin-ipg-visibility/quickstart.md`,
      all 10 sections, and record results.
- [X] T040 Confirm no audit trail of state changes was added — no `changed_by`, no `changed_at` on
      any model (FR-019). If one crept in during implementation, remove it.
- [X] T041 [P] Verify i18n completeness across the touched components: every new string added in
      T019 and T027 exists in **both** `fa.json` and `en.json`, and no hardcoded Persian or English
      remains in `AdminProviderList.tsx`, `AdapterSettings.tsx`, or `providers/page.tsx`.
- [X] T042 Run `cd apps/engine && poe check` (ruff lint + format) and `cd apps/web && pnpm lint`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **User Stories (Phases 3-6)**: All depend on Phase 2
  - US1 must land before US2 and US3 — both read state it writes
  - US2, US3, US4 are otherwise independent of each other
- **Polish (Phase 7)**: Depends on all desired stories

### User Story Dependencies

- **US1 (P1)**: After Phase 2. No story dependencies. **This is the MVP.**
- **US2 (P2)**: After Phase 2 **and US1's endpoint** (T012, T014). Reads the state US1 writes.
- **US3 (P2)**: After Phase 2 **and US1's endpoint** (T014). Reads the same state.
- **US4 (P3)**: After Phase 2 **and T005**. Applies the gate to the payment path.

### Within Each User Story

- Tests written and FAILING before implementation
- Resolver and guard before endpoints
- Endpoint before UI
- Story complete before moving on

### Parallel Opportunities

- T001, T002 parallel
- T004, T005 parallel (same module, independent functions)
- T008 parallel with T004/T005 (different file)
- T009, T010, T011 parallel (same file, independent test functions)
- T017, T019 parallel; T022, T023 parallel; T029, T030 parallel; T034, T035 parallel
- **`routes/__init__.py` is shared between US1 and US3**: T015 (US1) must land before T030 (US3)
- T012, T013 sequential — same file, T013 depends on T012's routes
- T018, T020, T021 sequential — T018 (`lib/api.ts`) before T020, T021 (`api.ts`, `middleware.ts`) after
- T025, T026, T027 sequential — same file (`providers/page.tsx`)

---

## Parallel Example: User Story 1

```bash
# Tests first, all three in one file but independent functions:
Task: "Contract test the admin write path in apps/engine/tests/contract/test_admin_providers.py"
Task: "Contract test the last-gateway guard in apps/engine/tests/contract/test_admin_providers.py"
Task: "Contract test the public read in apps/engine/tests/contract/test_admin_providers.py"

# Then implementation:
Task: "Create the admin router in apps/engine/src/api/admin_providers.py"   # then
Task: "Register the admin router in apps/engine/src/api/app.py"             # depends on the above
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational — **blocks everything**
3. Phase 3: User Story 1
4. **STOP and VALIDATE**: admin can toggle; non-admin and anonymous are refused
5. Ship if ready — the security property is live even before the page reflects it

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → admin-only writes enforced → **MVP**
3. US2 → providers page reflects state → the ask is now visible to users
4. US3 → merchants see why a gateway stopped working
5. US4 → graceful degradation guarantees

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Then: Developer A → US1, Developer B → US2, Developer C → US3
3. US4 last — it touches the payment path and benefits from the others being stable

---

## Notes

- **[P]** = different files, no dependencies
- **[Story]** labels map to spec.md user stories
- **Breaking change alert**: T015 changes an existing contract. T009-T011, T016, T023, T024, T028 all
  depend on the new behaviour. Update, do not delete, the existing coverage in
  `apps/engine/tests/unit/test_ipg_toggle.py`.
- **Gate alert**: T007 verifies the D1 assumption. If it fails, stop — the fallback is a
  `GatewayState` table and a migration, which changes Phase 2, not just T003.
- Two scope reductions are deliberate, not oversights: no audit trail (FR-019) and a config-based
  admin allowlist needing a restart (FR-014). T036 guards the first.
- Commit after each task or logical group. Stop at any checkpoint to validate the story independently.

---

## Phase 8: Convergence

- [X] T043 Create contract tests in `apps/engine/tests/contract/test_admin_providers.py` covering admin write path, last-gateway guard, and public read per T009-T011, US1/AC1-AC2, FR-001, FR-010 (missing)
- [X] T044 Update `apps/engine/tests/unit/test_ipg_toggle.py` to assert 422 validation_error when patching adapter enabled status per T016, FR-017 (partial)

