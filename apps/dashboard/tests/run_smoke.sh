#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$DIR/../.." && pwd)"

ENGINE_PORT=8088
DASH_PORT=3088
TMP_DB="/tmp/test_dashboard_$$.db"

# Cleanup on exit
cleanup() {
  if [ -n "$ENGINE_PID" ]; then kill "$ENGINE_PID" 2>/dev/null || true; fi
  if [ -n "$DASH_PID" ]; then kill "$DASH_PID" 2>/dev/null || true; fi
  rm -f "$TMP_DB"
}
trap cleanup EXIT

echo "Initializing database schema..."
"$REPO_ROOT/apps/engine/.venv/bin/python" -c "
import sys
sys.path.insert(0, '$REPO_ROOT/apps/engine')
from tests.conftest import Base
from sqlalchemy import create_engine
engine = create_engine('sqlite:///$TMP_DB')
Base.metadata.create_all(engine)
"

echo "Starting engine on port $ENGINE_PORT..."
DATABASE_URL="sqlite+aiosqlite:///$TMP_DB" "$REPO_ROOT/apps/engine/.venv/bin/uvicorn" src.api.app:app --app-dir "$REPO_ROOT/apps/engine" --port $ENGINE_PORT &
ENGINE_PID=$!

# Wait for engine up to 10s
for i in {1..50}; do
  if curl -sf "http://localhost:$ENGINE_PORT/api/v1/project" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

if ! curl -sf "http://localhost:$ENGINE_PORT/api/v1/project" >/dev/null 2>&1; then
  echo "Engine failed to start"
  exit 1
fi
echo "Engine ready."

echo "Starting dashboard on port $DASH_PORT..."
NEXT_PUBLIC_API_URL="http://localhost:$ENGINE_PORT" "$DIR/node_modules/.bin/next" start "$DIR" -p $DASH_PORT &
DASH_PID=$!

# Wait for dashboard up to 15s
for i in {1..75}; do
  if curl -sf "http://localhost:$DASH_PORT/fa/transactions" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

if ! curl -sf "http://localhost:$DASH_PORT/fa/transactions" >/dev/null 2>&1; then
  echo "Dashboard failed to start"
  exit 1
fi
echo "Dashboard ready."

echo "Running smoke tests..."
DASHBOARD_URL="http://localhost:$DASH_PORT" ENGINE_URL="http://localhost:$ENGINE_PORT" node --test "$DIR/tests/smoke.test.mjs"

echo "Smoke tests passed!"
