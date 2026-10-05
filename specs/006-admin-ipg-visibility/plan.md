# Implementation Plan: Admin IPG Visibility Control

**Branch**: `006-admin-ipg-visibility` | **Date**: 2026-10-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-admin-ipg-visibility/spec.md`

## Summary

Make gateway availability a platform-wide, administrator-only control, and make the public
`/fa/providers` page read that control instead of a hardcoded 13-entry array.

The technical approach follows clarification Q3: reuse the existing `AdapterConfig.enabled` column on
the **platform project** — the single project created at startup with `user_id IS NULL` — as the
store for global availability. No migration, no new table. A new admin-only router owns writes; a
small resolver module is the single read path that both the providers page and the checkout gate use,
so there is exactly one place that decides whether a gateway is offered.

## Technical Context

**Language/Version**: Python 3.12+ (engine) · TypeScript 5.4 / Next.js 14.2 (web)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x (async), Alembic, `enum.StrEnum` (stdlib) ·
Next.js 14 App Router, next-intl 3.12, React 18, Tailwind 3.4

**Storage**: PostgreSQL via SQLAlchemy async (`asyncpg`); SQLite via `aiosqlite` in tests. No new
storage. `AdapterConfig.enabled` is reused as-is.

**Testing**: `pytest` + `pytest-asyncio` (engine, `poe test`), Playwright + a smoke shell script (web)

**Target Platform**: Linux server; two containers (engine on 8080, web on 3000) behind Caddy in prod

**Project Type**: web-service (FastAPI control API) + web application (Next.js)

**Performance Goals**: One extra state read per providers page view (accepted at clarification Q4).
The gate adds no query to the checkout path beyond what it already does.

**Constraints**: No new dependency. No migration. `AdapterConfig.enabled` stays the single stored
truth for availability.

**Scale/Scope**: 13 gateways, 1 platform project, 1 administrator allowlist. Locale set: `fa`, `en`.

## Constitution Check

**Gate status: PASS — with a note.**

`.specify/memory/constitution.md` is the unfilled Spec Kit template. Every principle, section, and
governance rule is still a literal placeholder (`[PRINCIPLE_1_NAME]`, `[SECTION_2_CONTENT]`,
`[GOVERNANCE_RULES]`), with `Version: [CONSTITUTION_VERSION]`. There are no enforceable gates to
evaluate, so this check cannot fail on constitution grounds.

The one real project constraint found is enforced by the existing code rather than by the
constitution: `Patchable = {"enabled", "credentials"}` and the comment in
`src/adapters/registry.py` ("the 13 gateways never need a shared hand-maintained list") show this
project actively avoids hand-maintained duplication. This design honours that — the provider→adapter
mapping stays derived from the adapter classes, and the resolver is a single read path rather than a
second list of gateways maintained by hand.

Recommend running `/speckit-constitution` separately if governance is wanted before
`/speckit-tasks`. Not blocking.

## Project Structure

### Documentation (this feature)

```text
specs/006-admin-ipg-visibility/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api.md           # Phase 1 output
├── checklists/
│   └── requirements.md  # /speckit-clarify output
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
apps/engine/
├── src/
│   ├── config.py                      # + ADMIN_EMAILS setting
│   ├── api/
│   │   ├── admin_providers.py         # NEW: admin-only write router
│   │   ├── scoping.py                 # + platform_project dependency
│   │   ├── routes/__init__.py         # ~ patch_adapter: drop `enabled`, drop plan limit
│   │   └── app.py                     # + include admin router
│   ├── services/
│   │   └── provider_availability.py   # NEW: the single read path
│   └── models/models.py               # unchanged
└── tests/
    ├── unit/test_ipg_toggle.py        # extend: admin gate
    └── contract/test_admin_providers.py  # NEW

apps/web/
└── src/
    ├── app/[locale]/(marketing)/providers/page.tsx  # filter by live state
    ├── app/[locale]/(console)/settings/page.tsx      # withdraw reason, no toggle
    ├── components/AdapterSettings.tsx                # lock + withdrawn state
    ├── components/AdminProviderList.tsx              # NEW: admin surface
    ├── lib/api.ts                                    # + getPlatformProviders, admin calls
    └── i18n/messages/{fa,en}.json                    # + withdrawn/admin strings
```

**Structure Decision**: Keep the existing two-app monorepo. The engine is the control API and owns
the gate; the web app is a pure consumer. No new package, no new top-level directory. The one new
engine module (`services/provider_availability.py`) exists because two consumers need the same
decision — the providers page and the checkout gate — and duplicating that rule across routers is
exactly the hand-maintained duplication `registry.py` warns about.

## Phase 0 — Research

See [research.md](./research.md). Five decisions recorded:

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Platform project = the row with `user_id IS NULL` | Already created by `_seed_default_project`; stable, no migration |
| D2 | Admin = email allowlist from `ADMIN_EMAILS` | Settled at specify (FR-014) |
| D3 | New `PATCH /api/v1/admin/providers/{provider}` router | Keeps admin surface separable from the merchant API |
| D4 | Drop `enabled` from the merchant `PATCH /adapters` | Q5 removed the second writer |
| D5 | Public availability read is unauthenticated | The providers page is a marketing page |

## Phase 1 — Design & Contracts

- [data-model.md](./data-model.md) — platform project, resolver, withdrawn-by-operator derivation
- [contracts/api.md](./contracts/api.md) — new admin endpoints, changed merchant endpoint
- [quickstart.md](./quickstart.md) — runnable end-to-end validation

## Complexity Tracking

No constitution violations to justify — the constitution is an unfilled template. Two deliberate
scope reductions were made by choice during clarification, not as oversights, and are recorded here
so they are not "fixed" by a later reader who assumes they were accidents:

| Reduction | Why accepted | Revisit when |
|-----------|--------------|--------------|
| No audit trail of state changes (FR-019) | Single-operator platform; the admin is also the person who would be asked | More than one operator exists |
| Admin allowlist lives in config, so adding an admin needs a restart (FR-014) | Avoids a privilege column on `users` | Admin onboarding becomes frequent enough to annoy |
