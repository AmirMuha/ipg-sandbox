#!/bin/bash
# Run the client-journey E2E suite against a throwaway local stack.
#
# Starts the engine (SQLite, temp file) and the dashboard, plus the suite's own
# callback endpoint, then hands over to Playwright. Every process and the temp
# database are torn down on exit, so a run leaves nothing behind.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$DIR/../.." && pwd)"

ENGINE_PORT="${E2E_ENGINE_PORT:-8088}"
DASH_PORT="${E2E_DASH_PORT:-3088}"
CALLBACK_PORT="${E2E_CALLBACK_PORT:-3099}"
TMP_DB="$(mktemp -u /tmp/ipg_e2e_XXXXXX.db)"

ENGINE_PID=""
DASH_PID=""
CALLBACK_PID=""

cleanup() {
  for pid in "$ENGINE_PID" "$DASH_PID" "$CALLBACK_PID"; do
    [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  done
  rm -f "$TMP_DB"
}
trap cleanup EXIT

wait_for() {
  # wait_for <url> <attempts> <sleep-seconds>
  local url="$1" attempts="$2" delay="$3"
  for _ in $(seq 1 "$attempts"); do
    if curl -sf "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

echo "==> Preparing the database schema at $TMP_DB"
"$REPO_ROOT/apps/engine/.venv/bin/python" -c "
import sys
sys.path.insert(0, '$REPO_ROOT/apps/engine')
from tests.conftest import Base
from sqlalchemy import create_engine
engine = create_engine('sqlite:///$TMP_DB')
Base.metadata.create_all(engine)
engine.dispose()
"

echo "==> Starting the engine on port $ENGINE_PORT"
DATABASE_URL="sqlite+aiosqlite:///$TMP_DB" \
ENGINE_PORT="$ENGINE_PORT" \
DASHBOARD_PORT="$DASH_PORT" \
ENGINE_PROFILE=local \
  "$REPO_ROOT/apps/engine/.venv/bin/uvicorn" src.api.app:app \
  --app-dir "$REPO_ROOT/apps/engine" --port "$ENGINE_PORT" >/tmp/ipg_e2e_engine.log 2>&1 &
ENGINE_PID=$!

if ! wait_for "http://localhost:$ENGINE_PORT/api/v1/project" 50 0.2; then
  echo "Engine failed to start. Log:"
  cat /tmp/ipg_e2e_engine.log
  exit 1
fi
echo "    engine is up"

echo "==> Starting the callback endpoint on port $CALLBACK_PORT"
E2E_CALLBACK_PORT="$CALLBACK_PORT" node "$DIR/tests/e2e/callback-server.mjs" \
  >/tmp/ipg_e2e_callback.log 2>&1 &
CALLBACK_PID=$!

if ! wait_for "http://127.0.0.1:$CALLBACK_PORT/__received" 50 0.2; then
  echo "Callback endpoint failed to start. Log:"
  cat /tmp/ipg_e2e_callback.log
  exit 1
fi
echo "    callback endpoint is up"

echo "==> Building the dashboard"
NEXT_PUBLIC_API_URL="http://localhost:$ENGINE_PORT" \
  "$DIR/node_modules/.bin/next" build "$DIR" >/tmp/ipg_e2e_next_build.log 2>&1 || {
    echo "Dashboard build failed. Log:"
    cat /tmp/ipg_e2e_next_build.log
    exit 1
  }

echo "==> Starting the dashboard on port $DASH_PORT"
NEXT_PUBLIC_API_URL="http://localhost:$ENGINE_PORT" \
ENGINE_URL="http://localhost:$ENGINE_PORT" \
  "$DIR/node_modules/.bin/next" start "$DIR" -p "$DASH_PORT" >/tmp/ipg_e2e_dash.log 2>&1 &
DASH_PID=$!

if ! wait_for "http://localhost:$DASH_PORT/en/home" 100 0.3; then
  echo "Dashboard failed to start. Log:"
  cat /tmp/ipg_e2e_dash.log
  exit 1
fi
echo "    dashboard is up"

echo "==> Running the client-journey E2E suite"
DASHBOARD_URL="http://localhost:$DASH_PORT" \
ENGINE_URL="http://localhost:$ENGINE_PORT" \
E2E_CALLBACK_PORT="$CALLBACK_PORT" \
  "$DIR/node_modules/.bin/playwright" test --config "$DIR/playwright.config.ts" "$@"

echo "==> E2E suite passed"
