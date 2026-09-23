# Feature Specification: Payment Gateway Sandbox (IPG Sandbox) MVP

**Feature Branch**: `001-mvp`

**Created**: 2026-09-23

**Status**: Draft

**Input**: User description: "$ARGUMENTS — free, self-hostable, CI-friendly payment-gateway simulator for Iranian developers (Zarinpal, IDPay, Behpardakht), with scenario controls, webhooks, and a bilingual FA/EN Linear-dark dashboard; public repo + free hosted demo at launch. Source artifacts: .specify/assessments/ipg-sandbox/ (problem.md, concept.md, decision.md, intake.md)."

## Clarifications

### Session 2026-09-23

- Q: What access gate should the free hosted demo have when a new visitor arrives? → A: Free email signup required before simulating, combined with rate limiting and per-visitor data isolation.
- Q: Should webhook/callback payloads sent to the developer's app match each real gateway's callback format, or use one unified sandbox format for all adapters? → A: Match each real gateway's callback format per adapter (subset of operations in scope).
- Q: How long should simulated transaction history be retained by default? → A: Fixed 1000-transaction cap per project everywhere (oldest dropped).
- Q: In what currency unit should amounts be expressed in the sandbox's transaction records and dashboard? → A: Rial everywhere (records, dashboard, fixtures); each adapter presents amounts in the unit its emulated real API expects.
- Q: After a transaction is forced into pending→settle, how long should it take to resolve to settled by default? → A: 5 seconds after checkout (configurable).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Free local drop-in simulation (Priority: P1)

A developer runs the sandbox on their own machine at zero cost, points their existing payment integration at it by swapping the gateway endpoint URL and test credentials (no changes to their application's core payment code), and completes a full simulated payment: initiate → hosted checkout page → return → verify — receiving a successful (approved) result.

**Why this priority**: This is the product's core promise — a free, self-hostable replacement for banktest.ir's paid hosted-only model. Without it there is no value proposition; every other story builds on transactions flowing through an emulated gateway.

**Independent Test**: Can be fully tested by starting the sandbox on localhost, configuring an app (or sample request flow) with the sandbox endpoint + test credentials, and completing one approved payment end-to-end — with no payment, account signup, or external service involved.

**Acceptance Scenarios**:

1. **Given** a fresh environment with the sandbox started locally, **When** a developer initiates a payment through a supported adapter's endpoint, **Then** a hosted checkout/redirect page is presented and, after confirmation, the developer receives an approved verification response — without any real money, static IP, or gateway certification.
2. **Given** the sandbox is running locally, **When** a new user obtains and uses it, **Then** no payment, credit purchase, or paid tier is required to reach a successful simulated payment.
3. **Given** a developer's app configured only with a swapped endpoint URL and test credentials, **When** a payment is initiated, **Then** the flow completes without requiring changes to the app's core payment logic (drop-in compatibility).

---

### User Story 2 - Forced lifecycle scenarios (Priority: P2)

A developer or QA engineer forces a specific transaction outcome — approve, decline, timeout/exception, refund, or pending→settle — per transaction or as a default, and sees the integration behave accordingly, including verification-stage failures (e.g., a payment that appears successful at checkout but fails at verify).

**Why this priority**: Scenario coverage is the key capability that hand-rolled mocks and banktest.ir's baseline do not provide for free; it is what makes the sandbox a *testing* tool rather than a happy-path stub.

**Independent Test**: Can be tested by setting each outcome in turn (via dashboard control or configuration) and confirming the resulting payment/verification response matches the forced outcome for every supported adapter.

**Acceptance Scenarios**:

1. **Given** a "decline" scenario is forced, **When** a payment is initiated and verified, **Then** the integration receives a declined result at the appropriate stage.
2. **Given** a "timeout" scenario is forced, **When** a payment is initiated, **Then** the response behavior simulates a timeout/exception rather than returning an immediate success.
3. **Given** a "pending→settle" scenario is forced, **When** the flow advances, **Then** the transaction first reports pending and resolves to settled about 5 seconds after checkout (default, configurable).
4. **Given** a "verify-stage failure" scenario is forced, **When** checkout succeeds but verification is requested, **Then** verification fails, exercising the app's failure path.

---

### User Story 3 - Webhook / callback delivery (Priority: P3)

The sandbox delivers simulated webhooks/callbacks to URLs the developer configures — including localhost endpoints of their own app — and records each delivery attempt, its result, and its history so the developer can debug callback handling.

**Why this priority**: Callback/webhook handling is a primary source of real-world payment bugs; without delivery to the developer's local app, the sandbox cannot cover async settlement flows.

**Independent Test**: Can be tested by configuring a local receiver URL, forcing a transaction outcome that triggers a callback, and confirming the receiver gets the payload and the delivery appears with its status in the dashboard.

**Acceptance Scenarios**:

1. **Given** a webhook URL pointing at the developer's local app, **When** a transaction reaches a callback-triggering stage, **Then** the payload is delivered to that URL.
2. **Given** a webhook target that is unreachable, **When** delivery is attempted, **Then** the failure is recorded and visible, and delivery is retried according to the configured policy.
3. **Given** multiple deliveries, **When** the developer views delivery history, **Then** each attempt shows target, timestamp, outcome, and payload.

---

### User Story 4 - Transaction dashboard with scenario controls (Priority: P4)

The developer opens a professional dark-themed dashboard, sees the list and detail of simulated transactions across adapters, forces scenarios from the UI, inspects webhook deliveries, and switches the interface between Persian (RTL) and English.

**Why this priority**: The dashboard is a stated differentiator vs banktest.ir and DIY mocks (professional, bilingual, credible), but the sandbox delivers testing value headlessly first; the UI amplifies adoption rather than enabling the core flow.

**Independent Test**: Can be tested by completing transactions, then verifying they appear with correct details; toggling FA/EN and confirming layout and text switch correctly including right-to-left layout; forcing a scenario from the UI and confirming the next transaction honors it.

**Acceptance Scenarios**:

1. **Given** completed and in-flight transactions, **When** the dashboard is opened, **Then** each transaction shows provider/adapter, amount, status, scenario applied, and timestamps.
2. **Given** the interface is set to Persian, **When** it renders, **Then** text is Persian and the layout is right-to-left; switching to English restores left-to-right.
3. **Given** a scenario is forced from the dashboard, **When** the next matching transaction runs, **Then** the forced outcome is applied.
4. **Given** a developer views a transaction, **When** they inspect it, **Then** request/response details relevant to debugging are visible.

---

### User Story 5 - CI-friendly headless use + free hosted demo (Priority: P5)

A QA/DevOps engineer drives the entire sandbox — payments, scenario forcing, webhook verification — without any UI, from an automated pipeline; and a prospective user can try a free hosted demo online before self-hosting.

**Why this priority**: CI-friendliness and zero-cost entry are core goals, but they exercise the same engine as P1–P3; the hosted demo is a launch channel, not a prerequisite for local value.

**Independent Test**: Can be tested by running a full approve/decline/timeout scenario sequence non-interactively in a pipeline and asserting results; and by reaching the hosted demo and completing one simulated payment without a credit card or payment.

**Acceptance Scenarios**:

1. **Given** a CI pipeline, **When** the scenario sequence runs non-interactively, **Then** each step's outcome is assertable from machine-readable responses and the run exits with a clear pass/fail result.
2. **Given** a new visitor, **When** they open the hosted demo and complete free email signup (no payment involved), **Then** they can simulate a payment, and their demo data is isolated so it does not persist in a way that exposes other users' data.

---

### Edge Cases

- Webhook receiver is down or slow at the moment of callback → delivery fails, is retried per policy, and the failure is visible in history (no silent loss).
- Invalid or unknown credentials / adapter misconfiguration → clear error surfaced to the caller and in the dashboard, not a hang or generic crash.
- Unsupported gateway operation is called → explicit "not supported by this adapter" response.
- Forced scenario conflicts (e.g., default approve but per-transaction decline forced) → per-transaction force wins over default.
- Timeout scenario vs. test harness timeouts → simulated timeout completes within a bounded, configurable delay so CI runs don't hang indefinitely.
- Checkout page abandoned (user never returns) → transaction remains pending/open and is distinguishable from settled or expired transactions.
- Two transactions share reference/amount concurrently → each is tracked and resolved independently.
- Hosted demo receives abusive or oversized traffic or signup spam → rate limiting and email signup gate keep the demo usable; no real money or card data exists to be compromised anywhere in the system.
- Language switch mid-session → UI fully re-renders in the selected language/Direction without data loss.
- Transaction count reaches the 1000-per-project history cap → oldest transactions are dropped; remaining records and meters stay consistent.
- Adapter fidelity gaps (esp. Behpardakht WSDL drop-in) → sandbox answers the documented subset of operations needed for the flows above; unsupported operations fail explicitly rather than silently corrupting state (byte-perfect emulation is out of scope; callback payloads follow each gateway's real format only for that in-scope subset).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST be fully runnable on a developer's own machine at zero cost, with no account, credit purchase, or paid tier required to simulate payments.
- **FR-002**: The system MUST emulate at least these three adapters: Zarinpal, IDPay, and Behpardakht (Mellat PSP) — supporting drop-in use where the developer changes only endpoint URL and test credentials.
- **FR-003**: The system MUST emulate the hosted checkout/redirect page step of a payment flow for each supported adapter.
- **FR-004**: The system MUST support the transaction lifecycle: initiate → checkout → verify/settle, with outcomes: approve, decline, timeout/exception, refund, and pending→settle — including verification-stage failure after a successful-looking checkout.
- **FR-005**: The system MUST allow forcing a specific outcome per transaction and as a configurable default, settable via dashboard and via a non-interactive interface (for CI).
- **FR-006**: The system MUST record every simulated transaction with adapter, amount, status/outcome, scenario applied, reference identifiers, and timestamps, and expose them for inspection; history MUST be capped at the most recent 1000 transactions per project, dropping oldest beyond the cap.
- **FR-007**: The system MUST deliver webhooks/callbacks to developer-configured URLs (including localhost), using each emulated gateway's real callback payload format for the operations in scope, apply a configurable retry policy on failure, and record every attempt with payload, timestamp, and result.
- **FR-008**: The system MUST provide a dashboard showing transaction list and detail, scenario controls, webhook delivery history, and per-adapter configuration/status.
- **FR-009**: The system MUST offer the interface in Persian and English, with correct right-to-left layout for Persian.
- **FR-010**: The system MUST be fully operable without the dashboard (headless): payment simulation, scenario forcing, and delivery verification must be completable from automated scripts/pipelines with machine-readable output.
- **FR-011**: The system MUST record usage meters (request counts, transaction counts, history depth) as data structures now, with no billing or payment processing attached.
- **FR-012**: The system MUST NOT process real payments, collect card data, or integrate with production gateways — simulation only.
- **FR-013**: A free hosted demo MUST be publicly available at launch, allowing a visitor to simulate a payment without paying; the self-hosted version and the hosted demo must expose the same core simulation capabilities.
- **FR-014**: The self-hosted default MUST require no login for local single-user use; the hosted demo MUST require free email signup before simulating, apply rate limiting, and isolate each visitor's data.
- **FR-015**: The system MUST be distributed as open source under AGPL-3.0 with a documented one-command local setup path.

### Key Entities *(feature involves data)*

- **Transaction**: One simulated payment — adapter, amount (canonical unit: Iranian Rial) and currency, status (pending/approved/declined/failed/refunded/settled), applied scenario, gateway + app references, timestamps; relates to one Adapter and zero-or-more WebhookDeliveries.
- **Scenario (Forced Outcome)**: The outcome to impose (approve, decline, timeout, refund, pending→settle, verify-fail) — either a project default or pinned to a specific transaction.
- **Adapter (Gateway Config)**: Which emulated provider is active (Zarinpal, IDPay, Behpardakht), its endpoint surface, and test credentials mapping.
- **Webhook Delivery**: One callback attempt — target URL, payload in the emulated gateway's real callback format, timestamp, result (delivered/failed), attempt count; belongs to a Transaction.
- **Usage Meter**: Counters scoped to a project (requests, transactions, history retained vs. cap) for future tiering; carries no billing.
- **Project / Visitor Session**: Container isolating transactions and settings for the hosted demo (and the future multi-project cloud tier).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user reaches their first successful simulated payment in under 10 minutes from obtaining the sandbox (baseline: unknown — banktest.ir requires signup + paid time credits before any test).
- **SC-002**: 100% of core simulation capabilities are usable at zero cost locally — no payment, credit, or signup wall exists on the self-hosted path (baseline: banktest.ir has no free tier, verified 2026-09-23).
- **SC-003**: All five lifecycle outcomes (approve, decline, timeout/exception, refund, pending→settle) plus verify-stage failure are exercisable on each of the three v1 adapters — 18/18 outcome×adapter combinations pass scripted checks (baseline: 0).
- **SC-004**: A full scenario sequence for one adapter completes headlessly in a clean environment in under 5 minutes with a machine-verifiable pass/fail result (CI-friendliness).
- **SC-005**: ≥95% of triggered webhook deliveries to an available localhost target arrive within 5 seconds of the triggering event; 100% of undelivered attempts are visible in history with retry outcome (no silent loss).
- **SC-006**: Users can complete the primary flows (simulate payment, force scenario, inspect transaction) in both Persian (RTL) and English without functional difference.
- **SC-007**: Post-launch adoption tracked from baseline 0: public repo stars, hosted-demo unique users, and CI integrations measured at 30 days (targets set at launch).
- **SC-008**: Qualitative — Persian dev community feedback rates the dashboard as professional/credible relative to banktest.ir (collected from launch threads; baseline unknown).

## Assumptions

- Target users are developers/QA with Docker-capable local machines; "one-command setup" means a single bootstrap command with no manual multi-service wiring (the specific technology stack is an implementation decision deferred to planning, per intake.md).
- Behpardakht WSDL fidelity: the adapter supports the documented subset of operations needed for the flows in FR-003/FR-004 on day one; byte-perfect emulation is explicitly out of scope (concept.md). A fidelity spike is scheduled early to de-risk this.
- V1 adapter set is capped at three (Zarinpal, IDPay, Behpardakht); all other gateways (Saman/Sadad/Melli bank ports, NextPay, Stripe/PayPal) are post-v1 behind the adapter interface.
- Timeout/exception simulation uses a bounded configurable delay (seconds, not minutes) so CI doesn't hang; exact default delay is an implementation parameter.
- Pending→settle resolves 5 seconds after checkout by default (configurable by the operator); stays well within SC-004's under-5-minute CI budget.
- Retry policy for webhooks defaults to a small bounded retry count with backoff; configurable per project.
- Metering (FR-011) is counter structures only — no invoices, payments entity, or billing UI in v1 (concept.md out-of-scope).
- The 1000-transaction history cap is per project (FR-006), applied uniformly on self-hosted and hosted demo; the cap value is configurable by the operator.
- Amounts are canonical Iranian Rial in records, dashboard, and test fixtures; adapters convert at the emulated API boundary when the real gateway's API expects a different unit (e.g., Toman), preserving drop-in request compatibility.
- Hosted demo runs on the requester's personal infrastructure, simulation-only (no real money/card data), protected by free email signup + rate limiting; multi-tenant hardening beyond visitor isolation is post-v1.
- Free email signup verifies address only (double opt-in or magic link acceptable); no passwords, profiles, or identity verification required.
- Pro-tier pricing and cloud paid features are launch-time/later decisions, not spec blockers (problem.md).
- Demand validation (unmeasured appetite) is a launch-signal concern, not a spec requirement; a fixtures-repo-first soft launch may run in parallel.
- banktest.ir competitive facts are current as of 2026-09-23 and must be re-verified before public positioning copy — a documentation/marketing task, not a product requirement.
- Out of scope for v1 (inherited from concept.md): record & replay live proxy, cloud tunnel agent, packaged CLI/SDK, AI-assisted tests, team workspaces, paid-tier features, >3 adapters.
