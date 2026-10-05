# Feature Specification: Admin IPG Visibility Control

**Feature Branch**: `006-admin-ipg-visibility`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "only admin should be able to enable/disable the ipgs, and the shown ipgs inside the /fa/providers page should change base on it"

## Context

The toggle surface from 005-admin-ipg-toggle exists and works, but it is not admin-only — any
signed-in user who owns a project can change their own project's IPG flags. The public
`/fa/providers` marketing page is a hardcoded list of 13 gateways and never reflects any toggle.
This feature closes both gaps: a single global, admin-only control over which gateways are offered,
and a providers page that shows exactly what is currently offered.

**Terminology** — "IPG" and "provider" are the same thing in this product; both words appear in
existing screens and contracts. "Admin" means an operator of the platform, distinct from a signed-in
merchant user. A gateway that is turned off for everyone is "withdrawn"; a gateway turned off for one
project only is "disabled".

## Clarifications

### Session 2026-10-05

- Q: When an admin withdraws a gateway that a merchant already had enabled, what should that gateway
  look like in the merchant's own settings page? → A: Locked, withdrawn state — the card stays listed
  and marked as withdrawn by the operator, the merchant's toggle cannot flip it back on, and the
  merchant's own stored setting is preserved so re-offering restores it.
- Q: When an admin changes a gateway's availability, should the system keep a record of who changed
  it, what they changed, and when? → A: No audit trail — only the current state is stored. Accepted
  consequence: the system cannot answer "who disabled this gateway and when", so diagnosing a payment
  failure caused by a withdrawal relies on the administrator's own recollection. Deliberate scope
  reduction; revisit if the platform gains more than one operator.
- Q: Where should the global availability state be stored, given that the codebase already has a
  per-project enabled flag on each gateway's configuration row? → A: Reuse the existing per-project
  flag. The administrator's toggle writes the default project's row for each gateway, and the
  availability gate reads that row. No new stored state and no migration. Accepted consequence: the
  global gate is only as global as the project the administrator controls, so planning must first
  confirm a single default project exists and is unambiguously the one to read.
- Q: How quickly does the providers page need to reflect an administrator's change after they save it?
  → A: Always fresh, no cache. The page reads live state on every request, so the next visitor load
  shows the current set and there is no cache to invalidate. Accepted cost: one state read per page
  view, accepted because the page is already generated per request.
- Q: Should merchants still be able to toggle gateways on and off for their own project, or does the
  admin control the only gateway switch? → A: Remove the merchant toggle. The administrator is the
  only writer of gateway availability, so a gateway's state has exactly one writer and one meaning.
  Accepted cost: merchants lose the ability to turn a gateway off for themselves, and the per-project
  plan limit on how many gateways a project may activate no longer has a user-facing control, so it
  must be removed from the behaviour rather than left as a rule nothing can trigger.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Controls Which Gateways Are Offered (Priority: P1)

An administrator needs to be the only person able to turn a payment gateway on or off for the whole
platform, so that merchants can never offer a gateway the operator has not vetted, and no gateway is
offered that the operator has withdrawn.

**Why this priority**: This is the whole ask. Without it there is no source of truth for the
providers page to read.

**Independent Test**: Sign in as an admin, open the gateway management surface, disable a gateway,
reload, and confirm the disabled state persisted and that the control is not reachable by anyone else.

**Acceptance Scenarios**:

1. **Given** an administrator is signed in, **When** they open the gateway management surface,
   **Then** they see every supported gateway with its current offered/withdrawn state.
2. **Given** an administrator toggles a gateway's state, **When** the change is saved,
   **Then** the new state persists across page reloads and a confirmation is shown.
3. **Given** a signed-in merchant user who is not an administrator, **When** they attempt to change
   any gateway's state, **Then** the change is refused, no state is altered, and they are told they
   do not have permission.
4. **Given** a signed-in merchant user who is not an administrator, **When** they try to reach the
   gateway management surface directly, **Then** they cannot see it and cannot act on it.
5. **Given** a visitor with no session at all, **When** they try to change a gateway's state,
   **Then** the request is refused.

### User Story 2 - Public Providers Page Reflects Gateway State (Priority: P2)

A prospective merchant visiting `/fa/providers` needs to see only the gateways that are actually
available to them, so the page never advertises something they cannot use, and never hides something
they can.

**Why this priority**: Depends on User Story 1 for a source of truth. Delivers the visible half of
the ask.

**Independent Test**: With a known gateway state, load `/fa/providers` and compare the list shown
against the expected set.

**Acceptance Scenarios**:

1. **Given** one gateway is offered and the rest are withdrawn, **When** a visitor loads
   `/fa/providers`, **Then** only the offered gateway appears as a full listing.
2. **Given** an administrator withdraws a gateway, **When** a visitor reloads `/fa/providers`,
   **Then** that gateway no longer appears as an available listing without any restart or redeploy.
3. **Given** an administrator offers a gateway, **When** a visitor reloads `/fa/providers`,
   **Then** that gateway appears as available.
4. **Given** a visitor loads `/fa/providers` in Persian or English, **When** the page renders,
   **Then** the same set of gateways is shown in both languages.

### User Story 3 - Merchant Sees a Withdrawn Gateway, Not a Silent Failure (Priority: P2)

A merchant whose gateway was withdrawn needs to see that it was withdrawn by the operator, rather
than finding a gateway that silently stopped working, so they know the change is not something they
caused and whom to ask.

**Why this priority**: Pairs with the hard-gate decision. Without it a withdrawal is invisible to the
affected merchant, which turns an operator action into a support mystery.

**Independent Test**: Withdraw a gateway, load a merchant's settings, and confirm the gateway is
listed, marked as withdrawn, offers no switch to change it, and that a direct attempt to change it is
refused.

**Acceptance Scenarios**:

1. **Given** a merchant can see a gateway and an administrator withdraws it, **When** the merchant
   opens their gateway settings, **Then** the gateway is still listed, marked as withdrawn by the
   operator, with the reason shown in the merchant's language.
2. **Given** a merchant is on their gateway settings, **When** the page renders, **Then** no control
   is present that would let them change whether a gateway is available.
3. **Given** a gateway is withdrawn, **When** a non-administrator sends a direct request to change its
   state, **Then** the request is refused and the gateway stays withdrawn.
4. **Given** a gateway is withdrawn, **When** the administrator re-offers it, **Then** it becomes
   usable again with no further action from any merchant.

### User Story 4 - Withdrawing a Gateway Degrades Gracefully (Priority: P3)

An administrator needs to withdraw a gateway without breaking payments that are already in flight or
stranding the platform with nothing available, so that withdrawal is a safe operational action.

**Why this priority**: Operational safety, not the core ask. Ships after the first two stories.

**Independent Test**: With a transaction in flight on a gateway, withdraw that gateway and confirm
the in-flight transaction still completes and the platform does not end up offering zero gateways.

**Acceptance Scenarios**:

1. **Given** a gateway is withdrawn, **When** a merchant's customer is already paying through it,
   **Then** the existing payment is allowed to complete normally.
2. **Given** only one gateway is offered, **When** an administrator tries to withdraw that last one,
   **Then** the system explains that at least one gateway must remain offered and the state is
   unchanged.

### Edge Cases

- The providers page is loaded with no gateway state available (for example, the state service is
  unreachable) — the page must still render and must not silently claim gateways are available.
- Two administrators change the same gateway at the same time — the last change wins and both see
  the resulting state.
- An administrator's own account also owns a project — availability is still platform-wide, and the
  administrator's own project is subject to the same rule as every other merchant's.
- Every gateway is withdrawn through a path other than the guarded one (direct data change) — the
  page must handle an empty set of available gateways gracefully.
- A gateway is withdrawn between a visitor loading the page and clicking a listing on it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow only administrators to change whether a payment gateway is offered.
- **FR-002**: System MUST refuse gateway state changes from any non-administrator account, leaving
  the stored state unchanged.
- **FR-003**: System MUST refuse gateway state changes from unauthenticated visitors.
- **FR-004**: System MUST NOT expose the gateway management surface to non-administrators.
- **FR-005**: System MUST persist gateway offered/withdrawn state so it survives restarts and reloads.
- **FR-006**: System MUST show on the public providers page exactly the gateways currently offered.
- **FR-007**: The providers page MUST update to reflect a gateway state change without a restart,
  redeploy, or manual cache clearing by the operator.
- **FR-008**: System MUST show the same set of offered gateways in every supported language.
- **FR-009**: System MUST allow a gateway that is withdrawn to be offered again, and vice versa.
- **FR-010**: System MUST keep at least one gateway offered at all times.
- **FR-011**: System MUST allow transactions already in progress on a gateway to complete after that
  gateway is withdrawn.
- **FR-012**: System MUST tell the administrator which gateway they changed and what the resulting
  state is, in the language they are using.
- **FR-013**: System MUST remove withdrawn gateways from the providers page entirely, rather than
  listing them as unavailable, so the page is a clean list of what can be used right now.
- **FR-014**: System MUST determine administrator status from an allowlist of email addresses held
  in configuration, comparing case-insensitively so a differing capitalisation cannot deny access.
- **FR-015**: System MUST treat the global gateway state as the single authority on availability: a
  withdrawn gateway is non-functional and hidden for every merchant, with no per-project setting that
  could re-enable it.
- **FR-016**: System MUST keep a gateway that is withdrawn visible in the affected merchant's own
  settings, marked as withdrawn by the operator with an explanation in the merchant's language.
- **FR-017**: System MUST NOT offer merchants any control that changes whether a gateway is available,
  and MUST refuse such an attempt from any caller who is not an administrator.
- **FR-018**: System MUST leave every other aspect of a merchant's gateway configuration, such as
  stored credentials, untouched when an administrator changes availability.
- **FR-019**: System MUST NOT retain any record of which administrator changed a gateway's
  availability, or when. Only the current state of each gateway is retained.
- **FR-020**: System MUST store gateway availability by reusing the existing per-gateway enabled
  state, with the administrator's change applied to the default project, rather than introducing a
  second stored state for the same fact.
- **FR-021**: System MUST treat the availability gate as a property of the default project, so a
  gateway is offered to every merchant exactly when the default project has that gateway enabled.
- **FR-022**: System MUST read live gateway state on every providers page request and MUST NOT
  serve that page from a cache, so no operator or deployment action is needed to publish a change.
- **FR-023**: System MUST still render the providers page when gateway state cannot be read, showing
  no gateways as available rather than presenting unverified gateways as offered.
- **FR-024**: System MUST remove the per-project limit on how many gateways a project may have
  available, because administrators alone control availability and the limit can no longer be
  reached or exceeded by any action a merchant can take.

### Key Entities

- **Gateway**: a supported payment provider, with a stable identifier, a display name in each
  supported language, technical reference details, and a state of either offered or withdrawn. The
  state is the existing per-gateway enabled value on the default project, not a new attribute.
- **Administrator**: an account whose email address appears in the configured allowlist. No
  administrator flag is stored on the account itself.
- **Administrator allowlist**: the configured set of email addresses permitted to change gateway
  state. Changing it requires a configuration update and restart of the service.
- **Default project**: the single project whose gateway state defines platform-wide availability.
  A gateway is offered to everyone when the default project has it enabled, and withdrawn when it
  does not.
- **Provider listing**: the public-facing presentation of a gateway on the providers page, shown
  only while the gateway is offered.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of gateway state change attempts from non-administrator accounts are refused,
  verified by automated tests covering signed-in non-administrators and anonymous visitors.
- **SC-002**: An administrator's change is reflected on the public providers page on the very next
  page load after the save completes, with no restart, redeploy, or cache-clearing step.
- **SC-003**: A merchant can reach a checkout for an offered gateway without encountering a
  withdrawn gateway, in 100% of attempts.
- **SC-004**: The providers page shows an identical set of offered gateways across all supported
  languages, in 100% of checks.
- **SC-005**: Zero payments in progress are lost when a gateway is withdrawn.
- **SC-006**: An administrator can find and change a gateway's state in under 30 seconds from
  opening the management surface.

## Assumptions

- Gateway state is global to the platform, expressed as the enabled state of the same gateway on the
  default project. A withdrawn gateway is withdrawn for everyone, with no per-merchant or per-tier
  override. Planning must confirm a single unambiguous default project exists before relying on this,
  since the guarantee is only as strong as that project is.
- The global state is the only authority on availability. This supersedes the per-project toggle
  shipped by 005-admin-ipg-toggle, which merchants can no longer reach; the per-project enabled value
  survives only as the storage location for the global state, not as a merchant-facing control.
- Plan limits on how many gateways a single project may activate are withdrawn from behaviour, since
  no merchant action can add or remove a gateway any more. Any existing limit data is retained but
  unenforced.
- The descriptive content on the providers page (specifications, reference document links) is
  authored content that is retained while a gateway is offered, so nothing is lost by removing a
  withdrawn gateway from the page.
- Supported languages are Persian and English, matching the existing locale set.
- Administrators are already able to sign in to the product; this feature adds a privilege to
  existing accounts rather than a new sign-in flow.
- The administrator allowlist is operational configuration, not user data. Adding or removing an
  administrator requires a configuration update and a service restart; that operational cost is
  accepted deliberately, in exchange for not adding a privilege column to the account record.
