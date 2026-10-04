# Data Model: Comprehensive Iranian IPG Gateway Adapters Suite (Phase 1)

**Feature**: specs/003-implement-ipg-adapters | **Date**: 2026-10-03
**Source**: spec.md Key Entities + research.md; persistence = PostgreSQL (plan.md)

## 1. Enumerations

### Provider (Enum Expansion)

The database enum `provider` is expanded from 3 to 13 members to represent all documented Iranian payment gateways:

```python
class Provider(enum.StrEnum):
    # Initial MVP Providers
    zarinpal = "zarinpal"
    idpay = "idpay"
    behpardakht = "behpardakht"

    # Banking PSP Gateways (Shaparak)
    saman = "saman"                # Saman Electronic Payment (SEP)
    sadad = "sadad"                # Sadad Electronic Payment (Bank Melli)
    parsian = "parsian"            # Parsian Electronic Commerce (PEC)
    pasargad = "pasargad"          # Pasargad Electronic Payment (PEP)
    asan_pardakht = "asan_pardakht"# Asan Pardakht (AP / آپ)
    pardakht_novin = "pardakht_novin" # Pardakht Novin Arian (PNA)
    irankish = "irankish"          # IranKish
    fanava = "fanava"              # Fanava Card
    sarmayeh = "sarmayeh"          # Bank Sarmayeh

    # Modern Payment Facilitator (Pardakht-Yar)
    sizpay = "sizpay"              # SizPay
```

---

## 2. Entities & Schema Alignment

### AdapterConfig

The existing `adapter_configs` table stores project-specific settings for each gateway adapter.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID (PK) | Unique configuration identifier |
| `project_id` | UUID (FK) | Reference to owning `Project` |
| `provider` | `Provider` Enum | Target gateway provider (1 of 13) |
| `enabled` | Boolean | Whether adapter is active in this project |
| `credentials` | JSONB | Gateway credentials (terminal ID, merchant code, password, private key) |
| `api_unit` | `ApiUnit` Enum | `rial` (canonical) or `toman` (for ZarinPal) |
| `endpoint_path_prefix` | Text | Base route prefix (e.g. `/saman`, `/sadad`, `/api/payment`) |
| `created_at` | Timestamptz | Creation timestamp |
| `updated_at` | Timestamptz | Last update timestamp |

#### Credential Schemes per Provider

Each adapter class defines a `credential_scheme` tuple declaring which keys in `credentials` are inspected:

| Provider | `credential_scheme` | Description / Sample Value |
|---|---|---|
| `behpardakht` | `("terminal_id", "username", "password")` | Mellat Terminal & Portal user |
| `zarinpal` | `("merchant_id",)` | 36-character ZarinPal Merchant UUID |
| `idpay` | `("api_key",)` | Hexadecimal API Key |
| `saman` | `("terminal_id",)` | Saman Terminal ID (CellNumber / MID optional) |
| `sadad` | `("terminal_id", "merchant_id", "terminal_key")` | Melli terminal & DES/RSA Key |
| `parsian` | `("pin",)` | Parsian Merchant PIN Code |
| `pasargad` | `("merchant_code", "terminal_code")` | Optional: `private_key` (PEM) |
| `asan_pardakht` | `("merchant_id", "username", "password")` | Merchant ID & credentials |
| `pardakht_novin` | `("merchant_id", "password")` | PNA Merchant & Password |
| `irankish` | `("terminal_id", "acceptor_id", "pass_phrase")` | IranKish Terminal & Password |
| `sizpay` | `("merchant_id", "terminal_id", "username", "password")` | SizPay merchant credentials |
| `fanava` | `("merchant_id", "password")` | Fanava Merchant ID & password |
| `sarmayeh` | `("merchant_id", "terminal_id", "password")` | Sarmayeh Bank terminal credentials |

---

### Transaction

Transactions track payment lifecycles independently of gateway differences.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID (PK) | Internal transaction identifier |
| `project_id` | UUID (FK) | Scoping project ID |
| `adapter_id` | UUID (FK) | Target adapter configuration ID |
| `status` | `TransactionStatus` Enum | `initiated`, `pending`, `settled`, `declined`, `refunded`, `expired`, `failed` |
| `amount_rial` | BigInt | Canonical payment amount in Rials |
| `authority` | Text | Gateway tracking token (`Authority`, `Token`, `RefId`, `TokenPayment`) |
| `app_reference` | Text | Merchant-provided order identifier (`OrderId`, `ResNum`, `FactorId`) |
| `callback_url` | Text | Merchant return destination URL |
| `forced_scenario` | `ScenarioOutcome` | Optional per-transaction scenario override |
| `effective_scenario` | `ScenarioOutcome` | Resolved scenario (`forced` ?? `project.default` ?? `approve`) |
| `meta` | JSONB | Gateway-specific metadata (masked card PAN, RRN, trace number, bank status code) |
| `due_at` | Timestamptz | Scheduled time for delayed state transitions (e.g. pending→settle) |
| `created_at` | Timestamptz | Initiation timestamp |
| `updated_at` | Timestamptz | Last update timestamp |

---

## 3. Metadata Models

### Cardholder & Settlement Metadata (`Transaction.meta`)

To ensure authentic Shaparak responses across callbacks and verifications, the engine stores the following structured data inside `Transaction.meta`:

```json
{
  "card_pan": "603799******1234",
  "rrn": "202610031234",
  "trace_no": "041234",
  "sale_order_id": "100234",
  "sale_reference_id": "987654321012",
  "res_code": "0",
  "status_message": "Transaction Successful",
  "verified_at": "2026-10-03T10:15:30Z"
}
```

- **`card_pan`**: 16-character masked PAN using official bank BIN prefixes:
  - Melli (Sadad): `603799`
  - Mellat (Behpardakht): `610433`
  - Saman (SEP): `621986`
  - Parsian (PEC): `622106`
  - Pasargad (PEP): `502229`
  - Tejarat (IranKish): `585983`
  - Eghtesad Novin (PNA): `627412`
  - Sarmayeh: `639607`
  - Keshavarzi (Asan Pardakht): `603770`
  - Default / Payment-Yar: `502229`
- **`rrn`**: 12-digit numeric Retrieval Reference Number.
- **`trace_no`**: 6-digit numeric System Audit Trace Number.

---

## 4. State Transitions

All 13 adapters drive transactions through identical canonical state transitions, governed by `Transaction.transition_to`:

```text
               ┌─────────────┐
               │  initiated  │
               └──────┬──────┘
                      │
           ┌──────────┴──────────┐
           │ (Checkout Action)   │
           ▼                     ▼
     ┌───────────┐         ┌───────────┐
     │  pending  │         │ declined  │ (or cancelled/expired)
     └─────┬─────┘         └───────────┘
           │
     ┌─────┴─────────────────────┐
     │ (Verify / Settle Call)    │
     ▼                           ▼
┌─────────┐                 ┌─────────┐
│ settled │ (approved)      │ failed  │ (verify_fail)
└────┬────┘                 └─────────┘
     │
     │ (Refund Call)
     ▼
┌──────────┐
│ refunded │
└──────────┘
```

1. **`initiated`**: Gateway payment request received; token/authority issued; awaiting customer visit to checkout.
2. **`pending`**: Customer clicked "Confirm Payment" on checkout page; transaction authorized on bank side; awaiting merchant verification or async settlement.
3. **`settled`**: Payment verified by merchant or automatically settled by `due_at` scheduler.
4. **`declined`**: Cardholder clicked "Cancel", bank declined, or forced `decline` scenario.
5. **`refunded`**: Merchant initiated refund/reversal post-settlement.
6. **`expired`**: Customer abandoned checkout window past transaction validity duration.
