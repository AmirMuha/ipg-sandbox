# Quickstart: Validation Guide (Phase 1)

**Feature**: specs/001-mvp | **Date**: 2026-09-23
**Purpose**: Runnable end-to-end checks proving the spec's success criteria. No implementation bodies — commands + expected outcomes only. Contracts: [adapter-surfaces.md](./contracts/adapter-surfaces.md), [control-api.md](./contracts/control-api.md). Data: [data-model.md](./data-model.md).

## Prerequisites

- Docker + Docker Compose available; no accounts, keys, or payments anywhere on the local path (FR-001/SC-002).
- Free ports for engine (8080), dashboard (3000), Postgres (5432) — overridable via `.env`.

## 1. One-command bootstrap (SC-001, FR-015)

```bash
git clone <repo> && cd <repo>
cp .env.example .env
docker compose up -d
```

**Expected**: all containers healthy; dashboard at `http://localhost:3000` (FA default, RTL); engine surfaces at `http://localhost:8080`.
**SC-001 check**: from this command to step 2's approved result must take a fresh user **< 10 minutes** (time it at demo).

## 2. First approved payment, drop-in (US1, SC-002)

```bash
# Initiate (Zarinpal surface — swap only URL + test merchant id in a real app)
curl -s -X POST http://localhost:8080/zarinpal/request/payment \
  -H 'Content-Type: application/json' \
  -H 'X-Sandbox-Scenario: approve' \
  -d '{"amount":10000,"currency":"IRR","callback_url":"http://host.docker.internal:9999/callback","return_url":"http://localhost:3000"}'
# → returns authority + checkout URL

# Open checkout URL in a browser, press confirm → redirected to callback with success params
# Verify:
curl -s -X POST http://localhost:8080/zarinpal/payment/verification \
  -H 'Content-Type: application/json' -d '{"authority":"<from step 1>"}'
```

**Expected**: verification success payload; transaction `settled` in `GET /api/v1/transactions`. Zero signup/paywall encountered.

## 3. Scenario matrix — SC-003 (18/18)

```bash
pytest engine/tests/integration/test_scenario_matrix.py -q   # or the compose-run equivalent
```

**Expected**: exit 0 — 6 outcomes (`approve, decline, timeout, refund, pending_settle, verify_fail`) × 3 adapters (`zarinpal, idpay, behpardakht`), each asserting the contract-defined response for that (adapter × outcome) (contract: adapter-surfaces.md §1–3).

## 4. Forced pending→settle timing (clarification 5, US2.3)

```bash
curl -s -X POST http://localhost:8080/api/v1/transactions ... forced_scenario=pending_settle ...
# poll status until settled
```

**Expected**: `pending` immediately after checkout; `settled` ≈ **5 s** later (within configured delay tolerance; project override via `PATCH /api/v1/project`).

## 5. Webhook delivery to the host (US3, SC-005)

```bash
# terminal 1: local receiver
python3 -m http.server 9999   # or any endpoint that logs POSTs
# terminal 2: run a payment whose callback_url=http://host.docker.internal:9999/callback
curl -s "http://localhost:8080/api/v1/deliveries?result=delivered"
```

**Expected**: delivery row with real gateway-format payload (snapshot-pinned); ≥95% arrive **< 5 s**; kill the receiver mid-flow → attempts recorded `failed` + retries per project policy, visible via `GET /api/v1/deliveries` (**no silent loss**).

## 6. Headless CI run (US5.1, SC-004, FR-010)

```bash
./scripts/ci-scenario-run.sh --adapter zarinpal   # drives steps 2–5 non-interactively
echo $?
```

**Expected**: machine-readable PASS/FAIL per step, **exit code 0**, whole sequence **< 5 minutes** for one adapter. Nothing in this path touches the dashboard.

## 7. Dashboard checks (US4, SC-006)

Manual/Playwright smoke against `http://localhost:3000`:

1. Transactions list shows step 2–5 rows: adapter, amount (Rial), status, scenario, timestamps.
2. Force `decline` from the dashboard → next initiated payment declines (scenario PATCH contract).
3. Open a delivery in Webhooks view → target/payload/attempt/result visible.
4. Switch EN → FA: all strings translated, layout flips RTL; switch back → LTR. Primary flows work identically both languages.

## 8. Demo layer (US5.2, FR-013/FR-014) — staging check before launch

```bash
docker compose --profile demo up -d
# visit dashboard → signup form: enter email → magic link (dev: logged by demo container)
```

**Expected**: simulation blocked until verify; after session: normal flows; second browser/session sees **only its own** transactions (isolation); hammering `/demo/signup` or simulate endpoints returns `rate_limited` (edge case).

## 9. History cap (FR-006)

```bash
# script: insert >1000 transactions for one project, then:
curl -s "http://localhost:8080/api/v1/meters"
```

**Expected**: `history_retained == history_cap (1000)`, `transactions_total` keeps counting; oldest rows gone, newest intact (cap edge case).

## Pass criteria for the feature

| Check | Spec anchor |
|-------|-------------|
| 1–2 run with zero cost/account | SC-002, FR-001 |
| Steps 2–5 each independently runnable | US1–US3 independent tests |
| 18/18 matrix green | SC-003 |
| CI sequence < 5 min, exit-code contract | SC-004 |
| Webhook latency + failure visibility | SC-005 |
| FA/EN parity + RTL | SC-006, FR-009 |
| Demo gate + isolation | FR-013, FR-014, clarification 1 |
