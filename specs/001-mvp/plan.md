# Implementation Plan: Payment Gateway Sandbox (IPG Sandbox) MVP

**Branch**: `001-mvp` | **Date**: 2026-09-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-mvp/spec.md`

## Summary

Build a free, self-hostable payment-gateway sandbox: one Docker Compose stack (Python engine + Next.js dashboard + PostgreSQL) that emulates Zarinpal, IDPay, and Behpardakht (Mellat) so Iranian developers can run full payment lifecycles (approve/decline/timeout/refund/pending→settle/verify-fail) on localhost with drop-in URL/credential swapping, real per-gateway callback payload formats, webhook delivery to localhost, forced-scenario controls (dashboard + headless), a bilingual FA/EN RTL Linear-dark dashboard, a 1000-transaction per-project history cap, Rial-canonical amounts, and a free email-gated hosted demo — AGPL-3.0, public repo + demo at launch.

## Technical Context

**Language/Version**: Python 3.12 (engine), TypeScript / Node 20 (dashboard)

**Primary Dependencies**: FastAPI + httpx + Zeep (Behpardakht SOAP/WSDL); Next.js 14+ App Router, next-intl (FA/EN RTL); Docker Compose

**Storage**: PostgreSQL 16 (transactions, deliveries, meters, projects, demo users); no other state stores in v1

**Testing**: pytest (engine unit/integration/contract), Playwright (dashboard smoke + RTL), scripted scenario matrix for SC-003 (18/18 outcome×adapter)

**Target Platform**: Linux/macOS/Windows dev machines via Docker Compose; hosted demo on requester's personal Linux infra

**Project Type**: web-service (multi-container: emulated gateway engine + dashboard SPA + database)

**Performance Goals**: SC-005 webhook ≥95% delivered to live localhost target within 5s; SC-004 full one-adapter scenario suite <5 min headless; checkout/verify responses feel instant (<100ms engine-side excluding forced delays)

**Constraints**: zero-cost local entry (no signup/paywall locally); simulation only — no real money, no card data, no production gateway calls; history cap 1000/project; forced delays bounded (timeout default seconds, pending→settle default 5s); demo gated by free email signup + rate limiting; AGPL-3.0

**Scale/Scope**: 3 adapters, ~6 entities, ~10 dashboard views, single-digit containers; 1 host, tens of demo visitors — not multi-tenant hardened (post-v1)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` is an **unfilled template** (placeholder headings only — no ratified principles, constraints, or governance rules). No enforceable gates exist; the gate is vacuously **PASS**. Constraints applied instead come from the spec itself (FR-001…FR-015) and intake decisions (AGPL-3.0, stack, ~1-month appetite). If a constitution is ratified later, re-run this check.

**Post-Phase-1 re-check**: PASS — design artifacts introduce no licenses, storage, or interfaces that contradict any project constraint (AGPL-3.0 preserved; simulation-only preserved; no billing/payments entity added).

## Project Structure

### Documentation (this feature)

```text
specs/001-mvp/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── adapter-surfaces.md
│   └── control-api.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/
├── engine/                  # Python gateway-simulation engine
│   ├── src/
│   │   ├── api/             # FastAPI app: control API + adapter route mounting
│   │   ├── adapters/        # zarinpal/, idpay/, behpardakht/ (+ base interface)
│   │   ├── scenarios/       # forced-outcome resolution + delayed transitions
│   │   ├── webhooks/        # delivery worker, retry/backoff, real payload builders
│   │   ├── models/          # SQLAlchemy models (see data-model.md)
│   │   └── checkout/        # hosted checkout/redirect page rendering
│   ├── tests/
│   │   ├── unit/
│   │   ├── contract/        # per-adapter surface + callback-format contracts
│   │   └── integration/     # 18/18 scenario matrix, webhook delivery
│   ├── pyproject.toml
│   └── package.json         # thin bridge for turbo task graph
├── dashboard/               # Next.js dashboard (FA/EN, RTL)
│   ├── src/
│   │   ├── app/             # App Router pages (transactions, scenario, webhooks, settings)
│   │   ├── components/
│   │   ├── i18n/            # next-intl messages fa.json / en.json, dir switching
│   │   └── lib/             # control-API client
│   └── package.json
└── demo/                    # hosted-demo glue: email signup gate, rate limit, visitor isolation
    ├── src/
    └── ...

packages/                    # reserved for shared TypeScript packages (e.g. control-api-client)

docker-compose.yml           # one-command bootstrap: engine + dashboard + postgres
package.json                 # root workspace root + turbo
pnpm-workspace.yaml
turbo.json
AGPL-3.0 LICENSE
README.md                    # quickstart mirror for public repo
```

**Structure Decision**: Three deployable units under `apps/` sharing one compose file — `apps/engine` (all emulation logic and control API), `apps/dashboard` (UI only, talks to control API), `apps/demo` (signup/rate-limit shell that wraps the same engine+dashboard images; the OSS images themselves stay login-free per FR-014). pnpm-workspace Turborepo monorepo (apps/* deployables + packages/* shared TS) matches intake.md's declared structure; adapters live behind one base interface so post-v1 gateways (Stripe etc.) plug in without touching the engine core.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

No constitution violations (constitution is an unfilled template — see Constitution Check). No complexity entries.
