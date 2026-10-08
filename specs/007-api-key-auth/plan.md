# Implementation Plan: API Key Authentication

**Branch**: `007-api-key-auth` | **Date**: 2026-10-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-api-key-auth/spec.md`

## Summary

Implement API Key authentication to allow users to authenticate programmatic requests to the cloud-hosted sandbox. The backend (FastAPI) will generate `ipg_key_` prefixed tokens, store only their SHA-256 hash, and authenticate `Bearer` requests. The frontend (Next.js) will provide a UI to create, list, and revoke these keys.

## Technical Context

**Language/Version**: Python 3.12 (Engine), TypeScript 5.4 (Web)

**Primary Dependencies**: FastAPI, SQLAlchemy, asyncpg (Engine) / Next.js, React, Tailwind (Web)

**Storage**: PostgreSQL (via SQLAlchemy/asyncpg)

**Testing**: pytest (Engine), Playwright (Web)

**Target Platform**: Cloud Hosted Sandbox (Web Service)

**Project Type**: Monorepo with Web Service and Frontend

**Performance Goals**: <50ms authentication overhead

**Constraints**: API keys must be shown only once. The full key must not be retrievable from the database.

**Scale/Scope**: Limit to 10 keys per user.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No specific constitution rules are violated. The plan adheres to typical security best practices (hashing secrets) and fits cleanly into the existing tech stack.

## Project Structure

### Documentation (this feature)

```text
specs/007-api-key-auth/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (future)
```

### Source Code (repository root)

```text
# Option 2: Web application (frontend + backend)
apps/engine/
├── src/
│   ├── models/
│   │   └── api_key.py      # SQLAlchemy model
│   ├── api/
│   │   ├── auth.py         # Endpoints for generating/revoking keys
│   │   └── dependencies.py # API key auth dependency
│   └── core/
│       └── security.py     # Hashing and key generation logic
└── tests/
    └── api/
        └── test_api_keys.py

apps/web/
├── src/
│   ├── components/
│   │   └── api-keys/       # Key listing, creation modal, revocation
│   └── app/
│       └── settings/
│           └── api-keys/   # Next.js route for the settings page
└── tests/
    └── e2e/
        └── api_keys.spec.ts
```

**Structure Decision**: Standard web application monorepo structure. Engine gets new models and API endpoints. Web gets a new settings page and components.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       |            |                                     |
