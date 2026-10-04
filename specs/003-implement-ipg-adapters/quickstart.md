# Quickstart: Validation Guide (Phase 1)

**Feature**: specs/003-implement-ipg-adapters | **Date**: 2026-10-03
**Purpose**: Runnable end-to-end verification scenarios demonstrating compliance with `spec.md` success criteria across all 13 Iranian payment gateways.

---

## Prerequisites

- Local sandbox engine running at `http://localhost:8080`.
- Python 3.12 or `curl` available in the terminal.

---

## 1. Top-Tier Banking PSP Verification: Saman (SEP)

Test payment initiation, hosted checkout, and verification:

```bash
# 1. Request Payment Token from Saman SEP
INITIATE_RESP=$(curl -s -X POST http://localhost:8080/saman/onlinepg/onlinepg \
  -H "Content-Type: application/json" \
  -d '{
    "action": "token",
    "TerminalId": "12345678",
    "Amount": 500000,
    "ResNum": "ORDER-1001",
    "RedirectUrl": "http://localhost:3000/callback"
  }')
echo "Saman Token Response: $INITIATE_RESP"
TOKEN=$(echo "$INITIATE_RESP" | jq -r '.token')

# 2. Inspect Hosted Checkout Page
curl -s "http://localhost:8080/saman/checkout/$TOKEN" | grep -i "درگاه"

# 3. Verify Payment
VERIFY_RESP=$(curl -s -X POST http://localhost:8080/saman/verifyTxn \
  -H "Content-Type: application/json" \
  -d "{
    \"RefNum\": \"$TOKEN\",
    \"TerminalNumber\": \"12345678\"
  }")
echo "Saman Verify Response: $VERIFY_RESP"
```

**Expected Result**: Token received, checkout screen loads Saman branding, and verify response returns status code `0` (Success) with authentic settled amount and reference numbers.

---

## 2. Top-Tier Banking PSP Verification: Sadad Bank Melli

```bash
# 1. Initiate Payment Request on Sadad
SADAD_INIT=$(curl -s -X POST http://localhost:8080/sadad/api/v0/Request/PaymentRequest \
  -H "Content-Type: application/json" \
  -d '{
    "TerminalId": "12345678",
    "MerchantId": "87654321",
    "Amount": 1000000,
    "OrderId": 554433,
    "ReturnUrl": "http://localhost:3000/callback",
    "LocalDateTime": "2026-10-03T12:00:00"
  }')
echo "Sadad Token: $SADAD_INIT"
SADAD_TOKEN=$(echo "$SADAD_INIT" | jq -r '.Token')

# 2. Verify Payment
curl -s -X POST http://localhost:8080/sadad/api/v0/Advice/Verify \
  -H "Content-Type: application/json" \
  -d "{\"Token\": \"$SADAD_TOKEN\"}"
```

**Expected Result**: Status `ResCode: 0`, matching amount, 12-digit `RetrivalReferenceNumber`, and 6-digit `SystemTraceNo`.

---

## 3. SOAP WSDL Introspection Check

Validate that SOAP-based banking gateways serve compliant WSDL documents to SOAP clients (such as Zeep or PHP `SoapClient`):

```bash
# Verify Behpardakht WSDL
curl -s http://localhost:8080/behpardakht/MellatPaymentGateway?wsdl | grep -i "definitions"

# Verify Parsian EShop WSDL
curl -s http://localhost:8080/parsian/EShopService.asmx?wsdl | grep -i "definitions"

# Verify Saman WSDL
curl -s http://localhost:8080/saman/verifyTxn?wsdl | grep -i "definitions"
```

**Expected Result**: All endpoints return valid XML documents containing `<wsdl:definitions>` tags and port definitions without HTTP 404 or 500 errors.

---

## 4. Modern Payment Facilitator: SizPay

```bash
# 1. Initiate SizPay Token
SIZPAY_INIT=$(curl -s -X POST http://localhost:8080/sizpay/api/Payment/Token \
  -H "Content-Type: application/json" \
  -d '{
    "MerchantID": "M-12345",
    "TerminalID": "T-67890",
    "UserName": "test_user",
    "Password": "test_password",
    "Amount": 250000,
    "InvoiceNo": "INV-9901",
    "ReturnURL": "http://localhost:3000/callback"
  }')
echo "SizPay Init: $SIZPAY_INIT"
SIZPAY_TOKEN=$(echo "$SIZPAY_INIT" | jq -r '.Token')

# 2. Confirm Payment
curl -s -X POST http://localhost:8080/sizpay/api/Payment/Confirm \
  -H "Content-Type: application/json" \
  -d "{
    \"MerchantID\": \"M-12345\",
    \"TerminalID\": \"T-67890\",
    \"Token\": \"$SIZPAY_TOKEN\"
  }"
```

**Expected Result**: `ResCode: 0`, `Message: "Confirmed"`, matching amount in Rials.

---

## 5. Duplicate Verification Rejection (SC-006)

Verify that calling the verification endpoint a second time for an already verified payment correctly returns the gateway's native "already verified" error code without double-crediting:

```bash
# Repeat the SizPay confirm call above
curl -s -X POST http://localhost:8080/sizpay/api/Payment/Confirm \
  -H "Content-Type: application/json" \
  -d "{
    \"MerchantID\": \"M-12345\",
    \"TerminalID\": \"T-67890\",
    \"Token\": \"$SIZPAY_TOKEN\"
  }"
```

**Expected Result**: Gateway returns native duplicate verification code (e.g. `101` for ZarinPal, `-6` for SEP, or specific already-processed code) rather than approving a second time.

---

## 6. Automated Full Gateway Contract Suite

Run the complete automated pytest suite covering all 13 adapters:

```bash
pytest apps/engine/tests/contract/test_all_adapters_contracts.py -v
```

**Expected Result**: 13/13 adapter test cases pass, validating initiation, hosted checkout screen, callback generation, and verification.
