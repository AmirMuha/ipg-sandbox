# Feature Specification: Client Payment Journeys — End-to-End Proof

**Feature Branch**: `[008-client-e2e-tests]`

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "write E2E tests as a client imagine a client using this website using this platform for managing his payments to prove this project."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Merchant completes a payment end to end (Priority: P1)

A merchant signs in to the dashboard, creates a test payment, is taken to the hosted gateway checkout the way their shopper would be, confirms the payment, and then sees the transaction settle in their console after their backend verifies it.

**Why this priority**: This is the platform's core promise — an emulated gateway that behaves like the real one from initiation to settlement. If this journey cannot be proven, nothing else matters.

**Independent Test**: A single scripted session can create the payment from the console, confirm it on the hosted checkout page, verify it, and observe a settled row with the correct amount and authority in the transaction list.

**Acceptance Scenarios**:

1. **Given** a signed-in merchant on the console, **When** they create a payment and choose the gateway checkout step, **Then** the hosted checkout page opens showing that payment's authority and amount.
2. **Given** the hosted checkout page, **When** the shopper confirms the payment, **Then** they are returned to the merchant's callback destination and the transaction moves out of the initial state.
3. **Given** a confirmed payment, **When** the merchant's backend verifies the payment with its credentials, **Then** the transaction becomes settled and the console shows it as settled on refresh.
4. **Given** the merchant declines to pay, **When** they cancel on the hosted checkout, **Then** the transaction is recorded as declined, not settled.

---

### User Story 2 - Client provisions and uses an API key (Priority: P1)

A client creates an API key for their server-side integration, copies the secret exactly once, uses it to authenticate a real sandbox request, and later revokes it when it is no longer needed.

**Why this priority**: Programmatic access is how a client actually integrates. A key that cannot authenticate, or that keeps working after revocation, is a security defect.

**Independent Test**: Create a key in the dashboard, use its secret to call a sandbox endpoint successfully, revoke it in the dashboard, and confirm the same call is then rejected.

**Acceptance Scenarios**:

1. **Given** a signed-in merchant, **When** they create a named API key, **Then** the secret is shown once with the documented key prefix, and the list shows only the name, masked suffix, and timestamps.
2. **Given** a freshly created key, **When** the client sends it as a bearer credential to a sandbox payment endpoint, **Then** the request is authenticated and succeeds.
3. **Given** an active key, **When** the merchant revokes it, **Then** the key disappears from the list and subsequent requests using it are rejected.
4. **Given** the key list was reloaded, **When** the merchant looks for the secret again, **Then** it is nowhere in the interface.

---

### User Story 3 - Client wires webhooks and sees delivery proof (Priority: P2)

A client points the project at their own callback endpoint, receives the event the sandbox sends when a payment settles, and can inspect the delivery record in the dashboard.

**Why this priority**: Webhooks are the half of a payment integration that runs asynchronously. A sandbox that never proves delivery leaves clients guessing.

**Independent Test**: Configure a reachable callback endpoint, settle a payment, and observe both the event received at the endpoint and a delivered row in the webhook log.

**Acceptance Scenarios**:

1. **Given** a configured callback endpoint, **When** the client saves project settings, **Then** the dashboard shows the endpoint as the active target.
2. **Given** a settled payment, **When** the sandbox dispatches the event, **Then** the client endpoint receives a payload containing the payment authority and outcome, and the webhook log records a delivered attempt.
3. **Given** an unreachable endpoint, **When** the client uses the connection probe, **Then** the probe reports failure with a reason instead of claiming success.

---

### User Story 4 - Client finds, inspects, and purges a transaction (Priority: P2)

A client searches for a specific payment by its reference, filters the list by status, opens its details, and removes test records they no longer need.

**Why this priority**: Managing payments is the stated goal; a list that cannot be searched or cleaned up is not manageable.

**Independent Test**: Search for a known authority, observe exactly that payment, open its detail view, and delete it with confirmation.

**Acceptance Scenarios**:

1. **Given** many payments, **When** the client searches by an authority, **Then** only matching payments are listed.
2. **Given** a status filter, **When** the client selects settled, **Then** no non-settled payment is listed.
3. **Given** a payment in the list, **When** the client opens its details, **Then** the amount, status, gateway, and authority match the record.
4. **Given** a test record, **When** the client deletes it after confirming, **Then** it no longer appears anywhere in the console.

---

### User Story 5 - Dashboard protects merchant data (Priority: P3)

An unauthenticated visitor cannot reach merchant screens, and a signed-in merchant can sign out and lose access.

**Why this priority**: The console exposes payment data and credentials; unauthenticated access would invalidate every other journey.

**Independent Test**: Open a console URL without a session and confirm the visitor is sent to sign-in; sign in with valid credentials and confirm the console loads.

**Acceptance Scenarios**:

1. **Given** no session, **When** a visitor opens the console, **Then** they are redirected to sign-in.
2. **Given** valid credentials, **When** the merchant signs in, **Then** the console loads with their data.
3. **Given** invalid credentials, **When** the merchant attempts to sign in, **Then** an error is shown and no session is created.

### Edge Cases

- A payment whose shopper abandons the hosted checkout must not settle.
- A webhook target that refuses connections must be recorded as failed, not silently dropped.
- A revoked API key used concurrently must be rejected from the moment of revocation.
- An empty transaction list must render an explicit empty state rather than an error.
- Re-running the full suite against a fresh environment must not depend on data left by a previous run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The proof suite MUST exercise every journey through the product's user interface and its documented public API only; it must not read or write the database directly.
- **FR-002**: The suite MUST create its own merchant account per run so repeated runs start from a known state and do not collide.
- **FR-003**: The suite MUST prove a complete payment lifecycle: creation, hosted checkout display, shopper confirmation, merchant verification, and the settled state reflected in the console.
- **FR-004**: The suite MUST prove that a cancelled checkout is recorded as declined and does not settle.
- **FR-005**: The suite MUST prove API-key creation, one-time secret display, authenticated use, revocation, and post-revocation rejection.
- **FR-006**: The suite MUST prove webhook configuration, an actual event delivered to a client-controlled endpoint, and the delivery record visible in the dashboard.
- **FR-007**: The suite MUST prove transaction search, status filtering, detail inspection, and deletion-with-confirmation.
- **FR-008**: The suite MUST prove that unauthenticated console access is redirected to sign-in and that valid credentials grant access.
- **FR-009**: Every assertion MUST be against user-visible state (page content, received callback payload, API response) rather than internal storage or implementation-specific selectors alone.
- **FR-010**: The suite MUST run unattended, headlessly, and deterministically with a single command, and MUST clean up every process and temporary resource it starts.
- **FR-011**: The suite MUST NOT require any external network service; the only network participants are the locally running product components and the suite's own callback endpoint.
- **FR-012**: The suite MUST be repeatable: running it twice in a row against a fresh environment MUST produce the same result.

### Key Entities

- **Merchant account**: The identity under test, created per run, owning one project and its adapters.
- **Payment**: The transaction record whose authority, amount, status, and gateway are asserted across console, checkout, and API.
- **API key**: A programmatic credential shown once, used as a bearer token, then revoked.
- **Webhook delivery**: The record of an event sent to the client's endpoint, with target, stage, attempt, and result.
- **Callback endpoint**: The client-controlled receiver used to prove event delivery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A complete payment journey — create, pay, verify, observe settled — is demonstrated from a cold start in under 3 minutes of wall-clock time.
- **SC-002**: The full suite runs in under 10 minutes on a developer machine with no manual steps beyond one command.
- **SC-003**: 100% of the rejection scenarios (no session, revoked key, unreachable callback) fail closed with no unintended data written.
- **SC-004**: The suite passes on three consecutive runs against freshly initialized environments without manual cleanup between runs.
- **SC-005**: Every user story above is covered by at least one independently failing scenario, so a regression in any single journey is attributable without reading logs.
- **SC-006**: A failure report identifies the journey and the user-visible expectation that broke, not merely a stack trace.

## Assumptions

- The product's engine and dashboard are started locally by the same command that runs the suite; the suite does not assume an already-running stack.
- The environment has no outbound mail service, so account creation for the suite uses the product's registration API and then signs in through the interface. Email one-time-code registration remains covered by the API's own contract tests, not by this browser suite.
- Only the gateway enabled by default on a fresh project is required; other gateways keep their existing coverage elsewhere.
- Payment verification is a merchant-backend responsibility, so the suite performs it with the merchant's credential over the public API rather than through a dashboard button.
- Fresh data per run is achieved with a unique merchant email and a throwaway local database.
