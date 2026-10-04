# Feature Specification: Launch Readiness Flows (Login, Purchase, Checkout, Usage, Restrictions)

**Feature Branch**: `004-launch-readiness-flows`

**Created**: 2026-10-04

**Status**: Draft

**Input**: User description: "make sure login,purchase,checkout,usage,limitations,restrictions flows are correctly implemented, so I can launch the project"

## Clarifications

### Session 2026-10-04

- Q: What authentication mechanism is required for the launch version of the console? → A: Google OAuth, GitHub OAuth, and simple email/password credentials with session handling.
- Q: How should users purchase or activate paid plans at launch? → A: Live Zarinpal payment gateway integration (payment request, redirect to Zarinpal checkout, callback verification, and automatic workspace plan upgrade).
- Q: How should the system enforce daily request and active gateway limits when a workspace exceeds free tier quotas? → A: Hard block: return HTTP 429 (Too Many Requests) to API callers when daily limit is exhausted, and block activating more than 2 gateway adapters in the console UI.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hosted Payment Checkout Simulation (Priority: P1)

An end-buyer or developer testing a payment integration is redirected to the hosted checkout page after initiating a transaction. The checkout page displays the transaction details (amount, order reference, merchant name, and gateway branding). The user enters test card information or clicks an action button to confirm or cancel the payment, and is redirected back to the merchant's callback URL with accurate outcome parameters.

**Why this priority**: The hosted checkout page is the central visual and functional interaction point for all simulated payments. Without a functioning checkout page, end-to-end payment simulations cannot be completed by merchants or automated test suites.

**Independent Test**: Initiate a payment transaction for any supported gateway, open the returned checkout link in a web browser, complete the payment interaction, and verify that the browser is returned to the merchant callback URL with valid verification tokens.

**Acceptance Scenarios**:

1. **Given** an initiated payment transaction, **When** the user navigates to the checkout URL, **Then** the hosted checkout page renders with the correct payment amount, merchant identifier, and gateway theme.
2. **Given** a user on the checkout page, **When** they click "Pay" with valid test credentials, **Then** the transaction state transitions to successful and the user is redirected to the callback URL.
3. **Given** a user on the checkout page, **When** they click "Cancel", **Then** the transaction is marked as cancelled or failed, and the user is returned to the callback URL with appropriate cancellation status.

---

### User Story 2 - User Login & Access Control (Priority: P1)

A developer or merchant visits the platform marketing page and accesses the login interface. They authenticate their identity to access the private project console, where their transactions, API credentials, and gateway settings are isolated from other accounts.

**Why this priority**: Securing merchant data and separating sandbox environments requires an authentication gateway before accessing project management tools.

**Independent Test**: Access the login page, provide valid authentication credentials, and confirm immediate redirection to the protected console dashboard with access to project resources.

**Acceptance Scenarios**:

1. **Given** a visitor on the login page, **When** they submit valid credentials, **Then** they are authenticated and redirected to the management console.
2. **Given** an unauthenticated visitor, **When** they attempt to access protected console pages directly, **Then** they are redirected to the login page with an appropriate notice.
3. **Given** a visitor submitting invalid or malformed credentials, **When** authentication fails, **Then** an explicit error message appears and the user remains on the login page.

---

### User Story 3 - Plan Selection & Purchase Flow (Priority: P2)

A registered developer views the pricing plans (Developer Free tier vs Team / Pro paid tiers) and selects a plan to upgrade their workspace capabilities (higher daily request limits, all gateway adapters, extended history retention). They complete the purchase or upgrade step and receive confirmed access to the higher plan features.

**Why this priority**: Commercial launch requires clear monetization pathways and a mechanism for users to transition from free simulation limits to paid tiers.

**Independent Test**: Navigate to the pricing page as a logged-in user, select the Team plan, complete the upgrade workflow, and verify that the workspace status reflects the new tier and entitlements.

**Acceptance Scenarios**:

1. **Given** a user on the pricing page, **When** they click to select the Free Developer plan, **Then** their account is activated on the standard free tier without payment details required.
2. **Given** a user selecting the Team plan, **When** they proceed with the upgrade flow, **Then** the order summary is shown and the upgrade process completes with confirmed active status.
3. **Given** an upgraded account, **When** the user checks workspace settings, **Then** their current active plan, renewal or expiration status, and expanded entitlements are visible.

---

### User Story 4 - Usage Tracking & Quota Metering (Priority: P2)

Developers and team managers can monitor their sandbox consumption in real time from the dashboard. The system tracks key usage metrics—daily API request volume, cumulative transaction count, retained history count, and active gateway adapters—and displays them clearly alongside tier thresholds.

**Why this priority**: Users must understand their resource consumption to avoid unexpected service interruptions and recognize when upgrading to a paid tier is necessary.

**Independent Test**: Perform multiple simulated payment calls, refresh the console dashboard, and verify that the displayed request counters and transaction tallies increment accurately.

**Acceptance Scenarios**:

1. **Given** an active workspace, **When** API requests and transactions are processed, **Then** usage meters increment atomically to reflect total requests and retained transactions.
2. **Given** a developer viewing the console, **When** they inspect the workspace overview or settings, **Then** current consumption is displayed against tier allowances (e.g., current requests vs daily maximum).
3. **Given** a 24-hour cycle reset for daily quotas, **When** the reset boundary passes, **Then** daily request counters reset to zero while lifetime transaction counts persist.

---

### User Story 5 - Limitations & Restrictions Enforcement (Priority: P3)

The system automatically enforces plan-specific constraints based on the workspace's active tier. Free tier accounts are constrained by daily request caps (100 requests/day), concurrent active gateway limits (max 2 gateways), and history retention limits (1,000 transactions or 24 hours). When a limit is reached, the system prevents unauthorized overages and directs the user to upgrade.

**Why this priority**: Prevents infrastructure abuse on hosted deployments, protects free tier margins, and provides natural commercial incentives to convert to paid plans.

**Independent Test**: Exhaust the allowed free tier request quota or attempt to enable a third gateway on a two-gateway plan, and verify that the system denies the action with a clear restriction explanation.

**Acceptance Scenarios**:

1. **Given** a workspace that has exhausted its daily request allowance, **When** a new transaction request arrives, **Then** the request is rejected with a rate limit notice advising the developer to upgrade or wait for quota reset.
2. **Given** a Free tier workspace with 2 active gateways, **When** the developer attempts to enable a third gateway, **Then** the configuration change is blocked with an explanation of plan constraints.
3. **Given** a workspace reaching its transaction history retention cap, **When** new transactions are recorded, **Then** oldest transactions beyond the cap are pruned so stored records remain within the allowed boundary.

---

### Edge Cases

- **Checkout Session Expiry**: What happens if a buyer leaves a hosted checkout page open for hours before clicking Pay? The session must expire after a configurable duration (default 15 minutes), displaying an expired payment notice and returning a cancellation status.
- **Concurrent Quota Depletion**: If multiple requests arrive simultaneously right at the quota boundary, the system must atomically record requests so that the limit is never exceeded by race conditions.
- **Payment Failure During Plan Purchase**: If a user attempts to purchase a paid plan and the payment or activation process fails, their workspace remains on the existing tier without partial activation.
- **Graceful Downgrade or Cancellation**: When a user cancels a paid plan, their elevated benefits remain active until the end of the paid period, after which constraints smoothly apply without corrupting historical data.
- **Local vs Cloud Mode Discrepancies**: In self-hosted local mode, artificial commercial restrictions (such as daily payment caps) should be configurable or disabled by default, preserving unlimited developer freedom for local development.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a responsive, bilingual (Persian RTL and English LTR) hosted checkout page for simulating end-user card payments.
- **FR-002**: Checkout page MUST present payment details (amount, currency, order reference, merchant name) and clear actions to approve or cancel the payment.
- **FR-003**: System MUST redirect the user back to the merchant's specified callback URL upon checkout completion or cancellation, carrying gateway-compatible status parameters.
- **FR-004**: System MUST authenticate users prior to accessing the private management console via Google OAuth, GitHub OAuth, or standard email/password credentials, establishing secure authenticated sessions.
- **FR-005**: System MUST isolate project data (transactions, API keys, webhook logs, adapter settings) per workspace or user account.
- **FR-006**: System MUST allow users to view available subscription tiers (Developer Free vs Team Paid) on a dedicated pricing interface.
- **FR-007**: System MUST provide a plan upgrade workflow where users transition to a paid plan via a live Zarinpal payment gateway checkout flow (merchant request, user redirect, callback verification, and automatic plan entitlement activation).
- **FR-008**: System MUST record and persist usage metrics per workspace: lifetime total requests, lifetime total transactions, retained transactions, and daily request count.
- **FR-009**: System MUST display real-time usage consumption and quota ceilings within the management dashboard.
- **FR-010**: System MUST enforce a daily request ceiling on free-tier workspaces by rejecting excess requests with HTTP 429 (Too Many Requests) and machine-readable rate-limit details.
- **FR-011**: System MUST restrict free-tier accounts to a maximum of 2 concurrent active payment gateway adapters while allowing paid accounts to activate all available gateways.
- **FR-012**: System MUST enforce the transaction history cap (retaining the most recent N transactions, default 1,000 for free tier), purging older records atomically upon insert.
- **FR-013**: System MUST provide clear, user-facing error messages when actions are blocked due to plan restrictions, explaining the constraint and providing an upgrade pathway.
- **FR-014**: System MUST maintain operational independence between local self-hosted deployments (which allow unconstrained sandbox use) and hosted multi-tenant deployments.

### Key Entities

- **User**: Represents an authenticated merchant or developer account with login credentials, profile data, and associated workspaces.
- **Workspace / Project**: The tenant boundary containing adapter configurations, webhooks, transaction records, and assigned subscription tier.
- **Subscription Tier**: Defines plan attributes including name, price, daily request allowance, maximum active gateways, history retention ceiling, and feature flags.
- **Usage Quota**: The living counter record tracking daily requests, total transactions, and quota reset timestamps for a workspace.
- **Checkout Session**: A short-lived state entity representing a buyer's visit to the hosted payment simulator, tied to an in-flight transaction.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: End-to-end checkout simulation (from checkout page navigation to merchant return) can be completed in under 15 seconds.
- **SC-002**: 100% of checkout payments correctly update transaction status and redirect to merchant callback URLs with valid parameters.
- **SC-003**: Users can complete account registration/login and reach an active console in under 60 seconds.
- **SC-004**: Usage meters reflect new transactions and API calls within 1 second of occurrence.
- **SC-005**: Quota enforcement strictly prevents 100% of requests exceeding tier limits on constrained accounts without data corruption or memory leaks.
- **SC-006**: 95% of users can identify their current plan, remaining usage, and active restrictions without contacting support.

---

## Assumptions

- **Local Development Parity**: In local single-developer environments (`ENGINE_PROFILE=local`), limitations such as daily request quotas are either set to unlimited or large defaults to avoid impeding local testing.
- **Currency Unit Consistency**: All pricing and transaction amounts display in Toman for commercial plans and Rial for gateway transaction emulation, formatted with standard Persian and English numerals based on active locale.
- **Standard Session Lifespan**: User login sessions remain valid for at least 7 days unless explicitly logged out.
- **Checkout Session Timeout**: Hosted checkout simulation links expire after 15 minutes of inactivity if neither payment nor cancellation is submitted.
- **Graceful Degraded State**: When daily request quota is reached, existing transaction logs and historical analytics remain readable in the dashboard even if new transactions are blocked.
