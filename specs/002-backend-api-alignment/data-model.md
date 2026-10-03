# Data Model: Backend API and Dashboard UI Alignment

**Feature**: `002-backend-api-alignment` | **Date**: 2026-10-03  
**Status**: Ready for Planning | **Target Store**: PostgreSQL (Engine) + SQLite (Smoke/Dev fallback)

---

## 1. Entities & Schema Enhancements

### 1.1 Transaction (Entity Enhancement)

The underlying database schema for `Transaction` is retained, but the canonical API model exposes calculated runtime attributes to eliminate client-side URL inference.

| Field | Type | Storage / Origin | Notes |
|-------|------|-------------------|-------|
| `id` | UUID | Stored (PK) | Unique transaction identifier |
| `project_id` | UUID | Stored (FK → Project) | Scoping and multi-tenant boundary |
| `adapter_id` | UUID | Stored (FK → AdapterConfig) | Associated gateway adapter |
| `amount_rial` | BigInt | Stored | Canonical monetary amount in Iranian Rials |
| `currency` | Text | Stored | Default `IRR` |
| `status` | Enum | Stored | `initiated`, `pending`, `settled`, `approved`, `refunded`, `expired`, `declined`, `failed` |
| `forced_scenario` | Enum (null) | Stored | Manually forced outcome override |
| `effective_scenario`| Enum | Stored | Resolved scenario (`forced` ?? `project.default_scenario` ?? `approve`) |
| `authority` | Text | Stored | Emulated gateway authority/ref token |
| `app_reference` | Text (null) | Stored | Caller-provided order or invoice reference |
| `description` | Text (null) | Stored | Human-readable transaction memo |
| `callback_url` | Text (null) | Stored | Target for asynchronous notifications |
| `return_url` | Text (null) | Stored | Browser redirect destination post-checkout |
| `due_at` | Timestamp (null) | Stored | Timestamp when asynchronous settlement or timeout matures |
| `raw_request` | JSONB | Stored | Raw incoming initiation payload |
| `raw_response` | JSONB | Stored | Raw gateway response payload |
| `created_at` | Timestamp | Stored | Record creation time |
| `updated_at` | Timestamp | Stored | Last modification time |
| `checkout_url` | Text | **Computed (New)** | Canonical URL to hosted gateway checkout (`/{adapter_prefix}/checkout/{authority}`) |

**Cascade Rules**: Deleting a `Transaction` row triggers a cascade deletion of all associated `WebhookDelivery` records referencing `transaction_id`.

---

### 1.2 WebhookDelivery

Maintained as the audit log for all callback attempts.

| Field | Type | Storage | Notes |
|-------|------|---------|-------|
| `id` | UUID | Stored (PK) | Delivery attempt identifier |
| `transaction_id` | UUID (null) | Stored (FK → Transaction) | Target transaction (nullable for standalone pings) |
| `target_url` | Text | Stored | Dispatched HTTP destination |
| `stage` | Text | Stored | `initiate`, `checkout`, `settle`, `refund`, or `ping` |
| `payload` | JSONB | Stored | Exact body dispatched to target |
| `attempt` | Int | Stored | Sequence number for this stage/transaction |
| `result` | Enum | Stored | `delivered`, `failed`, `pending` |
| `response_status` | Int (null) | Stored | HTTP status received (e.g. 200, 500) |
| `error` | Text (null) | Stored | Exception or timeout message |
| `created_at` | Timestamp | Stored | Attempt dispatch timestamp |

---

## 2. API Data Transfer Objects (DTOs) & Contracts

### 2.1 Simulation DTOs

#### `PaymentSimulationRequest`
Input payload for initiating a manual or automatic transaction simulation from the dashboard.

```typescript
interface PaymentSimulationRequest {
  adapter: "zarinpal" | "idpay" | "behpardakht" | string; // Provider enum or adapter UUID
  amount_rial: number; // Positive integer in Iranian Rials
  forced_scenario?: ScenarioOutcome | null;
  callback_url?: string | null; // Absolute http(s) URL
  return_url?: string | null; // Absolute http(s) URL
  description?: string | null;
  app_reference?: string | null;
  auto_complete?: boolean; // Default: false. If true, immediately advances through verify.
}
```

#### `PaymentSimulationResponse`
Returned upon successful simulation initiation or completion.

```typescript
interface PaymentSimulationResponse {
  transaction: Transaction; // Full transaction body including checkout_url
  checkout_url: string; // Absolute or host-relative hosted checkout URL
  execution_mode: "interactive" | "auto_completed";
  callback_dispatched: boolean; // True if a webhook delivery was scheduled/executed
}
```

---

### 2.2 Analytics & Lifecycle Funnel DTOs

#### `ProjectAnalyticsOverview`
Aggregated project-wide metrics calculated across all retained records.

```typescript
interface ProjectAnalyticsOverview {
  total_volume_rial: number;
  total_transactions: number;
  success_rate_percent: number; // 0.0 - 100.0 (rounded to 1 decimal place)
  status_breakdown: {
    settled: number;
    approved: number;
    pending: number;
    initiated: number;
    declined: number;
    failed: number;
    expired: number;
    refunded: number;
  };
  scenario_distribution: {
    approve: number;
    decline: number;
    timeout: number;
    pending_settle: number;
    verify_fail: number;
    refund: number;
  };
  funnel: {
    initiated: number; // Step 1: all initiated transactions
    hosted: number; // Step 2: reached hosted checkout portal
    callback: number; // Step 3: callback dispatched or return URL triggered
    settled: number; // Step 4: successfully settled or verified
  };
  webhooks: {
    total_deliveries: number;
    delivered: number;
    failed: number;
    pending: number;
  };
  gateways: {
    configured_total: number;
    active_total: number; // Gateways with transactions in the retention window
  };
}
```

---

### 2.3 Query & Filtering DTOs

#### `TransactionQueryParams`
Query parameters supported by `GET /api/v1/transactions`.

```typescript
interface TransactionQueryParams {
  q?: string; // Free-text substring search across authority, app_reference, description
  status?: TransactionStatus;
  adapter?: "zarinpal" | "idpay" | "behpardakht";
  from_date?: string; // ISO 8601 string
  to_date?: string; // ISO 8601 string
  page?: number; // 1-based, default 1
  page_size?: number; // 1-100, default 20
}
```

#### `PaginatedResult<T>`
Standardized pagination metadata wrapper.

```typescript
interface PaginatedResult<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
```

---

### 2.4 Webhook Diagnostic DTOs

#### `WebhookPingRequest`
```typescript
interface WebhookPingRequest {
  target_url?: string | null; // Defaults to project.webhook_url if omitted
}
```

#### `WebhookPingResponse`
```typescript
interface WebhookPingResponse {
  ok: boolean;
  target_url: string;
  status_code: number | null;
  latency_ms: number;
  error: string | null;
}
```
