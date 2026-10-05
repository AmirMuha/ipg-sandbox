# Quickstart & Validation: Admin IPG Toggle

This guide describes how to validate that the IPG toggle functionality works and that Zarinpal is the only IPG enabled by default.

## Prerequisites

- The backend engine must be running (`pnpm --filter engine dev`).
- The frontend dashboard must be running (`pnpm --filter dashboard dev`).

## Validation Scenario 1: Default State

1. Open the dashboard at `http://localhost:3000` (or your configured port).
2. Register a new user account to create a fresh project.
3. Navigate to the **Settings** page in the console (`/console/settings`).
4. **Expected Outcome**: In the "Adapter Settings" section, observe that **Zarinpal** is marked as `Enabled`, while all other IPGs (IdPay, Behpardakht, etc.) are marked as `Disabled`.

## Validation Scenario 2: Toggling an IPG

1. While on the Settings page, locate a disabled IPG (e.g., IdPay).
2. Click the toggle switch to enable it.
3. **Expected Outcome**: The UI updates to show the IPG as `Enabled`, and a success state is reflected without page reload errors.
4. Refresh the page.
5. **Expected Outcome**: The IPG remains `Enabled`, proving the state was persisted.

## Validation Scenario 3: Checkout Enforcement

1. Ensure Zarinpal is enabled and Behpardakht is disabled.
2. Initiate a checkout transaction via the API or a test client, specifically requesting the disabled IPG (`"adapter": "behpardakht"`).
3. **Expected Outcome**: The API rejects the request with a `404 Not Found` or similar validation error, preventing the use of the disabled IPG.
