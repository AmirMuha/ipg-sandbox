# Implementation Plan: Admin IPG Toggle

**Branch**: `005-admin-ipg-toggle` | **Date**: 2026-10-05 | **Spec**: [specs/005-admin-ipg-toggle/spec.md](spec.md)

**Input**: Feature specification from `/specs/005-admin-ipg-toggle/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

The feature provides a UI in the project dashboard to list and toggle the enabled/disabled state of Internet Payment Gateways (IPGs) such as Zarinpal. It ensures disabled IPGs are hidden from the checkout flow and persists this configuration.

## Technical Context

**Language/Version**: Python 3.12 (Engine), TypeScript 5.4 (Dashboard)

**Primary Dependencies**: FastAPI, SQLAlchemy (Engine); Next.js 14, React 18 (Dashboard)

**Storage**: PostgreSQL (via asyncpg)

**Testing**: pytest (Engine), Playwright (Dashboard)

**Target Platform**: Web Browser + REST API

**Project Type**: Monorepo with Web Application and API Service

**Performance Goals**: Sub-2-second visual confirmation of state changes in UI.

**Constraints**: Access to IPG settings must be restricted to project administrators (authenticated project owners).

**Scale/Scope**: Impacts the existing `AdapterConfig` per-project configuration and the checkout selection flow.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- (No constitution file rules found to violate)

## Project Structure

### Documentation (this feature)

```text
specs/005-admin-ipg-toggle/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
apps/engine/
├── src/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── adapters/
└── tests/

apps/dashboard/
├── src/
│   ├── app/[locale]/(console)/console/[id]/
│   ├── components/
│   └── lib/
└── tests/
```

**Structure Decision**: The API for toggling IPGs and the dashboard UI for it already exist. The implementation will only modify the engine's default configuration (`seed_configs`) to enable Zarinpal and disable others by default, and provide a database migration for existing projects.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
