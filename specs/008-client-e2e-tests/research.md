# Research: Client End-to-End Payment Testing

## Test Execution Architecture
- **Decision**: Drive tests via Playwright in `apps/web/tests/e2e/client-payments.spec.ts`, orchestrating Next.js and FastAPI through an isolated bash launcher (`apps/web/tests/run_e2e.sh`).
- **Rationale**: Playwright is already installed in `apps/web` (`@playwright/test` v1.63.0). Using Playwright allows real browser DOM interaction, cookie handling, navigation, and modal flows that pure HTTP smoke tests cannot replicate.
- **Alternatives considered**: Cypress (requires new installation), pure Node `fetch` tests (already present in `smoke.test.mjs`, lacks client UI validation, DOM interactions, and form states).

## Webhook Verification Strategy
- **Decision**: Spawn a lightweight Node.js HTTP server (`apps/web/tests/e2e/callback-server.mjs`) on `127.0.0.1:3099` during the test run, recording all received payloads into an in-memory queue queryable via `GET /__received`.
- **Rationale**: Webhook verification requires receiving asynchronous POST requests from the engine. Using `node:http` requires zero extra dependencies, runs instantly on localhost, and allows the test to assert against real wire payloads sent by the sandbox dispatcher.
- **Alternatives considered**: Mocking the webhook dispatcher (rejected: violates FR-001/FR-006 by testing mocks rather than end-to-end delivery); polling third-party request bins (rejected: violates FR-011 requiring zero external network services).

## Multi-User & Test Isolation
- **Decision**: Generate a random unique merchant email per test execution (`e2e-${timestamp}-${random}@example.com`) and start the engine with a dedicated temporary SQLite database (`/tmp/ipg_e2e_*.db`).
- **Rationale**: Guarantees zero state pollution between consecutive test runs or with local developer data. Ensures testing default project initialization and clean state.
- **Alternatives considered**: Shared persistent test database with truncate queries (rejected: requires database cleanup scripts and risks race conditions).

## Authentication in Automated Browser Tests
- **Decision**: Register the test merchant via `POST /api/v1/auth/register`, then perform UI login via `apps/web/src/app/[locale]/(marketing)/login`.
- **Rationale**: Full browser registration requires email OTP verification via SMTP, which is not running in offline test environments. Registering via API seeds the user and workspace, while signing in via browser UI exercises the full authentication flow, form validation, error states, and session cookie attachment.
- **Alternatives considered**: Mocking the session cookie directly in the browser context (rejected: skips verifying the login form interaction and error banner handling).
