# Research: Payment Gateway Sandbox MVP (Phase 0)

**Feature**: specs/001-mvp | **Date**: 2026-09-23
**Input**: Technical Context in plan.md, spec.md, intake.md (assessment artifacts)

All Technical Context fields are resolved (no NEEDS CLARIFICATION remained — intake.md had already fixed the stack). Research below covers the best-practices/patterns tasks implied by those choices plus the spec's named risks.

## R1. Engine stack & framework

- **Decision**: Python 3.12 + FastAPI (async) for the engine; SQLAlchemy 2 + Alembic for persistence.
- **Rationale**: intake.md fixes Python as the engine language; FastAPI natively serves REST (control API + Zarinpal/IDPay JSON surfaces), mounts arbitrary paths for checkout pages, and has first-class async for webhook dispatch; SOAP handled by a dedicated lib (R4).
- **Alternatives considered**: Flask (weaker typing/async story), Django (batteries we don't need, heavier cold start in compose).

## R2. Adapter architecture (drop-in emulation)

- **Decision**: One abstract adapter interface — `create_payment`, `verify/settle`, `refund`, `checkout_page`, `callback_payload(stage, tx)` — with three implementations: Zarinpal (REST-style request/response), IDPay (REST-style), Behpardakht (SOAP/WSDL). Each adapter declares its own route prefix(s), credential scheme, and API unit (Rial/Toman) so the engine converts at the boundary (spec: Rial canonical).
- **Rationale**: FR-002/FR-004 + spec clarification on callback fidelity require per-gateway wire behavior including real callback payload shapes; a single interface keeps SC-003's 18/18 matrix testable uniformly and leaves the post-v1 adapter seam (Stripe, bank ports) open.
- **Alternatives considered**: protocol-agnostic "generic mock" (fails drop-in promise), one service per adapter (3× ops cost, wrong for compose v1).

## R3. Zarinpal & IDPay surfaces

- **Decision**: Emulate the well-documented sandbox-style flows of each API (payment request → redirect URL → verify) with in-scope operations only; unknown/unsupported operations return an explicit structured error (spec edge case).
- **Rationale**: Both are JSON/REST with publicly documented request/response shapes — no WSDL risk; drop-in means URL + merchant-id/credential swap only.
- **Alternatives considered**: full API-surface mirroring incl. admin/reporting endpoints — out of scope (YAGNI; byte-perfect explicitly excluded by spec).

## R4. Behpardakht (Mellat) WSDL fidelity — top schedule risk

- **Decision**: **Spike first** (timeboxed, first engineering task): hand-authored WSDL skeleton exposing only the in-scope operations (payment request, verify, reverse/refund) served as SOAP endpoints via a lightweight SOAP stack (Zeep for client-side contract tests; server accepts SOAP envelopes via FastAPI raw endpoints with XML built from templates). Validate drop-in against a real Mellat-style client SDK used in Iranian projects.
- **Rationale**: concept.md/decision.md name WSDL fidelity as the schedule's biggest unknown with an early-spike mitigation; a generated-from-official-WSDL server would drag in byte-perfect scope the spec excludes. Template-driven SOAP keeps the subset honest: unsupported operations → SOAP fault "not supported".
- **Alternatives considered**: full SOAP codegen from the official WSDL (scope creep, hard to bound), stub-only "return canned XML" (won't survive real SDK parsing — drop-in fails silently).
- **Exit criteria for spike**: a reference Iranian Mellat client lib completes initiate→verify against the spike; if not, fall back to documented-subset fidelity and note the gap in README positioning.

## R5. Scenario forcing mechanism (dashboard + CI)

- **Decision**: Scenario resolution order: per-transaction force → project default → built-in default (approve). Per-transaction force set via (a) dashboard, (b) control API `PATCH /transactions/{id}/scenario` or `POST` with `forced_scenario` inline (pre-seeding before initiate), (c) an optional request hint header (`X-Sandbox-Scenario`) honored at initiate for CI without pre-created rows. Time-based outcomes (timeout delay, pending→settle 5s) implemented with a lightweight in-process scheduler over DB-backed due-times (not an external queue).
- **Rationale**: spec FR-005 requires dashboard + non-interactive forcing; edge case fixes precedence (per-transaction wins); in-process scheduler avoids infra RabbitMQ/Celery for v1 scale (YAGNI), with due-times persisted so restarts don't lose pending transitions.
- **Alternatives considered**: Celery/Redis queue (extra container, overkill at tens of visitors), scenario only as project default (fails per-transaction requirement).

## R6. Webhook delivery to localhost from containers

- **Decision**: Engine performs outbound HTTP POSTs itself (async worker, bounded retry with backoff — spec assumption). In compose, webhook URLs targeting the host are documented as `http://host.docker.internal:<port>` (Linux: extra_hosts `host-gateway` entry) with plain `localhost` supported for non-container CI runs. Delivery attempts persisted as WebhookDelivery rows (payload, result, attempt count) before/after each try → feeds SC-005 and no-silent-loss edge case.
- **Rationale**: intake.md: "webhook studio ships self-host-first (Docker reaches the host)"; cloud tunnel agent is explicitly post-v1.
- **Alternatives considered**: polling/UI-only "fake deliveries" (fails US3), embedding a tunnel client now (named rabbit hole in concept.md).

## R7. Callback payload fidelity implementation

- **Decision**: Each adapter owns a `callback_payload()` builder emitting the real gateway's field names/shape for in-scope stages (spec clarification 2026-09-23). Contract tests snapshot per (adapter × stage) payloads so fidelity regressions fail CI.
- **Rationale**: drop-in requires the app's existing callback parser to work unchanged; snapshots make "real format" testable without live gateways.
- **Alternatives considered**: unified sandbox format (rejected by clarification), recording real gateway traffic (record/replay = post-v1 rabbit hole).

## R8. Dashboard & i18n/RTL

- **Decision**: Next.js App Router, `next-intl` with `fa`/`en` message catalogs, document `dir` swapped with locale (RTL for `fa`), Tailwind with logical properties (ms/me, start/end) so layout mirrors mechanically; Linear-dark theme via design tokens (CSS variables). Dashboard is a pure control-API client — no direct DB access.
- **Rationale**: intake fixes Next.js + Linear-dark + bilingual; logical CSS properties are the standard RTL-safe pattern; keeping UI on the control API means FR-010 headless parity by construction (the dashboard can't do anything scripts can't).
- **Alternatives considered**: runtime CSS re-baseline flipping (fragile), dashboard talking to DB directly (breaks headless-parity, duplicates authorization logic).

## R9. Data model persistence & history cap

- **Decision**: PostgreSQL 16 single database; history cap enforced transactionally on insert — after insert, delete oldest rows beyond 1000 per `project_id` (configurable constant); UsageMeter counters updated in the same transaction. State transitions for pending→settle/timeout driven by `due_at` timestamps + the R5 scheduler.
- **Rationale**: spec FR-006 cap + FR-011 meters; one DB keeps compose at three containers; same-transaction cap keeps meters and rows consistent (edge case).
- **Alternatives considered**: per-project logical purge jobs (more moving parts), append-only log w/ materialized views (over-engineered).

## R10. Hosted demo: email signup, rate limiting, isolation

- **Decision**: `demo/` layer in front of engine+dashboard images: free email signup via magic link (tokenized, no passwords — spec assumption), session cookie scopes every request to a `visitor_session` → bound `project_id`; rate limiting as a reverse-proxy concern (fixed-window per IP + per session on simulate endpoints) plus signup-spam throttle per email. Visitor isolation = strict `project_id` scoping on every control-API query (tenant key already in the model). Data expires with the shared 1000-cap project each visitor owns.
- **Rationale**: spec clarification 1 (email + rate limit + isolation); magic-link avoids password storage/verification surface entirely on personal infra; project-scoped queries are the cheapest correct isolation (multi-tenant hardening post-v1 per spec assumption).
- **Alternatives considered**: third-party auth provider (dependency + privacy overhead for a simulation tool), full user accounts with profiles (explicitly out per spec assumption), shared single demo project (fails isolation requirement).

## R11. One-command setup & distribution

- **Decision**: `docker compose up -d` from repo root as the documented bootstrap (FR-015 "one-command"), env-file driven config (`.env.example` committed), AGPL-3.0 LICENSE at root; README quickstart mirrors `quickstart.md`.
- **Rationale**: intake fixes Docker Compose; compose is the de-facto one-command standard for multi-service dev tools; AGPL chosen in intake to protect the future cloud tier.
- **Alternatives considered**: install script + native processes (matrix of host environments, loses "works identically everywhere"), Helm/k8s (wrong scale for localhost).

## R12. Testing strategy mapping to success criteria

- **Decision**: (1) pytest contract tests per adapter surface (R2/R3/R4 exit criteria); (2) snapshot tests for callback payloads (R7); (3) integration suite driving the 18/18 outcome×adapter matrix headless with pass/fail exit code (SC-003/SC-004); (4) webhook receiver test asserting ≥95% within 5s and retry visibility (SC-005); (5) Playwright smoke: FA/EN switch + RTL + dashboard flows (SC-006); (6) compose cold-start timing check against SC-001's 10-minute budget.
- **Rationale**: every SC gets a directly runnable check; contract/snapshot tests are the cheapest defense for a fidelity product.
- **Alternatives considered**: none material — this is the minimum check set ponytail requires for non-trivial logic.

## Open items carried to `/speckit.tasks`

- Schedule the Behpardakht WSDL spike as the first task (R4) with its exit-criteria check.
- Decide magic-link email transport for demo at deploy time (dev: log/link console; prod: any SMTP) — deploy config, not a code blocker.
