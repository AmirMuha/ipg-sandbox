# Contract: Emulated Adapter Surfaces (Phase 1)

**Feature**: specs/001-mvp | **Date**: 2026-09-23
**Purpose**: Wire-level contracts the engine exposes to the app under test (drop-in parity). Full request/response field tables are pinned by contract tests (research R2/R7); this document fixes paths, stages, and fidelity rules.

**Global rules**

- All surfaces are served by `engine` on a configurable base URL (local default `http://localhost:8080`).
- Only **in-scope operations** (initiate/request, checkout redirect, verify/settle, refund/reverse, callback notify) are implemented. Anything else → adapter-specific explicit error (`HTTP 400` JSON `{code:"unsupported_operation"}` or SOAP fault `sandbox:UnsupportedOperation`). Never silent state mutation (spec edge case).
- Amounts arrive in the emulated API's declared `api_unit` (Zarinpal/IDPay/Behpardakht real conventions) and are stored canonically as Rial (clarification 4).
- Scenario applied = per-transaction force ?? project default ?? `approve` (edge-case precedence).
- Forced delays: `timeout` → bounded delay then timeout/exception response; `pending_settle` → status `pending`, `due_at = checkout + project.pending_settle_delay_s` (default 5s), then `settled`.

## 1. Zarinpal (REST-style)

| Stage | Method + path (configurable prefix `/zarinpal`) | Behavior |
|-------|--------------------------------------------------|----------|
| Initiate | `POST {prefix}/request/payment` | Validates test credentials → returns emulated `authority` + redirect URL to sandbox checkout |
| Checkout | `GET {prefix}/checkout/{authority}` | Hosted sandbox checkout page (confirm/cancel per scenario) |
| Return | `GET {prefix}/callback/{authority}?Authority=…` | Redirects to app `CallbackURL` with result query params |
| Verify | `POST {prefix}/payment/verification` | Outcome per `effective_scenario` (`approve`→success codes; `decline`/`verify_fail`→failure codes) |
| Refund | `POST {prefix}/payment/refund` | Only meaningful after settle → status `refunded` |

## 2. IDPay (REST-style)

| Stage | Method + path (prefix `/idpay`) | Behavior |
|-------|----------------------------------|----------|
| Initiate | `POST {prefix}/payment` | Returns emulated `id` + sandbox start URL |
| Checkout | `GET {prefix}/payment/start/{id}` | Hosted sandbox checkout page |
| Return/Verify | `POST {prefix}/payment/verify` | Scenario-driven result (`verify_fail` passes checkout, fails here) |
| Refund | `POST {prefix}/payment/refund` | Post-settle refund |
| Callback | POST to app `callback_url` | Payload in **IDPay's real callback field names** |

## 3. Behpardakht / Mellat (SOAP/WSDL drop-in)

Spike first (research R4 — exit criteria: reference Mellat-style client completes initiate→verify).

| Stage | SOAP operation (in-scope subset) | Behavior |
|-------|----------------------------------|----------|
| Payment request | `bpPaymentRequest` | Returns emulated RefId + RedirectUrl → sandbox checkout |
| Checkout | `GET {prefix}/checkout/{refId}` | Hosted sandbox checkout page |
| Verify | `bpPaymentVerification` | Scenario-driven success/fault codes |
| Reverse/refund | `bpReverseTransaction` | Post-settle reverse |
| Inquiries etc. | — | SOAP fault `sandbox:UnsupportedOperation` |

- Endpoint: `POST {prefix}/MellatPaymentGateway` (WSDL at `{prefix}/MellatPaymentGateway?wsdl`).
- Envelope contents built from templates; contract test parses responses with a real client lib (Zeep) to prove SDK compatibility.
- Fidelity: documented subset only — byte-perfect emulation explicitly out of scope (spec edge case).

## 4. Callback / webhook payload fidelity (all adapters)

- Payload shape per (adapter × stage) mirrors the **real gateway's callback format** for in-scope stages (clarification 2).
- Delivery: POST to app `callback_url` / configured webhook target (incl. `host.docker.internal` — research R6).
- Every attempt persisted as WebhookDelivery (pending → delivered/failed) with project retry/backoff policy; 100% of terminal failures visible (SC-005, no-silent-loss edge case).
- Snapshot contract tests pin one golden payload per (adapter × stage); drift fails CI.

## 5. Checkout page contract

- Server-rendered page at each adapter's checkout path; language follows dashboard locale (FA default RTL / EN LTR).
- Interactive controls: **confirm**, **fail/decline**, **abandon** (navigating away leaves `pending` → `expired` per edge case). Page never collects real card data (FR-012) — amount + fake method only.

> Companion contract: [control-api.md](./control-api.md) (dashboard/CI interface — not seen by the app under test).
