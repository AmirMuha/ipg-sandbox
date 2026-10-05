# Quickstart: Validating Admin IPG Visibility Control

**Feature**: `006-admin-ipg-visibility` | **Date**: 2026-10-05

End-to-end validation guide. Assumes the implementation is done. Contracts and data model are in
[contracts/api.md](./contracts/api.md) and [data-model.md](./data-model.md) — this file does not
repeat them.

## Prerequisites

- `pnpm` (workspace root) and the engine's Python environment
- The engine reachable on `http://localhost:8080`, the web app on `http://localhost:3000`
  (`pnpm dev` at the repo root starts both; engine alone is `poe dev` in `apps/engine`)
- An admin email in `ADMIN_EMAILS` (e.g. `ops@example.com`)
- `curl` and `jq` for the API checks

## 1. Automated tests

```bash
cd apps/engine && poe test
```

Expected: the full suite green, including the new admin-gate tests. Specifically, these must pass —
they encode the feature's security properties:

| Test | Asserts |
|------|---------|
| admin can withdraw a gateway | 200, state persisted |
| non-admin signed in is refused | 403, state unchanged |
| anonymous is refused | 401, state unchanged |
| last offered gateway cannot be withdrawn | 422, state unchanged (FR-010) |
| merchant `PATCH {"enabled": true}` | 422, `details.allowed == ["credentials"]` (FR-017) |
| providers read is public | 200 with no session (FR-006) |
| platform project lookup | exactly one row with `user_id IS NULL` (D1) |

```bash
cd apps/web && pnpm test          # smoke
cd apps/web && pnpm test:playwright
```

## 2. Seed a known state

With only Zarinpal offered, the other twelve withdrawn — the state this feature is meant to produce.

```bash
curl -s localhost:8080/api/v1/providers | jq
```

```json
{ "providers": ["zarinpal"], "count": 1 }
```

If the list is longer, withdraw the extras as the admin (step 3) or re-run the seed migration
`0009_default_zarinpal_enabled`.

## 3. Admin can change availability

```bash
# sign in as the admin, keep the session cookie
curl -s -c /tmp/admin.jar -X POST localhost:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ops@example.com","password":"..."}' | jq '.user.email'

# offer a second gateway
curl -s -b /tmp/admin.jar -X PATCH localhost:8080/api/v1/admin/providers/idpay \
  -H 'Content-Type: application/json' -d '{"enabled":true}' | jq

# withdraw it again
curl -s -b /tmp/admin.jar -X PATCH localhost:8080/api/v1/admin/providers/idpay \
  -H 'Content-Type: application/json' -d '{"enabled":false}' | jq
```

Expected: `providers` reflects the change immediately, in both directions (FR-009).

## 4. Non-admins cannot

```bash
# a merchant, not in ADMIN_EMAILS
curl -s -c /tmp/merchant.jar -X POST localhost:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"merchant@example.com","password":"..."}' > /dev/null

curl -s -o /dev/null -w '%{http_code}\n' -b /tmp/merchant.jar \
  -X PATCH localhost:8080/api/v1/admin/providers/zarinpal \
  -H 'Content-Type: application/json' -d '{"enabled":false}'
```

Expected: `403`, and the state is unchanged (FR-002).

```bash
# anonymous
curl -s -o /dev/null -w '%{http_code}\n' \
  -X PATCH localhost:8080/api/v1/admin/providers/zarinpal \
  -H 'Content-Type: application/json' -d '{"enabled":false}'
```

Expected: `401` (FR-003).

## 5. The merchant toggle is gone

```bash
curl -s -b /tmp/merchant.jar -X PATCH localhost:8080/api/v1/adapters/<adapter_id> \
  -H 'Content-Type: application/json' -d '{"enabled":true}' | jq
```

Expected: `422` with `details.allowed: ["credentials"]` (FR-017).

```bash
# credentials still work
curl -s -b /tmp/merchant.jar -X PATCH localhost:8080/api/v1/adapters/<adapter_id> \
  -H 'Content-Type: application/json' -d '{"credentials":{"merchant_id":"abc"}}' | jq '.provider'
```

Expected: `200`. Availability and credentials are separate concerns (FR-018).

## 6. Last gateway cannot be withdrawn

```bash
curl -s -b /tmp/admin.jar -X PATCH localhost:8080/api/v1/admin/providers/zarinpal \
  -H 'Content-Type: application/json' -d '{"enabled":false}' | jq
```

Expected: `422`, an explanation that at least one gateway must stay offered, and Zarinpal still
offered afterwards (FR-010).

## 7. The providers page follows the state

```bash
curl -s localhost:3000/fa/providers | grep -c 'data-gateway-id'
curl -s localhost:3000/en/providers | grep -c 'data-gateway-id'
```

Expected: both counts equal `count` from `GET /api/v1/providers` — the same set in both languages
(FR-008), each appearing once.

Then, **with the page open**, withdraw a gateway in another terminal (step 3) and reload the page.

Expected: the withdrawn gateway is gone on the next load, with no restart and no cache clear
(SC-002, FR-022).

The page header count must equal the number of cards shown. If it still reads `۱۳`, the badge is
still a literal — see research.md "how the providers page filters".

## 8. A merchant sees why a gateway stopped working

Sign in as a merchant whose project has a gateway enabled, withdraw that gateway as the admin, then
load `/{locale}/settings`.

Expected: the card is still listed, marked as withdrawn by the operator, with the reason in the
merchant's language, and **no switch to change it** (FR-016, FR-017).

Re-offer the gateway as the admin and reload.

Expected: usable again, with no action from the merchant (FR-018).

## 9. A withdrawn gateway is non-functional

Initiate a payment through a gateway, then withdraw it mid-flow.

Expected: the in-flight payment completes normally (FR-011, SC-005). A *new* payment through the
withdrawn gateway is refused.

## 10. Empty and unreadable states

Withdraw every gateway by direct DB update, bypassing the API:

```sql
UPDATE adapter_configs SET enabled = false
WHERE project_id = (SELECT id FROM projects WHERE user_id IS NULL);
```

Reload `/fa/providers`.

Expected: the page renders, showing no gateways — not an error, and not the full list (FR-023).

Restore with:

```sql
UPDATE adapter_configs SET enabled = (provider = 'zarinpal')
WHERE project_id = (SELECT id FROM projects WHERE user_id IS NULL);
```

## Manual acceptance summary

| Requirement | Check | Section |
|-------------|-------|---------|
| FR-001 admin-only writes | 3 | ✅ |
| FR-002/003 refusals | 4 | ✅ |
| FR-006/022 page follows state | 7 | ✅ |
| FR-008 both languages | 7 | ✅ |
| FR-010 last-gateway guard | 6 | ✅ |
| FR-011 in-flight completes | 9 | ✅ |
| FR-016 withdrawn shown to merchant | 8 | ✅ |
| FR-017 merchant toggle removed | 5 | ✅ |
| FR-023 unreadable state | 10 | ✅ |
| SC-002 no restart needed | 7 | ✅ |
