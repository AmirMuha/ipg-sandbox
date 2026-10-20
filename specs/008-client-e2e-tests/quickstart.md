# Quickstart: Running Client E2E Tests

## Prerequisites

1. Node.js 18+ and pnpm installed.
2. Python 3.12 with virtual environment in `apps/engine/.venv`.
3. Playwright browser binaries installed (`pnpm --filter ipg-sandbox-web exec playwright install chromium`).

## Execution

To run the complete client-journey E2E suite end-to-end:

```bash
# From repository root
pnpm --filter ipg-sandbox-web test:e2e
```

Or invoke the runner script directly:

```bash
bash apps/web/tests/run_e2e.sh
```

## What the Script Does

1. Initializes a fresh ephemeral SQLite database at `/tmp/ipg_e2e_XXXXXX.db`.
2. Starts the backend Engine on port `8088`.
3. Starts the local Webhook Callback server on port `3099`.
4. Builds and starts the Next.js Web Dashboard on port `3088`.
5. Executes the Playwright test suite (`apps/web/tests/e2e/client-payments.spec.ts`) headlessly.
6. Automatically terminates all background processes and cleans up temporary database files via `trap EXIT`.

## Running in Interactive / UI Mode (Debugging)

If the background services are already running manually (e.g., via `docker compose up` or local `pnpm dev`):

```bash
cd apps/web
DASHBOARD_URL="http://localhost:3000" ENGINE_URL="http://localhost:8080" pnpm test:playwright --ui
```
