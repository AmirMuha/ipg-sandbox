# Phase 1 Data Model: Admin IPG Visibility Control

**Feature**: `006-admin-ipg-visibility` | **Date**: 2026-10-05

## Schema changes

**None.** No migration, no new table, no new column.

Global availability is stored in the existing `AdapterConfig.enabled` column, scoped to the platform
project. See [research.md](./research.md) D1 for why this is safe and what would invalidate it.

## Entities

### PlatformProject (existing `projects` row, not a new entity)

The single project holding platform-wide gateway availability.

| Field | Type | Rule |
|-------|------|------|
| `id` | UUID | PK |
| `user_id` | UUID \| NULL | **`NULL` identifies the platform project.** Exactly one such row exists, created by `_seed_default_project` (`src/api/app.py:77`) |
| `kind` | enum | `local` — not a reliable discriminator, see D1 |
| `max_active_adapters` | int | Retained but **unenforced** (FR-024) |

**Identification rule**: `user_id IS NULL`.

```sql
SELECT p FROM projects p WHERE p.user_id IS NULL LIMIT 1
```

**Failure mode**: if no such row exists (a database created before `_seed_default_project` ran, or
one where every project belongs to a user), the availability gate has nothing to read. The resolver
must treat this as "no gateways offered" and let the page render empty rather than raising — FR-023.

**Optional hardening** (not required, one line in a migration if wanted):

```sql
CREATE UNIQUE INDEX ix_projects_single_platform ON projects ((true)) WHERE user_id IS NULL;
```

Not adding it: a migration was explicitly avoided in Q3, and `_seed_default_project` already
guarantees uniqueness by returning early. Revisit if a second code path ever creates projects.

### Gateway availability (existing `AdapterConfig` row, scoped to the platform project)

| Field | Type | Rule |
|-------|------|------|
| `project_id` | UUID | FK → `projects.id`; the **platform** project for availability reads |
| `provider` | enum | Gateway id, e.g. `zarinpal`. Unchanged |
| `enabled` | boolean | **`true` = offered platform-wide.** Reused as the global state |
| `credentials` | JSON | Merchant-specific. Untouched by this feature (FR-018) |

**State transitions** (admin write, D3 router):

```text
                admin PATCH {enabled: true}
   withdrawn  ──────────────────────────────▶  offered
      ▲                                            │
      └────────────────────────────────────────────┘
                admin PATCH {enabled: false}
```

Invariant (FR-010): the transition to `withdrawn` is rejected when it would leave zero gateways
offered platform-wide.

**Not stored**: who changed it, and when (FR-019). No `changed_by`, no `changed_at`.

### Administrator (config, not a table)

| Source | Value |
|--------|-------|
| `ADMIN_EMAILS` env var | Comma-separated allowlist, compared case-insensitively |

No `users.is_admin` column. No cache table, no session claim — the allowlist is re-read per request
so a config change takes effect on restart without a migration.

## Derived values

Not stored, computed on read:

| Value | Derivation | Used by |
|-------|-----------|---------|
| `withdrawn_by_operator` | platform project row for that provider has `enabled = false` | FR-016 — the merchant's settings card |
| `offered` | platform project row has `enabled = true` | FR-006 — the providers page |
| `usable(project, provider)` | `offered(provider) AND adapter.enabled` for that project | FR-015 — the checkout gate |

`withdrawn_by_operator` is deliberately derived rather than stored. Storing it would mean writing to
every merchant's rows on withdrawal (option C in the clarify question, rejected) and would drift when
a gateway is re-offered.

## Relationships

```text
User (1) ──owns──▶ Project (many, user_id set)  ──has──▶ AdapterConfig (per-merchant)
                                                        (enabled = merchant's own choice, not read for availability)

User (0..1) ──▶ PlatformProject (user_id NULL)   ──has──▶ AdapterConfig (13 rows)
                                                        (enabled = PLATFORM-WIDE availability)
```

The platform project has no user. It is the only writer's target and the only reader of global state.

## Validation rules

| Rule | Requirement | Enforced where |
|------|-------------|----------------|
| At least one gateway stays offered | FR-010 | Admin write path, before commit |
| Only allowlisted emails may write | FR-001, FR-002 | Admin router guard, before the handler |
| No unauthenticated write | FR-003 | Same guard |
| `enabled` is not merchant-writable | FR-017 | `_PATCHABLE_ADAPTER` narrowed to `{"credentials"}` |
| Withdrawn gateway is non-functional | FR-011, FR-015 | The `usable()` gate, not the state itself |

## What is deliberately NOT modelled

- **Audit history** — rejected at Q2 (FR-019).
- **Per-merchant availability overrides** — rejected at Q5. One writer, one meaning.
- **Plan-tier gateway limits** — `max_active_adapters` retained but unenforced (FR-024). Unreachable
  once merchants cannot toggle.
- **Withdrawal state on merchant rows** — derived, not stored. See above.
