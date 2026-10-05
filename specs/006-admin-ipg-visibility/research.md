# Phase 0 Research: Admin IPG Visibility Control

**Feature**: `006-admin-ipg-visibility` | **Date**: 2026-10-05

All `NEEDS CLARIFICATION` items from Technical Context are resolved below. The spec carried none; the
unknowns were the ones surfaced by reading the code during planning.

---

## D1: Identifying the "platform project" without a migration

**Question**: Clarification Q3 chose to reuse `AdapterConfig.enabled` on the default project as the
store for global availability, and flagged that this only works if a single unambiguous default
project exists. Does one?

**Decision**: The platform project is the `projects` row with `user_id IS NULL`.

**Rationale**: Verified in code, not assumed.

- `src/api/app.py:77` `_seed_default_project` creates exactly one project named `"default"`, with no
  `user_id` argument — so `user_id` is `NULL`. It returns early if any project already exists
  (`select(Project).limit(1)`), so exactly one such row is ever created.
- `src/api/auth.py:228` and `:454` — every self-registered or OAuth user gets a project with
  `user_id` set to their own id.
- Therefore `user_id IS NULL` selects the platform project and only the platform project, on both
  fresh and existing databases. The `Project` docstring already says "local self-host runs exactly
  one", which matches.

**Alternatives considered**:

- *`kind = 'demo'`* — rejected. `ProjectKind` has `local` and `demo`, but the platform project is
  created with the `local` default, and no code sets `demo` at creation. The discriminator does not
  identify the platform project.
- *Oldest project by `created_at`* — rejected. This is what `scoping.py:64` does as a last-resort
  fallback, but on a database where users registered before the platform project existed, "oldest"
  would be a merchant's project. Silent, catastrophic misread of a platform-wide flag.
- *A new `GatewayState` table* — rejected as unnecessary. It is the safe fallback if D1 ever fails,
  and costs one migration. Recorded in the spec as the fallback to reach for.

**Consequence**: A second `user_id IS NULL` row would silently break the guarantee. Worth a
`unique` partial index, noted in data-model.md as optional hardening rather than a requirement.

---

## D2: How administrator status is checked

**Decision**: `ADMIN_EMAILS` in engine configuration, a comma-separated list, compared
case-insensitively against the signed-in user's email.

**Rationale**: Settled by the user at specify time (FR-014), and it matches how the codebase already
reads configuration — `Settings.from_env()` in `src/config.py`, consumed in `api/app.py` and
`api/auth.py`. Emails are already stored lowercased and stripped (`auth.py`: `email = raw_email.strip().lower()`),
so the comparison is a plain `in` check against a lowercased allowlist, normalised once at startup.

**Alternatives considered**: A per-account `is_admin` column (rejected — a migration and a privilege
field on `users` for what is a one-operator deployment); a separate operator sign-in (rejected — a
whole new auth path for a privilege one person holds).

**Consequence**: Adding an admin needs a config change and restart. Recorded as an accepted cost in
the spec and in plan.md Complexity Tracking.

---

## D3: Where the admin write endpoint lives

**Decision**: A new router at `src/api/admin_providers.py`, mounted under `/api/v1/admin/providers`,
separate from the merchant `router` in `api/routes/__init__.py`.

**Rationale**: The merchant router and the admin surface have different authorisation, different
scoping (platform project vs the caller's project), and different audiences. Keeping them in
separate modules means an auth guard cannot be forgotten on one route while being added to another —
the failure mode that matters most here, since the whole feature is "only admin may do this".

**Alternatives considered**:

- *A guard parameter on the existing `patch_adapter`* — rejected. The merchant router resolves the
  caller's own project via `current_project`; the admin router must resolve the platform project
  instead. Reusing the same function would mean every admin route overrides its own scoping, which
  is where privilege bugs breed.
- *Reusing `PATCH /adapters/{id}` with an admin check inside* — rejected for the same reason, plus it
  leaves the merchant route and the admin route sharing a body shape where only one should exist.

---

## D4: What happens to the merchant's existing toggle

**Decision**: Remove `enabled` from the merchant-facing `PATCH /api/v1/adapters/{adapter_id}` and
drop the per-project plan-limit check (`max_active_adapters`) that guards it.

**Rationale**: Clarification Q5 removed the merchant toggle outright, making administrators the only
writer of availability. With one writer, the `active_count >= project.max_active_adapters` check at
`routes/__init__.py:300-323` can never be triggered by any merchant action, so leaving it would be a
rule with no reachable path. FR-024 makes the removal explicit rather than leaving dead logic.

**Important**: `_PATCHABLE_ADAPTER = {"enabled", "credentials"}` currently accepts `enabled`. Narrowing
it to `{"credentials"}` means a merchant POSTing `{"enabled": true}` now gets a 422 with
`details.allowed: ["credentials"]` rather than silently succeeding. That is the correct outcome and
matches FR-017, but it is a **breaking change to an existing contract** — `test_ipg_toggle.py` and
the settings page both exercise the old behaviour and must be updated, not left failing.

`credentials` stays merchant-writable. A merchant configures *their* credentials; they do not control
whether the gateway is offered. These are different concerns and Q5 only removed the second.

---

## D5: Who may read the public availability state

**Decision**: The public availability read is unauthenticated.

**Rationale**: `/fa/providers` is a public marketing page with no session — the existing middleware
(`apps/web/src/middleware.ts`) only guards `/console`, `/settings`, `/webhooks`. An authenticated-only
endpoint would mean SSR-ing the page without credentials, which is the "fetch failed" class of bug the
`SERVER_API_BASE` comment in `lib/api.ts` documents having already been hit once in this codebase.

The endpoint returns only which gateways are offered — public marketing information, already printed
on the page today. It exposes no credentials, no project data, no merchant information.

**Alternatives considered**: Serving the list from the engine to the page at build time (rejected —
breaks the "always fresh, no cache" decision at Q4).

---

## Resolved: how the providers page filters

**Decision**: The page keeps its authored `GATEWAYS` array of 13 descriptive entries and filters it
against the live set of offered provider ids. Authored content stays; availability is dynamic.

**Rationale**: The array carries specification tables, reference-document links and monograms that
live only in that file. Deleting entries would destroy content, and the alternative — moving it into
the database — is a much larger change than this feature warrants. Filtering keeps the single source
of truth for *what a gateway is* while making *whether it is offered* live.

The two page-level counts (`۱۳ درگاه` / `۱۳ پایدار` badges) are currently literals and must become
derived from the filtered list, or the page will claim 13 gateways while showing one.

---

## Open item carried into tasks

`max_active_adapters` data is retained on `Project` but becomes unenforced (FR-024). Nothing in this
feature deletes the column — that is a separate cleanup, and leaving it is the smaller diff.
