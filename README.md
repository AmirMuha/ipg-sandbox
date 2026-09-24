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

## Status

Early. The engine foundation is in place — data model, migrations, control API, scenario
resolution and history cap, with the three gateway adapters next. `engine/` and `postgres`
run today; the dashboard is a placeholder shell.

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

AGPL-3.0. See [LICENSE](./LICENSE).
