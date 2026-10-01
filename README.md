# IPG Sandbox

A free, self-hostable payment-gateway sandbox for Iranian developers. It emulates
**Zarinpal**, **IDPay** and **Behpardakht (Mellat)** so you can run a full payment lifecycle —
approve, decline, timeout, refund, pending→settle, verify-fail — on your own machine, by
swapping only the gateway endpoint URL and your test credentials.

Simulation only: no real money, no card data, no production gateway reached, ever.

## Quickstart

```bash
git clone <repo> && cd <repo>
cp .env.example .env
docker compose up -d
```

Dashboard on <http://localhost:3000>; engine control API on <http://localhost:8080/api/v1>.

Local use requires **no account, signup or paid tier**. The gated hosted demo is a separate
compose profile (`--profile demo`).

## Drop-in swap

Point your app at the sandbox by changing **two things** and nothing else:

1. The gateway base URL — e.g. `https://api.zarinpal.example` → `http://localhost:8080/zarinpal`
2. The test merchant id in your config — the sandbox seeds `sandbox-merchant` per adapter

Force an outcome per-request with the `X-Sandbox-Scenario` header, so you can drive declines
and timeouts from a test without touching the code under test:

```bash
curl -s -X POST http://localhost:8080/zarinpal/request/payment \
  -H 'Content-Type: application/json' \
  -H 'X-Sandbox-Scenario: decline' \
  -d '{"amount":10000,"currency":"IRR","callback_url":"http://host.docker.internal:9999/callback"}'
```

Scenarios: `approve`, `decline`, `timeout`, `refund`, `pending_settle`, `verify_fail` — 6
outcomes × 3 adapters, 18 cells. See [specs/001-mvp/quickstart.md](specs/001-mvp/quickstart.md)
for the full §1–9 validation guide.

## Running without Docker

```bash
cd apps/engine
.venv/bin/uvicorn src.api.app:app --port 8080
.venv/bin/pytest -q          # 199 passed, 5 skipped
```

The suite runs on SQLite and needs no Postgres. Postgres-only concurrency tests skip
themselves unless `TEST_DATABASE_URL` is set.

## Project layout

| Path | What |
|---|---|
| `apps/engine` | FastAPI engine: adapters, scenarios, control API, webhooks, scheduler |
| `apps/dashboard` | Next.js bilingual (FA/EN, RTL) control dashboard |
| `apps/demo` | Gated demo layer (`--profile demo`), email-gated + per-visitor isolation |
| `specs/001-mvp` | Spec, plan, tasks, contracts, quickstart validation guide |

## Status

Functional MVP. Data model, migrations, control API, all three gateway adapters, the 18-cell
scenario matrix, webhook delivery with retries, the scenario scheduler, the bilingual
dashboard, and the CI runner are all in place and covered by the test suite.

## Behpardakht (Mellat) fidelity — known gap

Read this before pointing a real Mellat SDK at the sandbox.

The Behpardakht adapter targets the **documented subset** of operations needed for the flows
above. Byte-perfect emulation is explicitly out of scope, and there are two known divergences
from production Mellat PGW:

1. **Operation names.** The sandbox serves `bpPaymentRequest` / `bpPaymentVerification` /
   `bpReverseTransaction`. Real PGW uses `bpPayRequest` / `bpVerifyRequest` /
   `bpReversalRequest`.
2. **Response shape.** The sandbox returns structured response elements. Real PGW returns a
   single comma-joined `return` string (e.g. `"0,<refId>"` for pay), which real SDKs parse
   with `.split(',')`.

So a production Mellat client library will **not** drop in unchanged against the current
WSDL. Zarinpal and IDPay are unaffected. This gap is open work, tracked against T023/T066.

The WSDL spike that established this passed using the Python `zeep` client as the reference
implementation. The stricter exit criterion in `specs/001-mvp/research.md` R4 — a reference
*Iranian* Mellat client library completing initiate→verify — was **not** met: no such SDK is
installable in this environment, and initiate→verify additionally requires the adapter server
that T023 has not yet built. See the "R4 outcome" note in that file.

## License

AGPL-3.0. See [LICENSE](./LICENSE), declared as `AGPL-3.0-only` in both package manifests
(`apps/engine/pyproject.toml`, `apps/dashboard/package.json`).

Source files do **not** carry per-file SPDX headers. The license is declared once, in the three
canonical places above, rather than repeated across ~96 files — which would be pure diff noise
and would have to be kept in sync. T078 records this as a deliberate decision.
