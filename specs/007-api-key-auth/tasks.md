---
description: "Task list template for feature implementation"
---

# Tasks: API Key Authentication

**Input**: Design documents from `/specs/007-api-key-auth/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

*(No additional setup required; Next.js and FastAPI environments are already configured)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 [P] Create `ApiKey` SQLAlchemy model in `apps/engine/src/models/api_key.py` (fields: id, user_id, name, key_hash, last_four, created_at, last_used_at, revoked_at)
- [X] T002 Generate Alembic migration for `ApiKey` model in `apps/engine/`
- [X] T003 [P] Implement API key generation and SHA-256 hashing utilities in `apps/engine/src/core/security.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create API Key (Priority: P1) 🎯 MVP

**Goal**: As a user of the cloud-hosted sandbox, I want to create an API key so that I can authenticate my programmatic requests or CLI tools.

**Independent Test**: Can be fully tested by creating a key via the UI and receiving the token string.

### Tests for User Story 1

- [X] T004 [P] [US1] Write integration test for `POST /api/v1/auth/api-keys` in `apps/engine/tests/api/test_api_keys.py`
- [X] T005 [P] [US1] Write Playwright E2E test for API key creation modal in `apps/web/tests/e2e/api_keys.spec.ts`

### Implementation for User Story 1

- [X] T006 [P] [US1] Create API endpoint `POST /api/v1/auth/api-keys` in `apps/engine/src/api/auth.py`
- [X] T007 [P] [US1] Create frontend API key creation modal component in `apps/web/src/components/api-keys/CreateKeyModal.tsx`
- [X] T008 [US1] Create frontend Settings > API Keys page in `apps/web/src/app/settings/api-keys/page.tsx` integrating the creation modal

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Authenticate via API Key (Priority: P1)

**Goal**: As a user, I want to use my generated API key to authenticate requests to the cloud-hosted sandbox API.

**Independent Test**: Can be fully tested by sending an API request with the key and verifying it succeeds.

### Tests for User Story 2

- [X] T009 [P] [US2] Write integration test for API key authentication middleware in `apps/engine/tests/api/test_api_keys.py`

### Implementation for User Story 2

- [X] T010 [P] [US2] Implement API key authentication dependency (Bearer token extractor and hash lookup) in `apps/engine/src/api/dependencies.py`
- [X] T011 [US2] Update sandbox API routes in `apps/engine/src/api/` to accept API key authentication alongside existing session auth

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Manage/Revoke API Keys (Priority: P2)

**Goal**: As a user, I want to view my active API keys and revoke them if they are compromised or no longer needed.

**Independent Test**: Can be fully tested by revoking a key and verifying that subsequent requests with that key are rejected.

### Tests for User Story 3

- [X] T012 [P] [US3] Write integration tests for listing (`GET`) and revoking (`DELETE`) API keys in `apps/engine/tests/api/test_api_keys.py`
- [X] T013 [P] [US3] Update Playwright E2E test to include listing and revoking API keys in `apps/web/tests/e2e/api_keys.spec.ts`

### Implementation for User Story 3

- [X] T014 [P] [US3] Create API endpoint `GET /api/v1/auth/api-keys` in `apps/engine/src/api/auth.py`
- [X] T015 [P] [US3] Create API endpoint `DELETE /api/v1/auth/api-keys/{id}` in `apps/engine/src/api/auth.py`
- [X] T016 [P] [US3] Implement frontend API keys list component in `apps/web/src/components/api-keys/ApiKeysList.tsx`
- [X] T017 [US3] Integrate the list component and revoke action into `apps/web/src/app/settings/api-keys/page.tsx`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T018 Run validation scenarios defined in `specs/007-api-key-auth/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2)

### Within Each User Story

- Tests should be written before implementation
- Models before services
- Backend endpoints before frontend components
- Integration components last

### Parallel Opportunities

- Foundational tasks T001 and T003 can be built in parallel.
- All User Stories can be worked on in parallel across backend/frontend domains.
- Backend API endpoints (T006, T014, T015) can be developed in parallel to frontend components (T007, T016).

---

## Parallel Example: User Story 1

```bash
# Launch backend and frontend parts of User Story 1 together:
Task: "T006 [P] [US1] Create API endpoint POST /api/v1/auth/api-keys in apps/engine/src/api/auth.py"
Task: "T007 [P] [US1] Create frontend API key creation modal component in apps/web/src/components/api-keys/CreateKeyModal.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
2. Complete Phase 3: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Foundational → Foundation ready
2. Add User Story 1 → Test independently
3. Add User Story 2 → Test authentication
4. Add User Story 3 → Test revocation
