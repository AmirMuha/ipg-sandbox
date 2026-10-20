# Implementation Plan: Client Payment Journeys — End-to-End Proof

**Branch**: `008-client-e2e-tests` | **Date**: 2026-10-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-client-e2e-tests/spec.md`

## Summary

Build and run an unattended, browser-driven Playwright end-to-end test suite that exercises the entire IPG Sandbox platform from a merchant client's perspective: account creation and authentication, API key generation/revocation, payment simulation, hosted checkout confirmation/cancellation, backend payment verification, webhook event delivery tracking to a real client HTTP endpoint, and transaction search/inspection/deletion.

## Technical Context

**Language/Version**: TypeScript 5.4 (Web/Playwright E2E), Python 3.12 (Engine)

**Primary Dependencies**: `@playwright/test` (^1.63.0), Next.js 14.2, FastAPI, SQLAlchemy 2.0, aiosqlite, uvicorn

**Storage**: Ephemeral SQLite database per E2E test run (`/tmp/ipg_e2e_*.db`), automatically created and cleaned up on exit

**Testing**: Playwright (`apps/web/tests/e2e/client-payments.spec.ts`) with custom headless browser runner

**Target Platform**: Local Linux / CI environment (loopback HTTP services)

**Project Type**: Full-stack Monorepo (Next.js web app + FastAPI backend engine + Playwright test harness)

**Performance Goals**: Full suite execution < 3 minutes on standard developer machine

**Constraints**: Zero direct database access from tests (pure black-box client testing via UI and public HTTP endpoints); zero external network dependencies; self-contained cleanup of all spawned background processes and temp files

**Scale/Scope**: 7 comprehensive user journeys covering auth, API keys, gateways, transactions, checkouts, and webhooks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Test-First & Independence**: The E2E tests validate user-visible behaviors from external client perspective without coupling to database internals.
- **Simplicity (YAGNI)**: Reuses existing Playwright setup and Node built-in HTTP server (`node:http`) for callback verification without adding heavy external mock frameworks.
- **All Gates Passed**: No constitutional violations.

## Project Structure

### Documentation (this feature)

```text
specs/008-client-e2e-tests/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── test-matrix.md   # Test matrix and journey contract definitions
└── checklists/
    └── requirements.md  # Requirements quality checklist
```

### Source Code (repository root)

```text
apps/web/
├── playwright.config.ts                   # Playwright configuration for E2E runs
├── package.json                           # Contains test:e2e npm script
└── tests/
    ├── run_e2e.sh                         # Orchestration script (Engine + Next.js + Callback + Playwright)
    └── e2e/
        ├── client-payments.spec.ts        # Comprehensive client journey test suite
        ├── helpers.ts                     # Black-box API helpers and session management
        └── callback-server.mjs            # Loopback HTTP server capturing real webhook deliveries
```

**Structure Decision**: Place test assets in `apps/web/tests/e2e` alongside existing smoke test patterns, driven by a dedicated, hermetic shell runner (`run_e2e.sh`).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       |            |                                     |
