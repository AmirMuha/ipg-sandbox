# Research: Comprehensive Iranian IPG Gateway Adapters Suite (Phase 0)

**Feature**: specs/003-implement-ipg-adapters | **Date**: 2026-10-03
**Input**: Technical Context in plan.md, spec.md, and official documentation files in `./docs/`

All Technical Context requirements and clarification decisions are established. Research below addresses the core architectural strategies, wire protocols, signature models, and metadata patterns needed to implement all 13 documented gateways.

## R1. Gateway Taxonomy & Protocol Distribution

An analysis of the 13 gateway specifications in `./docs/` reveals three distinct communication paradigms used across the Iranian payment ecosystem:

1. **Modern REST / JSON Payment Facilitators (پرداخت‌یار)**:
   - **Gateways**: `zarinpal`, `idpay`, `sizpay`
   - **Initiation**: HTTP POST JSON with merchant credentials, amount, description, and callback URL.
   - **Checkout Handoff**: HTTP redirect (`GET`) to hosted gateway URL with payment token/authority.
   - **Customer Return**: HTTP GET redirect to merchant callback with query parameters (e.g. `Authority`, `Status`, `TrackId`).
   - **Verification**: HTTP POST JSON to verification endpoint returning JSON status envelopes.

2. **Hybrid Token REST + SOAP / REST Verification Banking PSPs (شاپرک)**:
   - **Gateways**: `saman-sep`, `sadad-melli`, `pasargad-pep`, `asan-pardakht`, `irankish`
   - **Initiation**: REST POST JSON (or SOAP XML) to acquire a single-use payment `Token`.
   - **Checkout Handoff**: HTTP POST form submission to Shaparak payment portal carrying the `Token`.
   - **Customer Return**: Shaparak standard HTTP POST form to merchant `callback_url` carrying transaction details (`RefNum`, `ResNum`, `TraceNo`, `Rrn`, `SecurePan`, `Status`).
   - **Verification**: REST POST JSON or SOAP XML verification request confirming the token/order.

3. **SOAP 1.1 / 1.2 WSDL Banking PSPs**:
   - **Gateways**: `behpardakht`, `parsian-pec`, `pardakht-novin`, `fanava`, `sarmayeh`
   - **Initiation**: SOAP XML envelope requesting `bpPaymentRequest`, `SalePaymentRequest`, etc.
   - **Checkout Handoff**: Form POST carrying `RefId` or `Token` to the gateway action URL.
   - **Customer Return**: Form POST to callback URL with bank status codes (`ResCode`, `SaleOrderId`, `SaleReferenceId`).
   - **Verification / Settlement**: SOAP XML envelope for verification, settlement, or reversal.

- **Decision**: The engine will support both protocol styles natively within FastAPI. REST gateways will expose dedicated Pydantic/JSON route handlers. SOAP gateways will use FastAPI raw request handlers that parse XML envelopes via `defusedxml` / `xml.etree` and render response envelopes from lightweight templates, mirroring the proven Behpardakht pattern.
- **Rationale**: Real Iranian payment SDKs in PHP, Python, Node.js, and Java send strict SOAP envelopes or JSON payloads. Emulating the exact wire protocol guarantees true drop-in compatibility.
- **Alternatives considered**: Generic JSON-only mock requiring clients to rewrite their payment library to JSON (rejected: violates drop-in promise).

## R2. WSDL & Schema Exposure for SOAP Clients

- **Decision**: For every gateway that uses SOAP XML, the engine will serve a clean, static `.wsdl` file matching the operations in scope when client libraries request `{endpoint}?wsdl` or `{endpoint}/wsdl`.
- **Rationale**: Many SOAP clients (such as PHP's `SoapClient` or Python's `zeep`) automatically initiate a `GET ?wsdl` request upon instantiation to validate XML types, endpoints, and method names before sending requests. Providing valid WSDLs ensures these clients initialize without error.
- **Alternatives considered**: Dynamic WSDL generation at runtime (overly complex, fragile) or omitting WSDL (causes `SoapClient` constructor exceptions in client apps).

## R3. Merchant Callback Redirection Mechanics

- **Decision**: The sandbox checkout screen will support two return redirection modes:
  1. **Shaparak POST Form Auto-Submit**: For banking PSPs (Behpardakht, Saman, Sadad, Parsian, Pasargad, Asan Pardakht, IranKish, PNA, Fanava, Sarmayeh), when payment is confirmed or cancelled, the checkout browser page renders an HTML page containing an auto-submitting `<form method="POST" action="{merchant_callback_url}">` populated with hidden fields matching the bank's exact parameter names.
  2. **Direct HTTP 302 / 303 Redirect**: For payment facilitators (ZarinPal, IDPay, SizPay), the checkout action returns an HTTP redirect response sending the user to the merchant callback URL with expected query parameters.
- **Rationale**: Real bank payment gateways return customers to merchants via browser POST redirects containing form data. Emulating this exact behavior allows merchant applications to test their CSRF exemptions and POST callback parsers accurately.
- **Alternatives considered**: Always using GET redirects (breaks merchants that expect POST bodies from Shaparak PSPs).

## R4. Deterministic Cardholder & Reference Metadata Generation

- **Decision**: Implement a unified `metadata.py` utility in `apps/engine/src/adapters/` that produces realistic Shaparak cardholder data:
  - **Masked Card PAN**: Uses the bank's official 6-digit BIN prefix, 6 masking asterisks, and 4 deterministic digits derived from the transaction ID (e.g. Melli: `603799******{tx.id % 10000:04d}`).
  - **Retrieval Reference Number (RRN)**: A 12-digit numeric string formatted as `{YYYYMMDD}{tx.id % 10000:04d}`.
  - **System Trace Number**: A 6-digit numeric string `{tx.id % 1000000:06d}`.
- **Rationale**: Real reconciliation software parses and logs masked card PANs and RRNs; deterministic generation makes test assertions repeatable across automated test suites.
- **Alternatives considered**: Random generation (makes test assertions flaky) or constant strings (unrealistic for multi-transaction tests).

## R5. Permissive Cryptographic Signature Handling

- **Decision**: Implement a modular `crypto.py` helper supporting RSA (PKCS#1 v1.5 with SHA1/SHA256) and HMAC verification:
  - If the adapter configuration does not contain public/private signing keys (the default in sandbox development), inbound signatures are treated as valid (permissive mode).
  - If a signing key or certificate is provided in `AdapterConfig.credentials["private_key"]` or `["sign_key"]`, the helper verifies the mathematical signature against the canonical data string.
  - When generating callbacks or responses that require gateway signatures, the helper signs the data if a private key exists, or generates a realistic mock base64 signature if no key is configured.
- **Rationale**: Eliminates the developer onboarding hurdle of generating and configuring RSA certificates just to run local sandbox tests, while still accommodating teams that need to test cryptographic signing logic.
- **Alternatives considered**: Strict-only signing (causes immense friction for quick testing) or no signature fields (breaks clients that parse signature fields).

## R6. Universal Scenario to Gateway Status Code Mapping

- **Decision**: Define a declarative mapping table translating the 6 engine scenarios (`approve`, `decline`, `timeout`, `refund`, `pending_settle`, `verify_fail`) into each gateway's official response format:

| Gateway | Success Code | Decline Code | Timeout Code | Verify Fail Code | Already Verified |
|---|---|---|---|---|---|
| **Behpardakht Mellat** | `0` (or `0,RefId`) | `41` (Invalid PIN) / `42` | `48` / Delayed | `43` (Verify timeout) | `45` |
| **ZarinPal** | `100` | `-11` | `-10` | `-12` | `101` |
| **IDPay** | `100` | `8` | `7` | `10` | `101` |
| **Saman SEP** | `0` | `-1` | `-3` | `-2` | `-6` |
| **Sadad Melli** | `0` | `-1` | `101` | `103` | `102` |
| **Parsian PEC** | `0` | `-1` | `-130` | `-138` | `100` |
| **Pasargad PEP** | `ResultCode: 0` | `ResultCode: 1` | `ResultCode: 2` | `ResultCode: 3` | `ResultCode: 0` |
| **Asan Pardakht** | `0` | `100` | `101` | `102` | `103` |
| **Pardakht Novin (PNA)**| `0` | `-1` | `-2` | `-3` | `0` |
| **IranKish** | `"00"` | `"51"` (No funds) | `"91"` | `"05"` | `"00"` |
| **SizPay** | `0` | `-1` | `-2` | `-3` | `0` |
| **Fanava Card** | `0` | `-1` | `-2` | `-3` | `0` |
| **Bank Sarmayeh** | `0` | `-1` | `-2` | `-3` | `0` |

- **Rationale**: Pinned mapping guarantees that automated test suites asserting on specific bank error codes receive the exact codes documented in official bank manuals.
