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
        DELIVERY_KEY="Authority"
        ;;
    idpay)
        INITIATE_PATH="/idpay/payment"
        VERIFY_PATH="/idpay/payment/verify"
        CHECKOUT_PATH="/idpay/payment/start"
        INITIATE_KEY="id"
        VERIFY_KEY="status"
        VERIFY_ID_FIELD="id"
        DELIVERY_KEY="id"
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
# WEBHOOK_URL defaults to unset: pointing it at the dashboard would promise a delivery that
# nothing is listening for, and the old script then reported that miss as a WARN. Set it to a
# real receiver to assert delivery; leave it unset and step 4 skips honestly.
CALLBACK_ARGS=""
EXPECT_DELIVERY="0"
if [ -n "${WEBHOOK_URL:-}" ]; then
    EXPECT_DELIVERY="1"
    CALLBACK_ARGS="\"callback_url\": \"$WEBHOOK_URL\","
fi
# MERCHANT_ID / API_KEY default to the values `docker compose` seeds (app.py). Override them
# for a stack seeded with different credentials — T080 rejects a mismatch, so a stale default
# now fails loudly instead of silently creating a payment with any value.
MERCHANT_ID=${MERCHANT_ID:-sandbox-merchant}
API_KEY=${API_KEY:-sandbox-key}

INITIATE_BODY=$(printf '{
    "amount": 250000,
    "currency": "IRR",
    "merchant_id": "%s",
    %s
    "description": "CI test order"
  }' "$MERCHANT_ID" "$CALLBACK_ARGS")

INITIATE_HEADERS=(-H "Content-Type: application/json" -H "X-Sandbox-Scenario: approve")
INITIATE_HEADERS+=(-H "X-API-KEY: $API_KEY")

INITIATE_RESP=$(curl -s -X POST "$BASE_URL$INITIATE_PATH" \
  "${INITIATE_HEADERS[@]}" \
  -d "$INITIATE_BODY")

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
# T068: the payload key is per-adapter — Zarinpal sends `Authority`, IDPay sends `id`. Matching
# `Authority` unconditionally meant `--adapter idpay` could never match, and the miss was then
# downgraded to a WARN that still exited 0, so a run where delivery never happened reported
# SUCCESS. jq failures inside $( ) also do not trip `set -e`, so guard the parse explicitly.
DELIVERY_JSON="null"
DELIVERED=""
for i in {1..10}; do
    RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/deliveries" || true)
    if ! echo "$RESPONSE" | jq -e '.items' >/dev/null 2>&1; then
        echo "FAIL: deliveries endpoint returned non-JSON: ${RESPONSE:0:200}" >&2
        exit 1
    fi
    DELIVERY_JSON="$RESPONSE"
    DELIVERED=$(echo "$RESPONSE" | jq -r \
        --arg auth "$AUTHORITY" --arg key "$DELIVERY_KEY" \
        '.items[]? | select(.payload[$key] == $auth and .result == "delivered") | .result' | head -1)
    if [ "$DELIVERED" == "delivered" ]; then
        break
    fi
    sleep 0.5
done

if [ "$DELIVERED" == "delivered" ]; then
    echo "PASS: Webhook delivered"
elif [ "$EXPECT_DELIVERY" == "0" ]; then
    # No webhook target configured in this run, so there is nothing to deliver — not a failure.
    echo "SKIP: No callback_url configured, so no delivery was expected"
else
    fail "Webhook delivery not confirmed for $AUTHORITY (key: $DELIVERY_KEY). Attempts so far:"
    echo "$DELIVERY_JSON" | jq -c --arg auth "$AUTHORITY" --arg key "$DELIVERY_KEY" \
        '.items[]? | select(.payload[$key] == $auth) | {stage, result, attempt, error}' >&2
    exit 1
fi

echo "==> SUCCESS: All CI steps passed."
exit 0
