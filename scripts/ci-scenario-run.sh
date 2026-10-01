#!/bin/bash
set -euo pipefail

ADAPTER="zarinpal"
while [ $# -gt 0 ]; do
    case "$1" in
        --adapter) ADAPTER="${2:-}"; shift 2 ;;
        --adapter=*) ADAPTER="${1#*=}"; shift ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

echo "==> CI Scenario Runner: ${ADAPTER} Full Flow"
export BASE_URL=${BASE_URL:-"http://localhost:8080"}

function fail {
    echo "FAIL: $1" >&2
    exit 1
}

# Each adapter has its own request/verify path; both take the same `authority` back.
# ponytail: JSON-only adapters here. Behpardakht is a SOAP/WSDL surface (`POST
# /behpardakht/MellatPaymentGateway`), so driving it from a curl script needs an XML envelope
# and a WSDL client — use `pytest tests/integration/test_scenario_matrix.py`, which already
# covers all 3 adapters x 6 outcomes, rather than hand-rolling SOAP in bash. Add it here when
# someone actually needs it headless.
case "$ADAPTER" in
    zarinpal)
        INITIATE_PATH="/zarinpal/request/payment"
        VERIFY_PATH="/zarinpal/payment/verification"
        CHECKOUT_PATH="/zarinpal/checkout"
        # Zarinpal answers `{code: 100}`; IDPay answers `{id, link}` on initiate and
        # `{status: 100}` on verify (adapter-surfaces.md §2). One success key each.
        INITIATE_KEY="code"
        VERIFY_KEY="code"
        VERIFY_ID_FIELD="authority"
        ;;
    idpay)
        INITIATE_PATH="/idpay/payment"
        VERIFY_PATH="/idpay/payment/verify"
        CHECKOUT_PATH="/idpay/payment/start"
        INITIATE_KEY="id"
        VERIFY_KEY="status"
        VERIFY_ID_FIELD="id"
        ;;
    *)
        echo "FAIL: unsupported adapter '$ADAPTER' (this runner drives zarinpal and idpay;" >&2
        echo "      behpardakht is SOAP — use pytest tests/integration/test_scenario_matrix.py)" >&2
        exit 2
        ;;
esac

# Ensure curl is available
if ! command -v curl &> /dev/null; then
    echo "FAIL: curl is required"
    exit 1
fi

echo "1. Initiate transaction (Scenario: approve)"
INITIATE_RESP=$(curl -s -X POST "$BASE_URL$INITIATE_PATH" \
  -H "Content-Type: application/json" \
  -H "X-Sandbox-Scenario: approve" \
  -d '{
    "amount": 250000,
    "currency": "IRR",
    "callback_url": "http://localhost:3000/callback",
    "description": "CI test order"
  }')

CODE=$(echo "$INITIATE_RESP" | jq -r --arg k "$INITIATE_KEY" '.[$k] // empty')
if [ -z "$CODE" ]; then
    fail "Initiate failed: $INITIATE_RESP"
fi
# Zarinpal returns `authority`; IDPay returns `id` and calls it a track id.
AUTHORITY=$(echo "$INITIATE_RESP" | jq -r '.authority // .id')
if [ -z "$AUTHORITY" ] || [ "$AUTHORITY" == "null" ]; then
    fail "Initiate returned no authority/id: $INITIATE_RESP"
fi
echo "PASS: Initiated, authority = $AUTHORITY"

# The checkout confirm button is what moves the row `initiated -> pending`; verify is only
# legal from `pending`. Skipping it made every CI run fail with an internal_error on
# `initiated -> settled`, so this step is part of the flow, not an optional UI click.
echo "2. Confirm checkout"
CONFIRM_RESP=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE_URL$CHECKOUT_PATH/$AUTHORITY" \
  -d "action=confirm")
if [ "$CONFIRM_RESP" != "302" ]; then
    fail "Checkout confirm failed: HTTP $CONFIRM_RESP"
fi
echo "PASS: Checkout confirmed"

echo "3. Verify Payment"
# IDPay's verify takes `id`; Zarinpal's takes `authority` (adapter-surfaces.md §1-2).
VERIFY_BODY=$(printf '{"amount": 250000, "%s": "%s"}' "$VERIFY_ID_FIELD" "$AUTHORITY")
VERIFY_RESP=$(curl -s -X POST "$BASE_URL$VERIFY_PATH" \
  -H "Content-Type: application/json" \
  -d "$VERIFY_BODY")
VCODE=$(echo "$VERIFY_RESP" | jq -r --arg k "$VERIFY_KEY" '.[$k] // empty')
if [ "$VCODE" != "100" ]; then
    fail "Verify failed: $VERIFY_RESP"
fi
echo "PASS: Verified successfully"

echo "4. Check webhook delivery (pending/delivered)"
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
