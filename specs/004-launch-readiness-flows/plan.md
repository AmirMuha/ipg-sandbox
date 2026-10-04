# Implementation Plan: Launch Readiness Flows (004-launch-readiness-flows)

**Branch**: `004-launch-readiness-flows` | **Date**: 2026-10-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-launch-readiness-flows/spec.md`

## Summary

Implement the core launch and commercial lifecycle flows for IPG Sandbox:
1. **Authentication & Session Management**: Multi-provider login (Google OAuth, GitHub OAuth, and standalone email/password with scrypt hashing) isolating multi-tenant workspaces.
2. **Subscription & Plan Purchase**: Live Zarinpal PGv4 payment integration to upgrade from Developer Free tier to Team Plan (199,000 Toman/mo).
3. **Usage Tracking & Rate-Limit Enforcement**: Atomic rolling 24-hour request counter enforcing a hard 100 requests/day cap via HTTP 429 Too Many Requests, plus a max 2 active gateway limit on the Developer tier.
4. **Hosted Payment Simulation Checkout**: Server-rendered, bilingual (FA/EN), zero-card-data checkout page with authentic branding and automatic return callbacks.

## Technical Context

**Language/Version**: Python 3.12 (engine), TypeScript / Node 20 (dashboard)

**Primary Dependencies**: FastAPI, SQLAlchemy 2 (asyncio), asyncpg, httpx, Next.js 14, Tailwind CSS

**Storage**: PostgreSQL 16 (users, user_sessions, subscriptions, projects, usage_meters, transactions)

**Testing**: pytest, pytest-asyncio, Playwright, bash smoke test

**Target Platform**: Linux/macOS/Windows, Docker Compose or bare-metal local processes

**Project Type**: web-service (backend engine + frontend dashboard)

**Performance Goals**: Auth endpoints < 100ms; quota check & increment < 10ms (row lock); checkout rendering < 50ms

**Constraints**: Zero extra npm or python packages for auth/crypto (use stdlib `hashlib.scrypt`, `secrets`, `hmac`); hard block (HTTP 429) on daily quota overage; seamless local developer experience (`ENGINE_PROFILE=local` disables artificial caps)

**Scale/Scope**: 5 core flow dimensions (login, purchase, checkout, usage, limitations), 4 new API routes modules, 3 new database models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` has no custom project-specific prohibitions.
Constraints evaluated against project specifications:
- Zero external SaaS dependencies for authentication (self-contained database sessions).
- Strict adherence to AGPL-3.0 open-core boundary.
- Zero card data stored or collected on simulated checkout page.
- Gate status: **PASS**.

**Post-Phase-1 Re-check**: **PASS**. All design artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) follow minimal dependency footprint (stdlib scrypt/secrets, direct httpx for Zarinpal and OAuth) without adding Redis or external auth services.

## Project Structure

### Documentation (this feature)

```text
specs/004-launch-readiness-flows/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 decisions: Auth, Zarinpal billing, Quota 429, Checkout
├── data-model.md        # Phase 1 data models: User, UserSession, Subscription, UsageMeter
├── quickstart.md        # Phase 1 validation scenarios and curl verification steps
├── contracts/           # Phase 1 API specifications
│   ├── auth-api.md
│   ├── billing-api.md
│   └── quota-enforcement.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
apps/engine/
├── alembic/versions/         # Migration adding users, user_sessions, subscriptions, project extensions
├── src/
│   ├── api/
│   │   ├── auth.py           # Login, register, me, oauth handlers
│   │   ├── billing.py        # Zarinpal upgrade initiation and callback verification
│   │   ├── scoping.py        # Session-aware project scoping dependency
│   │   └── app.py            # Route mounts and quota enforcement middleware
│   ├── models/
│   │   ├── auth.py           # User, UserSession models
│   │   ├── billing.py        # Subscription model and Tier enums
│   │   └── models.py         # Project tier/cap fields and UsageMeter daily counters
│   ├── services/
│   │   ├── auth.py           # Scrypt hashing, token issuance, OAuth token exchange
│   │   ├── billing.py        # Zarinpal PGv4 client (request & verify)
│   │   └── quota.py          # Atomic 24h request window tracking & 429 evaluator
│   └── checkout/
│       └── page.py           # Multi-gateway hosted checkout simulation renderer
apps/dashboard/
├── src/
│   ├── app/[locale]/
│   │   ├── (marketing)/
│   │   │   ├── login/        # Login page connected to /api/v1/auth/login and OAuth links
│   │   │   └── pricing/      # Pricing page with active plan indicators and upgrade CTAs
│   │   └── (console)/
│   │       ├── settings/     # Workspace plan badge, quota bars, active adapter switches
│   │       └── transactions/ # Quota warning banners and transaction monitoring
│   └── lib/
│       └── api.ts            # Client bindings for auth, billing, and meters
```

**Structure Decision**: Multi-service monorepo (`apps/engine` + `apps/dashboard`). Auth and billing services reside in `apps/engine` for centralized security and API consistency; `apps/dashboard` renders user interfaces and consumes engine contracts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | All solutions adhere to stdlib and native features | Third-party auth (Clerk/NextAuth) and Redis rejected in favor of PostgreSQL + stdlib crypto |
