# Data Model: Payment Gateway Sandbox MVP (Phase 1)

**Feature**: specs/001-mvp | **Date**: 2026-09-23
**Source**: spec.md Key Entities + Clarifications; storage = PostgreSQL (plan.md)

## Entities

### Project

Container for all simulation data; local self-host runs exactly one; hosted demo creates one per visitor session.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| name | text | "default" for local |
| kind | enum: `local` \| `demo` | demo projects are visitor-scoped |
| default_scenario | enum → ScenarioOutcome | project default (FR-005) |
| history_cap | int | default 1000, operator-configurable (FR-006) |
| webhook_retry_max | int | default small bounded value (spec assumption) |
| webhook_retry_backoff_s | int[] | backoff schedule |
| pending_settle_delay_s | int | default 5 (clarification 5) |
| timeout_delay_s | int | bounded seconds (spec assumption) |
| created_at | timestamptz | |

**Validation**: `history_cap ≥ 1`; delays ≥ 0 and < 300 (bounded so CI can't hang — spec edge case).

### VisitorSession (demo only)

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| project_id | FK → Project | 1:1 — isolation boundary (FR-014) |
| email | citext | verified address only, no password (spec assumption) |
| magic_link_token_hash | text null | single-use, expiring |
| verified_at | timestamptz null | simulation blocked until set |
| created_at | timestamptz | |

**Validation**: email format valid; token single-use. Local projects have **no** VisitorSession (FR-014: no login locally).

### AdapterConfig

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| project_id | FK → Project | |
| provider | enum: `zarinpal` \| `idpay` \| `behpardakht` | three v1 adapters (FR-002) |
| enabled | bool | |
| credentials | jsonb | test merchant-id/key/endpoint overrides; **test values only** (FR-012) |
| api_unit | enum: `rial` \| `toman` | unit this emulated API expects; engine stores Rial canonical and converts at boundary (clarification 4) |
| endpoint_path_prefix | text | derived from provider's drop-in surface (contract: adapter-surfaces.md) |

**Validation**: one enabled row per (project, provider); credentials never validated against real gateways (simulation only).

### Transaction

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| project_id | FK → Project | scoping key for isolation + cap |
| adapter_id | FK → AdapterConfig | exactly one adapter per transaction |
| amount_rial | bigint | **canonical unit: Iranian Rial** (clarification 4) |
| currency | text | default `IRR` |
| status | enum → see State machine | |
| forced_scenario | enum → ScenarioOutcome null | per-transaction force (wins over default — edge case) |
| effective_scenario | enum → ScenarioOutcome | resolved at initiate: forced ?? project default ?? approve |
| authority / payment_id | text | emulated gateway reference (per-adapter field names in payloads) |
| app_reference | text | caller-supplied order/authority id from the app under test |
| description | text null | passthrough |
| callback_url | text null | notify target for async callbacks |
| return_url | text null | checkout redirect target |
| due_at | timestamptz null | drives timeout delay & pending→settle (default +5s, clarification 5) |
| raw_request / raw_response | jsonb | debugging detail for dashboard (US4.4) |
| created_at / updated_at | timestamptz | |

**ScenarioOutcome** (shared enum): `approve` | `decline` | `timeout` | `refund` | `pending_settle` | `verify_fail`.

**State machine** (status):

```text
initiated ──► pending ──► settled          (approve, or pending_settle after due_at)
   │            │
   │            ├──► approved ──► refunded (refund scenario)
   │            └──► expired               (abandoned checkout / timeout window)
   ├──► declined                           (decline / verify_fail at verify)
   ├──► failed                             (timeout/exception outcome)
   └──► failed                             (unsupported op / invalid credentials → explicit error)
```

- `pending → settled` transition fires when `now ≥ due_at` (scheduler, research R5).
- Abandoned checkout stays `pending` until expiry → `expired` (spec edge case — distinguishable from settled).
- Cap enforcement: after insert, `DELETE` oldest rows for `project_id` beyond `history_cap`, same transaction as UsageMeter bump (FR-006 consistency edge case).

**Validation**: `amount_rial ≥ 0`; transitions only along the diagram (illegal transition raises, never silently mutates).

### WebhookDelivery

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| transaction_id | FK → Transaction | 0..n per transaction |
| target_url | text | incl. localhost / host.docker.internal (research R6) |
| stage | enum: `notify` \| `settle` \| `refund` … | callback trigger point |
| payload | jsonb | **real gateway callback format** per adapter (clarification 2) |
| attempt | int | 1-based |
| result | enum: `delivered` \| `failed` \| `pending` | |
| response_status | int null | |
| error | text null | |
| created_at | timestamptz | |

**Rule**: every attempt is INSERTed (pending) then UPDATEd with result — no silent loss (spec edge case / SC-005). Retry per `Project.webhook_retry_*` until success or exhausted.

### UsageMeter

| Field | Type | Notes |
|-------|------|-------|
| project_id | FK → Project PK | one row per project |
| requests_total | bigint | incremented on emulated-API + control-API calls |
| transactions_total | bigint | lifetime count (keeps counting even as rows are capped) |
| history_retained | int | min(transactions_total, history_cap) — FR-011 |
| webhook_attempts | bigint | |
| updated_at | timestamptz | |

**Rule**: counters only — **no billing fields, no invoices** (FR-011 / spec assumption).

## Relationships (summary)

```text
Project 1─* AdapterConfig
Project 1─* Transaction 1─* WebhookDelivery
Project 1─1 UsageMeter
Project 1─1 VisitorSession (demo only)
```

## Uniqueness & indexing

- Unique: `(project_id, provider)` where `enabled` (partial unique); `(project_id, authority)`; `(project_id, app_reference)` when supplied.
- Index: `(project_id, created_at DESC)` for list + cap deletion; `(status, due_at)` for the scheduler sweep; `(transaction_id)` on WebhookDelivery; `(project_id, email)` on VisitorSession.
