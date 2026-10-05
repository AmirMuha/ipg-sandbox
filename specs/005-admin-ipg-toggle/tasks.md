# Tasks: Admin IPG Toggle

**Input**: Design documents from `/specs/005-admin-ipg-toggle/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/api.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

*(No setup tasks required. The foundation is already in place.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

*(No foundational tasks required. `AdapterConfig` model and `GET`/`PATCH` endpoints already exist.)*

---

## Phase 3: User Story 1 - View and Toggle IPG Status (Priority: P1) 🎯 MVP

**Goal**: Make Zarinpal the only enabled IPG by default, while allowing others to be enabled manually.

**Independent Test**: Register a new user and confirm only Zarinpal is enabled out-of-the-box. Check that the DB migration disables non-Zarinpal IPGs for existing projects.

### Tests for User Story 1 ⚠️

- [x] T001 [P] [US1] Add a test in `apps/engine/tests/api/test_auth.py` or a dedicated test file to assert that newly registered projects only have Zarinpal enabled.
- [x] T004 [P] [US1] Add a test in `apps/engine/tests/api/test_adapters.py` (or similar) to verify that unauthorized (non-admin) requests to `PATCH /api/v1/adapters/{id}` are rejected (SC-003).

### Implementation for User Story 1

- [x] T002 [US1] Update `seed_configs` in `apps/engine/src/adapters/registry.py` to set `enabled=True` for `Provider.zarinpal` and `enabled=False` for all other providers.
- [x] T003 [US1] Generate and write an Alembic migration in `apps/engine/alembic/versions/` to update existing `adapter_configs` rows in the database, setting `enabled = false` where `provider != 'zarinpal'`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T005 [P] Run `quickstart.md` validation to ensure the default state and toggle behavior work as expected end-to-end.

---

## Dependencies & Execution Order

### Phase Dependencies

- **User Story 1 (P1)**: No dependencies. Can start immediately.
- **Polish (Final Phase)**: Depends on US1 completion.

### Within Each User Story

- Test before implementation.
- `seed_configs` update (T002) and DB migration (T003) can be done in parallel or sequentially.

### Parallel Opportunities

- Tests (T001) and implementation (T002, T003) touch different files and can be parallelized.

---

## Parallel Example: User Story 1

```bash
# Launch implementation and test setup together:
Task: "Update seed_configs in apps/engine/src/adapters/registry.py"
Task: "Generate an Alembic migration in apps/engine/alembic/versions/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Write test for new default behavior.
2. Update `seed_configs`.
3. Create database migration.
4. **STOP and VALIDATE**: Run test suite and quickstart validation.
