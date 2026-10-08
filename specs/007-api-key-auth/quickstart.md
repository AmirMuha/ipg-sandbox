# Quickstart & Validation: API Key Authentication

## Prerequisites
- The backend engine is running locally (`pnpm --filter ipg-sandbox-engine dev`)
- The web frontend is running locally (`pnpm --filter ipg-sandbox-web dev`)
- You are logged in to the sandbox UI.

## Validation Scenarios

### Scenario 1: Generate a new API Key
1. Navigate to the Settings -> API Keys section in the web UI.
2. Click "Create New Key".
3. Enter the name "Test Key" and submit.
4. Verify that a modal appears showing the full token (e.g., `ipg_key_...`).
5. Copy the token.
6. Close the modal and refresh the page.
7. Verify that the list shows "Test Key" with the last 4 characters matching what you copied, and the full token is no longer visible.

### Scenario 2: Authenticate a Request
1. Use `curl` or Postman to make a request to a protected endpoint, using the key from Scenario 1:
   ```bash
   curl -X GET http://localhost:8080/api/v1/user/me \
     -H "Authorization: Bearer ipg_key_YOUR_COPIED_TOKEN"
   ```
2. Verify the response is `200 OK` and returns your user details.
3. Modify the token slightly (e.g., change the last character) and send the request again.
4. Verify the response is `401 Unauthorized`.

### Scenario 3: Revoke an API Key
1. In the web UI, find "Test Key" and click "Revoke" (or delete).
2. Confirm the revocation.
3. Repeat the `curl` request from Scenario 2 with the exact same valid token.
4. Verify the response is now `401 Unauthorized`.
