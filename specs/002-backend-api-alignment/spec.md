# Feature Specification: Backend API and Dashboard UI Alignment

**Feature Branch**: `002-backend-api-alignment`

**Created**: 2026-10-03

**Status**: Draft

**Input**: User description: "backend api should align and implement the functionality that the current UI needs, find the gaps"

## Clarifications

### Session 2026-10-03

- Q: How should the Payment Simulation feature execute transactions? → A: Both interactive checkout portal & one-click auto-complete. The simulation dialog allows either opening the mock banking checkout page for manual testing OR executing an instant end-to-end payment cycle to test webhooks and settlement immediately.
- Q: What scope of analytics and funnel statistics should the backend provide? → A: Unified analytics & funnel. A single analytics endpoint provides summary totals (volume, status counts, success rate) plus conversion drop-off counts across lifecycle stages (Initiated → Gateway Hosted → Callback Received → Verified / Settled).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive and Automated Payment Simulation (Priority: P1)

A developer or QA tester clicks the primary "Simulate Payment" action in the dashboard to generate a realistic payment without having to write or trigger external client code. They select the target payment gateway, amount in Rials, target scenario outcome (e.g. approved, declined, timeout, pending settle, or verify-stage failure), and optional callback URL and order reference. The system initiates the transaction, returns the generated authority and a direct URL to the hosted gateway checkout screen, and optionally allows completing the payment immediately to verify application webhooks and state transitions.

**Why this priority**: Testing integrations requires an easy way to trigger transactions directly from the console. Currently the UI header displays a "Simulate Payment" button that only redirects to the transaction list without enabling any simulation.

**Independent Test**: Can be tested by navigating to the dashboard, clicking "Simulate Payment", filling out the simulation dialog, and confirming that a transaction is created, displayed in the transactions table, and provided with an accessible hosted checkout link.

**Acceptance Scenarios**:

1. **Given** a user on the dashboard, **When** they trigger the "Simulate Payment" action, **Then** they are presented with options to select the payment gateway, enter the transaction amount, specify the expected outcome scenario, and provide optional callback/order metadata.
2. **Given** submitted simulation parameters, **When** the creation request is processed, **Then** a new transaction record is created with the chosen parameters and an accessible hosted checkout URL is returned.
3. **Given** an initiated simulation, **When** the user accesses the hosted checkout portal, **Then** they can interact with the mock banking page to confirm or cancel the transaction.

---

### User Story 2 - Accurate System-Wide Analytics and Metrics (Priority: P2)

A developer or engineering manager views the dashboard's primary overview cards to assess overall payment health. The dashboard presents accurate project-wide totals: total simulated monetary volume (in Rials), overall transaction success rate percentage, counts of approved versus declined transactions, gateway health status, and webhook delivery totals with failure rates. These numbers represent the entirety of the project's retained data rather than being computed only from the first page of recent records.

**Why this priority**: Overview metrics currently compute statistics purely client-side from the first 50 transactions loaded on page 1. When projects accumulate hundreds of records, displayed metrics become inaccurate and misleading.

**Independent Test**: Can be tested by seeding more than 50 transactions with known amounts and statuses, and verifying that the summary cards display exact aggregate values matching the entire database rather than only the first 50 items.

**Acceptance Scenarios**:

1. **Given** a project with 200 recorded transactions across multiple gateways, **When** the user loads the dashboard overview, **Then** the total volume, total record count, and success rate reflect all 200 transactions.
2. **Given** simulated transactions across all configured gateways, **When** viewing the gateway status card, **Then** the count of active gateways reflects real project activity rather than only gateways present in the current pagination window.
3. **Given** webhook delivery activity, **When** reviewing the callback card, **Then** the total deliveries and failed delivery count accurately reflect all webhook delivery logs.

---

### User Story 3 - Transaction Search, Filtering, and Pagination (Priority: P3)

A developer investigating a test run needs to locate a specific transaction among hundreds of records. They enter an authority token, order reference, or description into a search box, filter by specific gateway adapter and status (e.g. settled, pending, declined), and navigate between pages of results using pagination controls.

**Why this priority**: As transaction volume grows during testing, finding specific records without free-text search or multi-criteria filtering becomes cumbersome, and missing pagination controls leaves older records inaccessible through the interface.

**Independent Test**: Can be tested by performing text searches for specific order references and authority strings, applying gateway and status filters, and verifying that the resulting list matches the criteria and reflects correct page counts.

**Acceptance Scenarios**:

1. **Given** a collection of transactions, **When** the user enters a search query matching an authority or order reference, **Then** only matching transactions are returned.
2. **Given** a selected gateway adapter and status filter, **When** applied, **Then** the results are scoped strictly to the chosen criteria.
3. **Given** more results than the selected page size, **When** navigating to the next page, **Then** subsequent records are loaded with clear page indicators.

---

### User Story 4 - Webhook Delivery Management and Connectivity Testing (Priority: P4)

A developer configuring their local server to receive payment notifications views the webhooks section to inspect delivery payloads and verify connectivity. They can filter deliveries by outcome (delivered, failed, pending) or specific transaction, inspect the exact JSON payload and HTTP response code, retry failed attempts, and trigger a test webhook ping to verify that their local receiver endpoint is reachable before running full payment scenarios.

**Why this priority**: Webhook reliability is critical for asynchronous payment confirmation. Developers need to test whether their webhook listener is receiving payloads properly without initiating a full checkout sequence each time.

**Independent Test**: Can be tested by updating the project's webhook destination URL, triggering a test webhook ping from the dashboard, and confirming that the receiver gets the ping payload and a corresponding delivery log entry is created.

**Acceptance Scenarios**:

1. **Given** a configured project webhook URL, **When** the user clicks "Send Test Webhook", **Then** the system dispatches a test payload and records the HTTP response status.
2. **Given** a list of webhook deliveries, **When** filtering by delivery outcome, **Then** only matching attempts are displayed.
3. **Given** a failed delivery attempt, **When** the user clicks retry, **Then** an immediate re-delivery is executed and the updated status is displayed.

---

### User Story 5 - Transaction Detail Actions and Hosted Checkout Access (Priority: P5)

A developer inspecting an individual transaction on its detail page can review full request and response payloads, copy identifiers, adjust forced scenarios, immediately access the hosted gateway checkout page for transactions still awaiting payment, or permanently delete/purge test records that are no longer needed.

**Why this priority**: Full lifecycle control over individual transactions completes the debugging experience and allows testers to clear stale data or complete in-flight checkouts manually.

**Independent Test**: Can be tested by opening an initiated transaction, clicking the hosted checkout link to complete the payment flow, and testing the transaction deletion action to confirm the record is purged.

**Acceptance Scenarios**:

1. **Given** a transaction in initiated or pending state, **When** viewing its detail page, **Then** a direct action to open the hosted checkout portal is visible.
2. **Given** an existing transaction, **When** the user triggers the delete action and confirms, **Then** the transaction and associated delivery records are removed.

---

### Edge Cases

- **Zero Transactions**: When a new project has no transactions, analytics metrics must return zero values gracefully without divide-by-zero errors or broken visual cards.
- **Search Queries with Special Characters**: Search inputs containing Persian characters, numbers, dashes, and URL-encoded symbols must be sanitized and matched without application errors.
- **Unreachable Webhook Destinations**: Test pings to invalid hosts, private loopback addresses, or non-responsive ports must time out within 3 seconds and report structured error diagnostics rather than freezing the interface.
- **Purging In-Flight Transactions**: Purging a transaction that is currently scheduled for delayed settlement must cancel any background timers or worker tasks associated with that transaction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a payment simulation capability allowing users to create simulated transactions by specifying adapter, amount in Rials, outcome scenario, and optional metadata.
- **FR-002**: System MUST return the complete, accessible hosted checkout URL for any initiated or pre-seeded transaction.
- **FR-003**: System MUST provide an aggregate metrics endpoint returning project-wide totals: total simulated volume in Rials, total transactions count, count by status (settled, declined, pending, failed), count by scenario, and overall success rate percentage.
- **FR-004**: System MUST calculate overview metrics across all retained records rather than restricting aggregation to the current pagination window.
- **FR-005**: System MUST support free-text search across transactions matching against authority, order reference, and description fields.
- **FR-006**: System MUST support combined filtering of transactions by gateway adapter, transaction status, and date range with pagination metadata (page, page size, total matching items, total pages).
- **FR-007**: System MUST provide a webhook connectivity test ("ping") endpoint that sends a standardized test payload to the configured project webhook URL and records the outcome.
- **FR-008**: System MUST allow configuring the project's default webhook URL, maximum webhook retry attempts, and transaction history cap from the project settings interface.
- **FR-009**: System MUST allow permanently deleting individual transactions and cascading the deletion to associated delivery logs.
- **FR-010**: System MUST handle cross-origin resource requests for all configured dashboard host and port combinations without blocking browser fetch calls.
- **FR-011**: System MUST support both interactive hosted checkout portal navigation and an automated one-click completion option (simulating initiate, customer checkout, and verification in a single action).
- **FR-012**: System MUST report lifecycle conversion funnel statistics (counts and drop-off rates across Initiated -> Gateway Hosted -> Callback -> Settled) as part of a unified aggregate analytics endpoint.

### Key Entities

- **Transaction**: Represents a simulated payment through a specific gateway adapter, containing monetary amount in Rials, status, forced and effective scenarios, authority token, external checkout URL, order metadata, and raw communication payloads.
- **Project Metrics**: Aggregated summary of all transaction and webhook activity within a project, including total volume, transaction counts categorized by status and scenario, overall success rate, and active adapter status summary.
- **Webhook Delivery**: Record of an HTTP callback attempt dispatched to an external endpoint, containing target URL, trigger stage, attempt counter, response status code, error detail, and payload data.
- **Project Configuration**: Global settings governing sandbox behavior, including default scenario outcome, delay parameters for asynchronous settlement and timeouts, webhook retry policies, default destination URL, and retention limits.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can initiate and navigate to a simulated payment in under 10 seconds from any dashboard screen.
- **SC-002**: Dashboard overview metrics reflect 100% of historical transactions within the retention cap, eliminating discrepancies between overview cards and database contents.
- **SC-003**: Transaction searches return matching results in under 500 milliseconds for projects containing up to the maximum retention limit of 1,000 records.
- **SC-004**: Webhook ping tests report delivery success or diagnostic failure reasons within 3 seconds of initiation.
- **SC-005**: All primary dashboard navigation actions and controls function end-to-end without encountering unhandled API exceptions or missing backend routes.

## Assumptions

- The sandbox operates under the local self-hosted profile by default where a single shared project is used, though all data queries remain cleanly scoped by project identifier.
- The standard retention cap is 1,000 transactions per project, so database aggregation queries perform efficiently without requiring specialized background pre-aggregation tables.
- All monetary amounts remain normalized to Iranian Rials in storage and analytics calculations.
- Gateway-specific endpoints (`/zarinpal/*`, `/idpay/*`, `/behpardakht/*`) continue to adhere strictly to each provider's real-world protocol specifications.
