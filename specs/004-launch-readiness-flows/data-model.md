# Data Model: Launch Readiness Flows (004-launch-readiness-flows)

## Entity Relationship Overview

```text
+-------------------+       1:N       +-------------------+
|      User         | <-------------- |   UserSession     |
+-------------------+                 +-------------------+
| id (UUID)         |                 | id (UUID)         |
| email (VARCHAR)   |                 | user_id (FK)      |
| password_hash     |                 | token_hash        |
| provider (ENUM)   |                 | expires_at        |
| oauth_id (VARCHAR)|                 | created_at        |
+-------------------+                 +-------------------+
          | 1:N
          v
+-------------------+       1:1       +-------------------+
|     Project       | --------------> |    UsageMeter     |
+-------------------+                 +-------------------+
| id (UUID)         |                 | project_id (FK)   |
| user_id (FK, opt) |                 | requests_total    |
| name (VARCHAR)    |                 | requests_today    |
| tier (ENUM)       |                 | window_started_at |
| daily_cap (INT)   |                 | tx_total          |
| max_adapters (INT)|                 | history_retained  |
+-------------------+                 +-------------------+
          | 1:N                                 |
          v                                     v
+-------------------+                 +-------------------+
|   Subscription    |                 |   Transaction     |
+-------------------+                 +-------------------+
| id (UUID)         |                 | id (UUID)         |
| project_id (FK)   |                 | project_id (FK)   |
| tier (ENUM)       |                 | adapter_id (FK)   |
| status (ENUM)     |                 | status (ENUM)     |
| zarinpal_auth     |                 | amount_rial (INT) |
| amount_rial (INT) |                 | expires_at        |
| expires_at        |                 +-------------------+
+-------------------+
```

---

## 1. User (`users`)

Represents a registered merchant or developer who owns workspaces.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Canonical user identifier |
| `email` | VARCHAR(255) | Unique, Not Null | Normalized lowercase email address |
| `password_hash` | VARCHAR(255) | Nullable | Scrypt hash (`$scrypt$...`); null for OAuth-only users |
| `auth_provider` | VARCHAR(32) | Not Null, Default `'local'` | `'local'`, `'github'`, `'google'` |
| `oauth_id` | VARCHAR(255) | Nullable | External subject / user ID from OAuth provider |
| `full_name` | VARCHAR(255) | Nullable | User display name |
| `created_at` | TIMESTAMPTZ | Not Null, Default now() | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | Not Null, Default now() | Last profile modification timestamp |

**Indexes**:
- `ix_users_email` (unique)
- `ix_users_provider_oauth_id` (`auth_provider`, `oauth_id`)

---

## 2. UserSession (`user_sessions`)

Tracks active authenticated web and API sessions.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Session identifier |
| `user_id` | UUID | Foreign Key (`users.id`), Not Null | Associated user |
| `token_hash` | VARCHAR(64) | Unique, Not Null | SHA-256 hash of the bearer/cookie token |
| `user_agent` | VARCHAR(512) | Nullable | Browser or client user agent string |
| `ip_address` | VARCHAR(64) | Nullable | Remote client IP address |
| `expires_at` | TIMESTAMPTZ | Not Null | Token expiry timestamp (now + 7 days) |
| `created_at` | TIMESTAMPTZ | Not Null, Default now() | Issuance timestamp |

**Indexes**:
- `ix_user_sessions_token_hash` (unique)
- `ix_user_sessions_user_id` (`user_id`)

---

## 3. Project (`projects` extensions)

Extends the workspace tenant with ownership, subscription tier, and enforcement boundaries.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | UUID | Foreign Key (`users.id`), Nullable | Project owner (null for default local project) |
| `tier` | VARCHAR(32) | Not Null, Default `'developer'` | `'developer'` (free), `'team'` (paid), `'unlimited'` |
| `daily_requests_cap` | INTEGER | Not Null, Default 100 | Max allowed requests per 24 hours (0 = unlimited) |
| `max_active_adapters`| INTEGER | Not Null, Default 2 | Max enabled payment adapters (0 = all allowed) |

---

## 4. UsageMeter (`usage_meters` extensions)

Enforces atomic request counting and rolling 24-hour rate limit boundaries.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `requests_today` | INTEGER | Not Null, Default 0 | Requests processed within current 24-hour window |
| `window_started_at` | TIMESTAMPTZ | Not Null, Default now() | Start timestamp of current rate limit cycle |

**Rate Limit Lifecycle**:
- When incoming request arrives:
  1. If `now() - window_started_at >= 24 hours`:
     `requests_today = 0`, `window_started_at = now()`.
  2. If `daily_requests_cap > 0` and `requests_today >= daily_requests_cap`:
     Reject with HTTP 429.
  3. Else:
     `requests_today += 1`, `requests_total += 1`.

---

## 5. Subscription (`subscriptions`)

Tracks commercial plan upgrades and live Zarinpal settlement records.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Subscription record identifier |
| `project_id` | UUID | Foreign Key (`projects.id`), Not Null | Upgraded workspace |
| `user_id` | UUID | Foreign Key (`users.id`), Not Null | Purchasing user |
| `tier` | VARCHAR(32) | Not Null | Target tier (`'team'`) |
| `status` | VARCHAR(32) | Not Null, Default `'pending'` | `'pending'`, `'active'`, `'expired'`, `'cancelled'` |
| `amount_rial` | BIGINT | Not Null | Payment amount in Rial (1,990,000 IRR) |
| `zarinpal_authority`| VARCHAR(64) | Unique, Not Null | Zarinpal PG authority token (`A0000...`) |
| `zarinpal_ref_id` | BIGINT | Nullable | Zarinpal reference transaction number |
| `started_at` | TIMESTAMPTZ | Nullable | Plan activation start timestamp |
| `expires_at` | TIMESTAMPTZ | Nullable | Subscription expiry timestamp (started_at + 30 days) |
| `created_at` | TIMESTAMPTZ | Not Null, Default now() | Initiation timestamp |

**Indexes**:
- `ix_subscriptions_zarinpal_authority` (unique)
- `ix_subscriptions_project_id` (`project_id`)

---

## 6. Checkout Session Lifecycle

Applies to end-buyer payment simulation (`transactions` table):

| State | Trigger | Next State | Timeout / Limit |
|-------|---------|------------|-----------------|
| `initiated` | Merchant initiates payment | `pending` | Returns checkout URL to client |
| `pending` | Buyer opens checkout URL | `approved`, `declined`, `cancelled`, or `expired` | 15 minutes TTL |
| `approved` | Buyer clicks "Pay" | `settled` (via verify) | Normal simulated settlement |
| `cancelled` | Buyer clicks "Cancel" | Callback to merchant | Terminal status |
| `expired` | Inactivity past 15 min | Terminal error | Rejection if Pay attempted |
