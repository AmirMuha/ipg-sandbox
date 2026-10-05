# Feature Specification: Admin IPG Toggle

**Feature Branch**: `005-admin-ipg-toggle`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "admin-dashboard for enabling and disabling the ipgs, let's say I only need to enable the zarinpal for now and disable the other ipgs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Toggle IPG Status (Priority: P1)

An administrator needs to view all available Internet Payment Gateways (IPGs) and toggle their active status (e.g., enabling Zarinpal while disabling others) so that only supported payment methods are shown to customers.

**Why this priority**: It is the core requirement to control which payment methods are active and visible in the application.

**Independent Test**: Can be fully tested by logging in as an admin, navigating to the IPG settings, toggling an IPG, and verifying the state persists upon page reload.

**Acceptance Scenarios**:

1. **Given** an administrator is on the IPG management dashboard, **When** they view the list of IPGs, **Then** they see all supported IPGs (including Zarinpal) and their current enabled/disabled status.
2. **Given** an administrator is on the IPG management dashboard, **When** they toggle Zarinpal to "Enabled" and others to "Disabled", **Then** the system saves the new configuration and displays a success notification.
3. **Given** a non-admin user attempts to access the IPG management dashboard, **When** they navigate to the URL, **Then** they are denied access and redirected.

### Edge Cases

- What happens when an administrator tries to disable the last remaining active IPG? (Should there be at least one active IPG, or is it acceptable to have zero?)
- How does the system handle an ongoing checkout process when its selected IPG is suddenly disabled by an admin?
- How does the system handle network errors while attempting to save the toggled status?

## Requirements *(mandatory)*

### Functional Requirements

*(Note: FR-001 through FR-005 are already implemented in the existing codebase and are listed here for context, but do not require new implementation tasks.)*

- **FR-001**: System MUST provide an administrative interface listing all available IPGs.
- **FR-002**: System MUST allow administrators to toggle the enabled/disabled status of each IPG individually.
- **FR-003**: System MUST persist the enabled/disabled status of IPGs across sessions.
- **FR-004**: System MUST ensure that disabled IPGs are hidden and cannot be selected by customers during the checkout flow.
- **FR-005**: System MUST restrict access to the IPG management interface and its underlying operations to users with administrative privileges.
- **FR-006**: System MUST default to only enabling Zarinpal for new projects, with all other IPGs disabled by default.

### Key Entities *(include if feature involves data)*

- **IPG Configuration**: Represents a payment gateway setting, including its unique identifier (e.g., 'zarinpal'), display name, and active status boolean.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can successfully toggle IPG statuses and receive visual confirmation of the saved state in under 2 seconds.
- **SC-002**: Disabled IPGs are immediately removed from the customer checkout flow without requiring a system restart.
- **SC-003**: 100% of unauthorized attempts to access or modify IPG settings are blocked.

## Assumptions

- IPG integrations (e.g., Zarinpal) are already implemented in the codebase and only need their active state toggled.
- There is an existing administrative dashboard structure and an established role/authentication system to restrict access.
- Changes to IPG status apply globally and immediately to all new checkout sessions.
