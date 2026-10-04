# Contract: Wire-Level Adapter Surfaces (Phase 1)

**Feature**: specs/003-implement-ipg-adapters | **Date**: 2026-10-03
**Purpose**: Formal wire protocol specification for all 13 emulated payment gateway surfaces. Client payment SDKs and applications swap their production bank URLs to these endpoints without modifying client code.

---

## Global Rules

1. **Protocol Adherence**: Gateways expecting SOAP/XML receive native SOAP envelopes with authentic method names and XML namespaces; gateways expecting REST/JSON receive standard JSON payloads with HTTP 200/400 status codes.
2. **Unsupported Operations**: Unimplemented methods return an explicit structured error (`HTTP 400` JSON `{"code": "unsupported_operation"}` or SOAP Fault `<faultcode>sandbox:UnsupportedOperation</faultcode>`).
3. **Canonical Rial Storage**: Amounts in requests are accepted in the gateway's expected unit (Rials for banking PSPs, Rials or Tomans for ZarinPal) and normalized to Rials in internal records.
4. **Scenario Overrides**: Scenarios resolve per transaction (`forced_scenario` ?? `project.default_scenario` ?? `approve`).
5. **Permissive Signatures**: Missing RSA/HMAC signatures are accepted without error; configured keypairs trigger strict cryptographic validation.

---

## 1. Top-Tier Banking PSPs (Shaparak)

### 1.1 Saman Electronic Payment (SEP / سامان کیش)
- **Base Prefix**: `/saman`
- **WSDL URL**: `/saman/verifyTxn?wsdl` (or `/saman/service?wsdl`)

| Stage | Method & Path | Payload / Headers | Wire Behavior & Response |
|---|---|---|---|
| **Initiate (Token)** | `POST /saman/onlinepg/onlinepg` | JSON or Form: `Action="token"`, `Amount`, `Wage`, `ResNum`, `RedirectUrl`, `CellNumber`, `TerminalId` | Returns JSON: `{"status": 1, "token": "<token_uuid>", "errorCode": 0}` |
| **Checkout Portal** | `GET /saman/checkout/{token}` or `POST /saman/onlinepg/payment` with `Token` | Browser navigation | Renders Saman-branded checkout screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST containing: `State="OK"`, `Status=0`, `RefNum`, `ResNum`, `MID`, `TraceNo`, `Rrn`, `SecurePan` |
| **Verify** | `POST /saman/verifyTxn` | SOAP XML `verifyTransaction` or REST JSON `{"RefNum": "...", "TerminalNumber": "..."}` | Returns status code `0` (Success) or positive amount, or negative integer error (e.g. `-1` failed, `-6` already verified) |
| **Reverse** | `POST /saman/reverseTxn` | SOAP XML `reverseTransaction` | Status code `0` on success |

---

### 1.2 Sadad Bank Melli (سداد بانک ملی)
- **Base Prefix**: `/sadad`
- **WSDL URL**: `/sadad/services?wsdl`

| Stage | Method & Path | Payload / Headers | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /sadad/api/v0/Request/PaymentRequest` | JSON: `TerminalId`, `MerchantId`, `Amount`, `SignData`, `ReturnUrl`, `LocalDateTime`, `OrderId` | Returns JSON: `{"ResCode": 0, "Token": "<sadad_token>", "Description": "Success"}` |
| **Checkout Portal** | `GET /sadad/checkout/{token}` or `POST /sadad/Purchase` with `Token` | Browser navigation | Renders Sadad/Melli-branded payment portal |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST with `ResCode=0`, `OrderId`, `Token`, `RetrivalReferenceNumber`, `SystemTraceNo` |
| **Verify** | `POST /sadad/api/v0/Advice/Verify` | JSON: `{"Token": "...", "SignData": "..."}` | Returns JSON: `{"ResCode": 0, "Amount": <amount>, "Description": "Success", "RetrivalReferenceNumber": "...", "SystemTraceNo": "..."}` |

---

### 1.3 Parsian Electronic Commerce (PEC / تجارت الکترونیک پارسیان)
- **Base Prefix**: `/parsian`
- **WSDL URL**: `/parsian/EShopService.asmx?wsdl`

| Stage | Method & Path | Payload / Headers | Wire Behavior & Response |
|---|---|---|---|
| **Initiate (SOAP)** | `POST /parsian/EShopService.asmx` | SOAP Action `SalePaymentRequest`: `Pin`, `Amount`, `OrderId`, `AdditionalData`, `ReffererAddress` | Returns SOAP: `SalePaymentRequestResult`: `Status=0`, `Token="<token>"` |
| **Checkout Portal** | `GET /parsian/checkout/{token}` or `POST /parsian/payment` with `Token` | Browser navigation | Renders Parsian PEC-branded hosted checkout screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST: `Token`, `status=0`, `OrderId`, `TerminalNo`, `RRN`, `CardNumberMasked` |
| **Verify (SOAP)** | `POST /parsian/EShopService.asmx` | SOAP Action `ConfirmPayment`: `Pin`, `Token` | Returns SOAP: `ConfirmPaymentResult`: `Status=0`, `RRN`, `CardNumberMasked` |
| **Reversal (SOAP)**| `POST /parsian/EShopService.asmx` | SOAP Action `ReversalProcess`: `Pin`, `Token` | Returns SOAP: `ReversalProcessResult`: `Status=0` |

---

### 1.4 Pasargad Electronic Payment (PEP / پرداخت الکترونیک پاسارگاد)
- **Base Prefix**: `/pasargad`

| Stage | Method & Path | Payload / Headers | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /pasargad/api/payment/purchase` | JSON: `invoiceNumber`, `invoiceDate`, `amount`, `terminalCode`, `merchantCode`, `redirectAddress`, `timestamp` | Returns JSON: `{"resultCode": 0, "result": "Success", "token": "<token_id>", "url": "..."}` |
| **Checkout Portal** | `GET /pasargad/checkout/{token}` or redirect URL | Browser navigation | Renders Pasargad PEP-branded checkout screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST: `invoiceNumber`, `invoiceDate`, `transactionId`, `referenceNumber`, `trackId`, `status=0` |
| **Verify** | `POST /pasargad/api/payment/verify` | JSON: `invoiceNumber`, `invoiceDate`, `amount`, `terminalCode`, `merchantCode`, `timeStamp` | Returns JSON: `{"resultCode": 0, "result": "Success", "amount": <amount>, "referenceNumber": "..."}` |

---

### 1.5 Asan Pardakht (AP / آسان پرداخت - آپ)
- **Base Prefix**: `/asan_pardakht`
- **WSDL URL**: `/asan_pardakht/services?wsdl`

| Stage | Method & Path | Payload / Headers | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /asan_pardakht/Token` | JSON / SOAP: `merchantConfigurationId`, `serviceTypeId`, `localDate`, `localTime`, `additionalData`, `callBackUrl`, `amountInRials` | Returns JSON: `{"status": "Success", "token": "<ap_token>"}` |
| **Checkout Portal** | `GET /asan_pardakht/checkout/{token}` or Form POST | Browser navigation | Renders Asan Pardakht-branded checkout screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST: `CardNumber`, `RRN`, `TraceNumber`, `PayResult=0`, `Amount`, `InvoiceNumber` |
| **Verify** | `POST /asan_pardakht/Verify` | JSON / SOAP: `token`, `merchantConfigurationId` | Returns JSON: `{"status": "Success", "amount": <amount>, "rrn": "..."}` |

---

## 2. Specialized & Institutional Banking PSPs

### 2.1 Behpardakht Mellat (به‌پرداخت ملت)
- **Base Prefix**: `/behpardakht`
- **WSDL URL**: `/behpardakht/MellatPaymentGateway?wsdl`

| Stage | Method & Path | Payload / Headers | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /behpardakht/MellatPaymentGateway` | SOAP XML `bpPaymentRequest` (terminal, user, pass, orderId, amount, localDate, localTime, callbackUrl) | Returns SOAP: `bpPaymentRequestResponse`: `ResCode="0"`, `RefId="<numeric_ref_id>"` |
| **Checkout Portal** | `GET /behpardakht/checkout/{refId}` | Browser navigation | Renders Behpardakht Mellat checkout screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST: `ResCode=0`, `RefId`, `SaleOrderId`, `SaleReferenceId`, `CardHolderPan` |
| **Verify / Settle** | `POST /behpardakht/MellatPaymentGateway` | SOAP XML `bpVerifyRequest` & `bpSettleRequest` | Returns SOAP: `0` (Success) or bank error codes (`41`, `42`, `43`, `45`) |
| **Reversal** | `POST /behpardakht/MellatPaymentGateway` | SOAP XML `bpReversalRequest` | Returns SOAP: `0` on reversal success |

---

### 2.2 Pardakht Novin Arian (PNA / پرداخت نوین)
- **Base Prefix**: `/pardakht_novin`
- **WSDL URL**: `/pardakht_novin/services?wsdl`

| Stage | Method & Path | Payload | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /pardakht_novin/GenerateToken` | JSON / SOAP: `WSContext`, `TransType`, `Amount`, `OrderId`, `CallbackUrl` | Returns: `Status="0"`, `Token="<token>"` |
| **Checkout** | `GET /pardakht_novin/checkout/{token}` | Browser navigation | Renders Pardakht Novin payment screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST: `RefNum`, `ResNum`, `State="OK"`, `TraceNo`, `RRN` |
| **Verify** | `POST /pardakht_novin/Verify` | JSON / SOAP: `WSContext`, `Token`, `RefNum` | Returns: `Result="0"`, `Amount=<amount>` |

---

### 2.3 IranKish (ایران‌کیش)
- **Base Prefix**: `/irankish`

| Stage | Method & Path | Payload | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /irankish/api/v1/token` | JSON: `terminalId`, `acceptorId`, `amount`, `revertURL`, `requestUniqueId` | Returns JSON: `{"status": true, "resultCode": "00", "token": "<token>"}` |
| **Checkout** | `GET /irankish/checkout/{token}` | Browser navigation | Renders IranKish payment screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST: `token`, `resultCode="00"`, `referenceId`, `retrievalReferenceNumber`, `maskedPan` |
| **Verify** | `POST /irankish/api/v1/verify` | JSON: `terminalId`, `token`, `retrievalReferenceNumber` | Returns JSON: `{"status": true, "resultCode": "00", "amount": <amount>}` |

---

### 2.4 Fanava Card (فن‌آوا کارت) & 2.5 Bank Sarmayeh (بانک سرمایه)
- **Base Prefixes**: `/fanava`, `/sarmayeh`
- **WSDL URLs**: `/fanava/services?wsdl`, `/sarmayeh/services?wsdl`

| Stage | Method & Path | Payload | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST {prefix}/payment` | SOAP / Form: Merchant ID, Amount, OrderId, ReturnUrl | Returns: `Status=0`, `Token/RefId` |
| **Checkout** | `GET {prefix}/checkout/{token}` | Browser navigation | Renders institutional bank checkout page |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST with reference numbers and status |
| **Verify** | `POST {prefix}/verify` | SOAP / REST verification | Returns approval confirmation and settled amount |

---

## 3. Payment Facilitators (پرداخت‌یار)

### 3.1 ZarinPal (زرین‌پال)
- **Base Prefix**: `/zarinpal`

| Stage | Method & Path | Payload | Wire Behavior & Response |
|---|---|---|---|
| **Initiate (v4)** | `POST /zarinpal/pg/v4/payment/request.json` | JSON: `merchant_id`, `amount`, `currency`, `description`, `callback_url` | Returns JSON: `{"data": {"code": 100, "message": "Success", "authority": "S00000000000000000000000000000000001", "fee_type": "Merchant"}, "errors": []}` |
| **Checkout** | `GET /zarinpal/pg/StartPay/{authority}` | Browser navigation | Renders ZarinPal hosted screen |
| **Callback** | `GET {merchant_callback_url}?Authority={authority}&Status=OK` | HTTP 302 Redirect | Query string callback to merchant |
| **Verify (v4)** | `POST /zarinpal/pg/v4/payment/verify.json` | JSON: `merchant_id`, `amount`, `authority` | Returns JSON: `{"data": {"code": 100, "message": "Verified", "card_pan": "603799******1234", "ref_id": 12345678}, "errors": []}` |

---

### 3.2 IDPay (آیدی‌پی)
- **Base Prefix**: `/idpay`

| Stage | Method & Path | Payload / Headers | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /idpay/v1.1/payment` | Header: `X-API-KEY`. JSON: `order_id`, `amount`, `callback` | Returns JSON: `{"id": "<32_hex_id>", "link": "http://localhost:8080/idpay/v1.1/payment/start/<id>"}` |
| **Checkout** | `GET /idpay/v1.1/payment/start/{id}` | Browser navigation | Renders IDPay hosted checkout screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded or JSON | Post containing `status=100`, `track_id`, `id`, `order_id`, `amount`, `card_no` |
| **Verify** | `POST /idpay/v1.1/payment/verify` | Header: `X-API-KEY`. JSON: `id`, `order_id` | Returns JSON: `{"status": 100, "track_id": "...", "id": "...", "order_id": "...", "amount": <amount>}` |

---

### 3.3 SizPay (سیزپی)
- **Base Prefix**: `/sizpay`

| Stage | Method & Path | Payload | Wire Behavior & Response |
|---|---|---|---|
| **Initiate** | `POST /sizpay/api/Payment/Token` | JSON: `MerchantID`, `TerminalID`, `UserName`, `Password`, `Amount`, `InvoiceNo`, `ReturnURL` | Returns JSON: `{"ResCode": 0, "Message": "Success", "Token": "<sizpay_token>"}` |
| **Checkout** | `GET /sizpay/checkout/{token}` or `POST /sizpay/api/Payment/Start` | Browser navigation | Renders SizPay-branded checkout screen |
| **Callback** | `POST {merchant_callback_url}` | Form-urlencoded | Form POST: `ResCode=0`, `Token`, `InvoiceNo`, `RefNo`, `CardNoMask` |
| **Verify** | `POST /sizpay/api/Payment/Confirm` | JSON: `MerchantID`, `TerminalID`, `Token` | Returns JSON: `{"ResCode": 0, "Message": "Confirmed", "RefNo": "...", "Amount": <amount>}` |
