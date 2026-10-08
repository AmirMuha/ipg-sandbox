# Feature Specification: API Key Authentication

**Feature Branch**: `[007-api-key-auth]`

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "allow the users to create api-keys as a method of authentication when they need to use the cloud hosted version of the sandbox"

## Clarifications

### Session 2026-10-08
- Q: Should the API keys have a distinct prefix (e.g., `ipg_key_...`) to enable secret scanning? → A: Option A - Use a standard prefix like `ipg_key_...`
- Q: To secure the API keys in the database, should we store only a one-way hash alongside the last 4 characters in plaintext for UI identification? → A: Option A - Store a one-way hash plus the last 4 characters in plaintext
- Q: Should we enforce a maximum lifetime for API keys (e.g., 30, 60, or 90 days), or allow non-expiring keys for this MVP? → A: Option A - Allow non-expiring keys

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create API Key (Priority: P1)

As a user of the cloud-hosted sandbox, I want to create an API key so that I can authenticate my programmatic requests or CLI tools.

**Why this priority**: Without the ability to create keys, programmatic access to the cloud sandbox is impossible. This is the core functionality.

**Independent Test**: Can be fully tested by creating a key via the UI and receiving the token string.

**Acceptance Scenarios**:

1. **Given** I am a logged-in user, **When** I request to create a new API key and provide a descriptive name, **Then** an API key is generated with the `ipg_key_` prefix and the secret token is displayed to me exactly once.
2. **Given** I just created an API key, **When** I close the creation dialog or refresh the page, **Then** I cannot view the secret token again.

---

### User Story 2 - Authenticate via API Key (Priority: P1)

As a user, I want to use my generated API key to authenticate requests to the cloud-hosted sandbox API.

**Why this priority**: The key is useless if it cannot be used for authentication. This completes the core loop.

**Independent Test**: Can be fully tested by sending an API request with the key and verifying it succeeds.

**Acceptance Scenarios**:

1. **Given** I have a valid API key, **When** I include it in the authorization header of a sandbox API request, **Then** my request is authenticated as my user account and processed successfully.
2. **Given** I provide an invalid or revoked API key, **When** I send a sandbox API request, **Then** the request is rejected with a 401 Unauthorized error.

---

### User Story 3 - Manage/Revoke API Keys (Priority: P2)

As a user, I want to view my active API keys and revoke them if they are compromised or no longer needed.

**Why this priority**: Security requirement. Users must be able to rotate or disable keys.

**Independent Test**: Can be fully tested by revoking a key and verifying that subsequent requests with that key are rejected.

**Acceptance Scenarios**:

1. **Given** I have created API keys, **When** I view my settings, **Then** I see a list of my active keys (showing name, creation date, last used date, and the last 4 characters of the key, but not the full secret).
2. **Given** I have an active API key, **When** I revoke it, **Then** the key is immediately invalidated and can no longer be used for authentication.

### Edge Cases

- What happens if a user tries to create an API key without providing a name? (Validation error)
- What happens if an API key is leaked? (User can revoke it via the management UI)
- How does the system handle rapid, repeated authentication attempts with an invalid key? (Should be rate-limited)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authenticated users to generate new API keys with a custom name.
- **FR-002**: System MUST display the generated API key secret to the user exactly once upon creation.
- **FR-003**: System MUST authenticate incoming API requests to the cloud sandbox that include a valid API key.
- **FR-004**: System MUST allow users to view a list of their active API keys (metadata only, not the secret).
- **FR-005**: System MUST allow users to permanently revoke/delete an existing API key.
- **FR-006**: System MUST reject API requests that use invalid, revoked, or missing API keys.
- **FR-007**: System MUST store only a one-way hash of the API key secret in the database to prevent plaintext retrieval, alongside the last 4 characters in plaintext for UI identification.
- **FR-008**: System MUST generate API key secrets with the prefix `ipg_key_` to enable automated secret scanning tools to detect leaked keys.

### Key Entities

- **API Key**: Represents a programmatic access token for a user. Key attributes include a descriptive name, the one-way hashed secret, the last 4 characters of the token in plaintext, creation timestamp, last used timestamp, and the associated user ID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully generate an API key and use it to authenticate an API request.
- **SC-002**: API requests using a valid API key are authenticated in under 50ms (authentication overhead).
- **SC-003**: Revoked API keys are invalidated instantly, with subsequent requests failing 100% of the time.

## Assumptions

- We assume API keys have full access to the user's sandbox resources (no granular scopes/permissions for MVP).
- We assume standard Bearer token or custom header (e.g., `X-API-Key`) usage for passing the key in HTTP requests.
- We assume API keys do not have a hard expiration date for this MVP (as confirmed by clarification), but rely on manual revocation by the user.
- We assume users are limited to a reasonable number of concurrent active keys (e.g., 10) to prevent abuse.
