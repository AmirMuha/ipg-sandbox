# Feature Specification: Comprehensive Iranian IPG Gateway Adapters Suite

**Feature Branch**: `003-implement-ipg-adapters`

**Created**: 2026-10-03

**Status**: Draft

**Input**: User description: "implementing all the adapters inside ./docs/"

## Clarifications

### Session 2026-10-03

- Q: Which payment gateway adapters are included in the scope of this feature? → A: All 13 payment gateways documented in `./docs/`, including the 3 initial gateways (`behpardakht`, `zarinpal`, `idpay`) and the 10 remaining banking and payment facilitator gateways (`saman-sep`, `sadad-melli`, `parsian-pec`, `pasargad-pep`, `asan-pardakht`, `pardakht-novin`, `irankish`, `sizpay`, `fanava`, `sarmayeh`).
- Q: What communication protocols must be supported for each gateway? → A: Each gateway must emulate the exact wire protocol defined in its official documentation in `./docs/`, supporting REST (JSON) or SOAP (XML/WSDL) endpoints as expected by real-world merchant payment libraries and banking SDKs.
- Q: How should merchant application callbacks and redirects be delivered? → A: Callbacks must adhere strictly to each gateway's official specification: HTTP POST form submissions containing gateway-native parameter names for Shaparak PSP gateways, and HTTP GET query parameters for modern payment facilitators.
- Q: How should the sandbox implement communication protocols for gateways whose official documentation specifies SOAP/XML web services (such as Saman SEP, Sadad Melli, Parsian PEC, and Asan Pardakht)? → A: Native SOAP 1.1/1.2 XML endpoints with authentic operation names and XML envelope parsing matching bank WSDLs, with REST endpoints where specified, ensuring drop-in compatibility for standard banking SDKs.
- Q: How should cryptographic payload signing be handled for gateways that specify RSA or HMAC signatures (such as Pasargad PEP and Sadad)? → A: Permissive signature mode by default (accepts dummy/mock signatures), with optional strict RSA/HMAC verification when keys are configured in the adapter.
- Q: How should the sandbox generate cardholder metadata (such as masked card PAN, RRN, and system trace numbers) in gateway callback and verification responses? → A: Realistic mock generation: authentic 16-digit masked card PANs (e.g. `603799******1234`) using recognized Iranian bank prefixes, plus 12-digit RRNs and 6-digit trace numbers.
- Q: How are transaction currencies and amounts handled across diverse gateways? → A: The sandbox maintains all internal transaction records canonical in Rials (IRR) while automatically translating amounts to and from Tomans at the gateway API boundary whenever a specific gateway protocol expects Tomans (e.g. ZarinPal optional Toman mode).
- Q: Which operational lifecycle methods must be available for each adapter? → A: Every adapter must support the complete payment lifecycle: payment initiation, gateway checkout page rendering, callback delivery, payment verification, status inquiry/settlement, and reversal/refund (where specified by the gateway's documentation).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Top-Tier Banking PSP Gateway Simulation (Priority: P1)

A merchant developer integrating with major Iranian banking payment service providers (Saman SEP, Sadad Bank Melli, Parsian PEC, Pasargad PEP, and Asan Pardakht) points their application's payment configuration to the local sandbox URL. Without modifying their core business code, their application initiates a payment, receives an authentic gateway token or reference ID, redirects the customer through the gateway's checkout screen, receives a valid callback POST form, and successfully verifies and settles the payment.

**Why this priority**: These five banking PSPs process the majority of e-commerce transactions in Iran. Supporting them gives developers drop-in testing capability for the most critical payment flows without requiring bank approvals, test merchant credentials, or static IP whitelisting.

**Independent Test**: Can be tested independently by running an automated payment flow against each of the five top-tier PSP endpoints, verifying that initiation produces a valid gateway-specific token, the checkout page renders with matching gateway styling, and the verification endpoint returns an authentic bank approval response.

**Acceptance Scenarios**:

1. **Given** a merchant application configured for Saman (SEP), **When** a payment request is initiated, **Then** the system returns an authentic token string and accepts a checkout redirection using that token.
2. **Given** an initiated payment on Sadad (Bank Melli), **When** the customer completes payment on the simulated checkout screen, **Then** the system delivers an HTTP POST callback to the merchant return URL with authentic bank reference numbers (`ResCode`, `RefId`, `SaleOrderId`).
3. **Given** an initiated transaction on Parsian (PEC), **When** the merchant calls the verification service with the transaction token, **Then** the system returns a successful verification response confirming transaction amount and approval.
4. **Given** an application integrating Pasargad (PEP) or Asan Pardakht, **When** executing the payment lifecycle, **Then** the transaction advances smoothly through initiation, hosted authorization, callback delivery, and verification.

---

### User Story 2 - Specialized Bank and Institutional PSP Adapters (Priority: P2)

A developer testing an integration for specialized or institutional payment gateways (Pardakht Novin / PNA, IranKish, Fanava Card, and Bank Sarmayeh) connects their payment module to the sandbox. The sandbox responds to the gateway's specific API endpoints, generates the exact tracking and reference formats required by each institution, and provides accurate error codes and status reports.

**Why this priority**: Many enterprise, governmental, and specialized merchant systems rely on Pardakht Novin, IranKish, Fanava, or Sarmayeh. Having these adapters ensures full coverage across all legacy and institutional banking systems.

**Independent Test**: Can be tested by executing sample transaction requests for each of the four specialized PSPs, validating that endpoint URLs, request parameters, response headers, and callback payloads adhere to each gateway's official documentation.

**Acceptance Scenarios**:

1. **Given** a payment initiation request to the Pardakht Novin (PNA) endpoint, **When** processed, **Then** the sandbox generates a valid gateway authority and redirects to the PNA-branded payment screen.
2. **Given** a payment transaction with IranKish, **When** the merchant verifies the payment after customer checkout, **Then** the system returns the transaction status with proper masked card number, reference ID, and approval code.
3. **Given** a transaction on Fanava Card or Bank Sarmayeh, **When** the complete payment flow executes, **Then** callback parameters and verification responses match the documented schemas.

---

### User Story 3 - Payment Facilitator (Pardakht-Yar) Adapters (Priority: P3)

A startup or independent developer using Iranian payment facilitators (ZarinPal, IDPay, and SizPay) uses the sandbox to validate their modern REST-based checkout flows. They initiate payments via simple JSON payloads, receive short payment URLs, test redirection via GET or POST callbacks, and verify transactions with multi-state confirmation responses.

**Why this priority**: Payment facilitators are the preferred gateways for startups and individual developers due to simpler onboarding. Full support for SizPay alongside ZarinPal and IDPay covers the primary modern payment aggregator ecosystem.

**Independent Test**: Can be tested by submitting payment creation requests to the SizPay, ZarinPal, and IDPay endpoints, following the returned payment URLs, and validating that callback query parameters and REST verification responses return expected HTTP status codes and JSON envelopes.

**Acceptance Scenarios**:

1. **Given** a payment creation request sent to SizPay with merchant credentials and invoice details, **When** accepted, **Then** the sandbox responds with a valid token and redirection URL.
2. **Given** a completed payment on SizPay, **When** the customer returns to the merchant callback URL, **Then** the callback delivers transaction status and confirmation tokens matching the SizPay API specification.
3. **Given** a payment on ZarinPal or IDPay, **When** verified for the first time, **Then** the sandbox returns the primary success code (e.g. code 100), and when verified a second time, it returns the already-verified status code (e.g. code 101).

---

### User Story 4 - Universal Scenario Simulation Across All Gateways (Priority: P4)

A QA engineer or developer configures test scenarios (approved, declined, bank timeout, pending settlement, payment cancellation, or verification failure) to simulate real-world failure modes. Regardless of which of the 13 gateways is being tested, the sandbox returns the gateway's native error codes and status messages rather than generic error responses.

**Why this priority**: Robust payment integrations must handle network timeouts, cardholder cancellations, insufficient funds, and verification failures gracefully. Protocol-accurate error codes allow developers to thoroughly test their error handling UI and recovery logic.

**Independent Test**: Can be tested by forcing each of the 6 scenario outcomes on each of the 13 gateway adapters and verifying that the returned HTTP status, XML/JSON body, and status codes match the official failure codes for that specific gateway.

**Acceptance Scenarios**:

1. **Given** a "decline" scenario configured for Behpardakht Mellat, **When** the payment is processed, **Then** the callback and inquiry return native bank decline codes (e.g., `ResCode: 41` or `42`).
2. **Given** a "timeout" scenario configured for Saman (SEP), **When** payment initiation or verification is requested, **Then** the sandbox delays or simulates gateway unresponsiveness to test the merchant application's timeout handling.
3. **Given** a "verify-stage failure" scenario configured on any of the 13 adapters, **When** the customer completes checkout successfully but the merchant calls the verify endpoint, **Then** verification fails with an authentic gateway error code, testing the merchant's reversal flow.
4. **Given** a "pending settlement" scenario, **When** verified, **Then** the transaction reports pending status and transitions to settled after the configured delay.

---

### User Story 5 - Gateway-Branded Hosted Checkout Experience (Priority: P5)

A developer testing a user flow manually in a web browser clicks through the checkout process. The sandbox serves a realistic hosted checkout page reflecting the branding, language (Persian/English), and input fields of the selected gateway, with interactive controls allowing the tester to simulate user approval, cancellation, or error injection directly from the browser.

**Why this priority**: Visual fidelity on the mock payment page helps QA teams and frontend developers experience the exact redirection and return behavior that end customers will encounter in production.

**Independent Test**: Can be tested by opening the hosted payment URL for each of the 13 adapters in a browser, confirming that the page loads the corresponding gateway identity, displays order details and amounts, and provides interactive buttons to approve, cancel, or fail the transaction.

**Acceptance Scenarios**:

1. **Given** an initiated transaction for any of the 13 adapters, **When** navigating to the checkout URL, **Then** the browser renders a hosted payment screen featuring the visual identity, logo, and layout of that specific gateway.
2. **Given** the hosted payment screen, **When** the tester clicks "Pay / Approve", **Then** the transaction is marked successful and the user is redirected to the merchant callback with valid parameters.
3. **Given** the hosted payment screen, **When** the tester clicks "Cancel", **Then** the transaction is marked cancelled/declined and the user is returned to the merchant callback with appropriate cancellation codes.

---

### Edge Cases

- **Credential Mismatch**: When a request contains invalid or empty merchant IDs, terminal IDs, or API keys, the adapter rejects the request with the gateway's native authentication error response.
- **Duplicate Payment Verification**: When an application calls the verification endpoint more than once for the same transaction, the first call returns success and subsequent calls return the gateway's native "already verified" code (e.g. 101 for ZarinPal, error code for SEP/Mellat) without double-crediting.
- **Expired Transaction Token**: When a customer attempts to access the checkout screen or verify a transaction after its validity window has expired, the gateway returns an expired-session error.
- **Verification of Unpaid / Cancelled Transaction**: When a merchant calls the verify endpoint for a transaction where the cardholder cancelled or payment failed, the verification is rejected with an invalid-status code.
- **Partial and Full Refunds / Reversals**: When reversal or refund is requested for a supported gateway, the system updates transaction status and returns proper refund acknowledgment, rejecting reversals on already-refunded or unverified transactions.
- **Amount Mismatch on Verification**: When the merchant application sends a verification request specifying an amount that does not match the originally initiated transaction amount, the adapter rejects verification with an amount-mismatch error code.
- **Unreachable Merchant Callback URL**: When the sandbox attempts to deliver an automatic callback or webhook to an unreachable or non-responsive merchant URL, the attempt is logged as failed without crashing the engine.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement full adapter specifications for all 13 Iranian payment gateways documented in `./docs/`:
  1. Behpardakht Mellat (`behpardakht`)
  2. ZarinPal (`zarinpal`)
  3. IDPay (`idpay`)
  4. Saman Electronic Payment / SEP (`saman-sep`)
  5. Sadad Bank Melli (`sadad-melli`)
  6. Parsian Electronic Commerce / PEC (`parsian-pec`)
  7. Pasargad Electronic Payment / PEP (`pasargad-pep`)
  8. Asan Pardakht / AP (`asan-pardakht`)
  9. Pardakht Novin Arian / PNA (`pardakht-novin`)
  10. IranKish (`irankish`)
  11. SizPay (`sizpay`)
  12. Fanava Card (`fanava`)
  13. Bank Sarmayeh (`sarmayeh`)
- **FR-002**: Each adapter MUST expose authentic entry-point URLs and communication protocols conforming to its official documentation in `./docs/`, including REST (JSON) endpoints and SOAP (XML/WSDL) endpoints.
- **FR-003**: The system MUST generate authentic tracking tokens and reference numbers for each gateway (e.g., `Authority`, `Token`, `RefId`, `SaleOrderId`, `SaleReferenceId`, `TraceNo`) matching expected formats and lengths.
- **FR-004**: Each adapter MUST render a hosted checkout page with matching gateway visual identity, transaction summary (order ID, amount, merchant name), and action buttons for confirmation and cancellation.
- **FR-005**: The system MUST format and transmit return callbacks in the exact format required by each gateway (HTTP POST with form data for Shaparak PSPs, HTTP GET with query parameters for REST aggregators).
- **FR-006**: Each adapter MUST implement payment verification and settlement endpoints returning native response structures, status codes, and tracking references.
- **FR-007**: Each adapter MUST implement refund and reversal endpoints where supported by the gateway's documented API specifications.
- **FR-008**: The system MUST map the sandbox's universal scenario outcomes (`approve`, `decline`, `timeout`, `refund`, `pending_settle`, `verify_fail`) to each gateway's authentic status codes and error messages.
- **FR-009**: The system MUST validate request credentials against the adapter's configured credential scheme (e.g., `merchant_id`, `terminal_id`, `username`, `password`, `api_key`) and reject missing or invalid credentials with gateway-native error responses.
- **FR-010**: The system MUST handle currency conversions between canonical Rials and gateway-specific currency expectations (Rials or Tomans) accurately across request and response payloads.
- **FR-011**: The system MUST guard against duplicate verification calls, returning the gateway's native "already verified" response code on subsequent verification attempts.
- **FR-012**: The system MUST record all inbound requests, outbound callbacks, and state transitions for each transaction to enable debugging and inspection in the management dashboard.
- **FR-013**: The system MUST support permissive cryptographic signature handling by default (accepting mock or dummy signatures without failure), while performing strict RSA or HMAC verification when private/public keys are configured in the adapter settings.
- **FR-014**: The system MUST generate realistic, deterministic cardholder metadata in callbacks and verification responses, including 16-digit masked PANs with recognized Iranian bank BIN prefixes, 12-digit Retrieval Reference Numbers (RRN), and 6-digit system trace audit numbers.

### Key Entities *(include if feature involves data)*

- **Payment Gateway Adapter**: Represents an individual gateway integration definition, including provider identifier, supported protocols (REST/SOAP), credential schema, endpoint path prefix, and default currency unit.
- **Adapter Configuration**: Project-specific configuration for a gateway adapter, holding merchant credentials, custom path overrides, active status, and default scenario preferences.
- **Simulated Transaction**: An individual payment lifecycle record tracking initiation parameters, amount in Rials, generated tokens, customer reference numbers, current state (initiated, pending, settled, declined, refunded, expired), and assigned scenario.
- **Callback Delivery Record**: An event log capturing the callback or webhook transmission attempt, including target URL, HTTP method, payload data, response code, and delivery timestamp.
- **Scenario Mapping**: Configuration table defining the translation between universal sandbox outcomes and the specific numeric codes, messages, and XML/JSON fields of each individual gateway.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can integrate and run complete payment cycles across all 13 documented gateways by updating only the gateway base URL in their application, requiring zero changes to their application's core payment logic.
- **SC-002**: 100% of the 13 documented gateways support the full four-stage lifecycle: initiation, checkout redirection, merchant callback delivery, and verification/settlement.
- **SC-003**: 100% of gateway callback payloads provide the exact parameter names, data types, and status values defined in the official bank and PSP technical specifications.
- **SC-004**: All 6 sandbox scenarios (approved, declined, timeout, refund, pending settle, verify failure) produce accurate gateway-specific status codes and error responses for all 13 adapters.
- **SC-005**: Payment initiation and verification responses in the local sandbox return within 200 milliseconds under standard test workloads.
- **SC-006**: Duplicate verification requests return the official "already verified" status in 100% of test attempts without altering transaction balance or state.
- **SC-007**: Hosted checkout pages for all 13 gateways load within 300 milliseconds and accurately display the gateway's visual identity, transaction amount, and action controls.

## Assumptions

- **Internal Canonical Currency**: All transaction records and internal accounting are stored canonically in Iranian Rials (IRR); gateways expecting Tomans (such as ZarinPal in Toman mode) are converted at the adapter boundary.
- **Local Network Accessibility**: Merchant application callback URLs are accessible via HTTP or HTTPS from the network environment where the sandbox engine is running.
- **Drop-in Client Compatibility**: Client applications communicate with the sandbox via standard HTTP REST or SOAP clients capable of directing traffic to custom endpoints.
- **Mock Banking Environment**: All payment processing is simulated in-memory and in the sandbox database; no live connections to Shaparak or banking production networks are initiated.
- **Credential Storage**: Merchant credentials for testing are stored within the sandbox project configuration without requiring external bank validation.
