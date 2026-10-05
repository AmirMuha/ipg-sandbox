# API Contracts: Admin IPG Visibility Control

**Feature**: `006-admin-ipg-visibility` | **Date**: 2026-10-05

One endpoint added, one changed, one added read-only. Base path `/api/v1`.

---

## NEW — public availability read

### `GET /api/v1/providers`

Which gateways are currently offered platform-wide. **Unauthenticated** (D5).

**Response `200`:**

```json
{
  "providers": ["zarinpal"],
  "count": 1
}
```

`providers` is the list of offered gateway ids. `count` is `len(providers)` so the page can render a
badge without recomputing.

**Notes**

- Public marketing information — gateway ids only. No credentials, no project data, no merchant data.
- Not cached (FR-022). Read live on every request.
- When the platform project cannot be read, returns `{"providers": [], "count": 0}` rather than an
  error, so the page renders empty instead of presenting unverified gateways as offered (FR-023).

---

## NEW — administrator write

### `PATCH /api/v1/admin/providers/{provider}`

Set whether a gateway is offered platform-wide. **Administrators only** (FR-001).

**Path parameter**: `provider` — a gateway id, e.g. `zarinpal`.

**Request body:**

```json
{ "enabled": true }
```

**Response `200`:** the same shape as the public read.

**Errors**

| Status | Code | When |
|--------|------|------|
| `401` | `session_required` | No valid session (FR-003) |
| `403` | `forbidden` | Signed in, but email is not in `ADMIN_EMAILS` (FR-002) |
| `404` | `not_found` | Unknown `provider` id |
| `422` | `validation_error` | `enabled` missing or not a boolean |
| `422` | `adapter_limit_exceeded` | Would leave zero gateways offered (FR-010) |

The last is the interesting one: `PATCH {"enabled": false}` on the only offered gateway is refused
and the state is unchanged. The response must say why.

**Notes**

- Writes the **platform project's** `AdapterConfig.enabled` (D1/D3). Never the caller's own project.
- `credentials` is not accepted on this endpoint — admins control availability, not merchant
  credentials (FR-018).

---

## CHANGED — merchant adapter update

### `PATCH /api/v1/adapters/{adapter_id}`

**Breaking change.** The `enabled` field is no longer accepted.

**Request body — now:**

```json
{ "credentials": { "merchant_id": "..." } }
```

**Errors**

| Status | Code | When |
|--------|------|------|
| `422` | `validation_error` | Any field outside `{"credentials"}`, including `enabled` |

```json
{
  "code": "validation_error",
  "message": "unknown field(s): ['enabled']",
  "details": { "allowed": ["credentials"] }
}
```

**Rationale**: Clarification Q5 made administrators the only writer of availability (FR-017). Keeping
`enabled` writable would leave two writers and two meanings for the same flag.

**Also removed**: the `max_active_adapters` plan-limit check that previously rejected an enable beyond
the project's quota (`routes/__init__.py:300-323`). It is unreachable once merchants cannot toggle
(FR-024).

**Breaking-change checklist** — these exercise the old behaviour and must be updated, not left failing:

- `apps/engine/tests/unit/test_ipg_toggle.py` — `test_patch_adapter_unauthorized_in_demo_profile`
  and any test asserting an enable succeeds
- `apps/web/src/components/AdapterSettings.tsx` — `handleToggle` and its checkbox
- `apps/web/src/app/[locale]/(console)/settings/page.tsx` — the adapter list rendering
- `apps/web/src/lib/api.ts` — `patchAdapter` callers passing `enabled`

---

## UNCHANGED — consumed by this feature, no edit needed

| Endpoint | Why it still works |
|----------|-------------------|
| `GET /api/v1/adapters` | Still lists the caller's adapters. Now also reports the derived `withdrawn_by_operator` flag so the settings card can show the reason (FR-016) |
| `GET /api/v1/auth/me` | Returns the signed-in email the allowlist is checked against |
| `POST /api/v1/auth/login` / `register` / OAuth callback | Unchanged; admin is a privilege on an existing account, not a new sign-in |
| 13 gateway routers (`/zarinpal/...` etc.) | Unchanged. The availability gate is applied at lookup, not by altering these routes |

## Client contract (web)

`apps/web/src/lib/api.ts` gains:

| Function | Calls | Used by |
|----------|-------|---------|
| `getPlatformProviders()` | `GET /api/v1/providers` | providers page (server-side, no credentials) |
| `setPlatformProvider(provider, enabled)` | `PATCH /api/v1/admin/providers/{provider}` | `AdminProviderList` |

Both follow the existing `SERVER_API_BASE` / `CLIENT_API_BASE` split already in that file — the
providers page renders on the server, the admin toggle runs in the browser.
