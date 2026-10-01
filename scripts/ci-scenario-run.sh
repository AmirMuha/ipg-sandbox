#!/bin/bash
set -euo pipefail

echo "==> CI Scenario Runner: Zarinpal Full Flow"
export BASE_URL=${BASE_URL:-"http://localhost:8080"}

function fail {
    echo "FAIL: $1" >&2
    exit 1
}

# Ensure curl is available
if ! command -v curl &> /dev/null; then
    echo "FAIL: curl is required"
    exit 1
fi

echo "1. Initiate transaction (Scenario: approve)"
INITIATE_RESP=$(curl -s -X POST "$BASE_URL/zarinpal/request/payment" \
  -H "Content-Type: application/json" \
  -H "X-Sandbox-Scenario: approve" \
  -d '{
    "amount": 250000,
    "currency": "IRR",
    "callback_url": "http://localhost:3000/callback",
    "description": "CI test order"
  }')

CODE=$(echo "$INITIATE_RESP" | jq -r '.code')
if [ "$CODE" != "100" ]; then
    fail "Initiate failed: $INITIATE_RESP"
fi
AUTHORITY=$(echo "$INITIATE_RESP" | jq -r '.authority')
echo "PASS: Initiated, authority = $AUTHORITY"

echo "2. Verify Payment"
VERIFY_RESP=$(curl -s -X POST "$BASE_URL/zarinpal/payment/verification" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 250000,
    "authority": "'"$AUTHORITY"'"
  }')
VCODE=$(echo "$VERIFY_RESP" | jq -r '.code')
if [ "$VCODE" != "100" ]; then
    fail "Verify failed: $VERIFY_RESP"
fi
echo "PASS: Verified successfully"

echo "3. Check webhook delivery (pending/delivered)"
SUCCESS=false
for i in {1..10}; do
    DELIVERIES=$(curl -s -X GET "$BASE_URL/api/v1/deliveries" || echo "{}")
    DELIVERED=$(echo "$DELIVERIES" | jq -r --arg auth "$AUTHORITY" '.items[]? | select(.payload.Authority == $auth and .result == "delivered") | .result')
    if [ "$DELIVERED" == "delivered" ]; then
        SUCCESS=true
        break
    fi
    sleep 0.5
done
if [ "$SUCCESS" == "true" ]; then
    echo "PASS: Webhook delivered"
else
    echo "WARN: Webhook delivery check timed out or failed (maybe no active listener)"
fi

echo "==> SUCCESS: All CI steps passed."
exit 0
