# Phase 0 Research: Launch Readiness Flows (004-launch-readiness-flows)

## Summary of Decisions

This document establishes the architecture for the commercial launch flows of IPG Sandbox: multi-provider authentication (OAuth + email/password), live Zarinpal subscription billing, usage quota metering with hard rate-limiting (HTTP 429), gateway adapter restrictions (max 2 for free tier), and verified checkout simulation.

---

### Decision 1: Authentication Architecture (Google, GitHub, Email/Password)

- **Decision**: Implement authentication inside `apps/engine` backed by PostgreSQL, with session cookies forwarded by Next.js dashboard middleware.
  - Password hashing: Python 3.12 stdlib `hashlib.scrypt` (salt + N=16384, r=8, p=1). Zero external packages required (no `passlib`, no `bcrypt`).
  - Session management: Cryptographically secure random session tokens (stdlib `secrets.token_hex(32)`), stored as SHA-256 hashes in PostgreSQL `user_sessions` table with 7-day expiration.
  - OAuth: Lightweight OAuth2 authorization code exchange using `httpx` (already installed) directly to GitHub (`https://github.com/login/oauth/access_token`) and Google (`https://oauth2.googleapis.com/token`).
- **Rationale**:
  - Eliminates external identity service costs and vendor lock-in.
  - Python stdlib provides production-grade cryptographic hashing and randomness out of the box.
  - Keeps the dashboard thin (Next.js server actions/middleware forward cookies to engine `/api/v1/auth`).
- **Alternatives Considered**:
  - *NextAuth.js (Auth.js)*: Requires adding multiple npm dependencies and managing a separate Node.js database adapter connection.
  - *Third-party SaaS (Supabase / Clerk)*: Introduces cloud reliance, subscription costs, and sanctions/access issues for Iranian developers.

---

### Decision 2: Plan Purchase & Upgrade Flow (Live Zarinpal Integration)

- **Decision**: Integrate real Zarinpal PGv4 API in `apps/engine/src/services/billing.py` for plan upgrades (Team Plan: 199,000 Toman / month).
  - Flow:
    1. User clicks "Upgrade" on dashboard pricing page (`POST /api/v1/billing/checkout`).
    2. Engine initiates Zarinpal Payment Request: `https://payment.zarinpal.com/pg/v4/payment/request.json` with merchant ID, amount (1,990,000 Rial = 199,000 Toman), and return callback URL (`/api/v1/billing/callback`).
    3. User is redirected to `https://payment.zarinpal.com/pg/StartPay/{authority}`.
    4. Upon completion, Zarinpal redirects to `/api/v1/billing/callback?Authority=...&Status=OK`.
    5. Engine verifies payment: `https://payment.zarinpal.com/pg/v4/payment/verify.json`.
    6. Upon `code == 100` or `101`, project subscription is upgraded to `tier: team` for 30 days.
  - Local/Dev sandbox override: When `ZARINPAL_MODE=sandbox` or in local test suites, the request routes to the engine's internal Zarinpal adapter for self-contained automated testing.
- **Rationale**:
  - Zarinpal is the standard, trusted payment provider for Iranian SaaS and developers.
  - PGv4 REST API is cleanly implemented using `httpx`.
  - Immediate automatic activation upon verification callback prevents manual provisioning delays.
- **Alternatives Considered**:
  - *Manual invoice / bank transfer*: Adds operational friction and delayed activation.
  - *Stripe / Paddle*: Incompatible with Iranian payment cards and local Toman pricing.

---

### Decision 3: Usage Quota & Rate-Limit Enforcement (HTTP 429 Hard Block)

- **Decision**: Atomic daily request counting in `UsageMeter` table with rolling midnight UTC or 24-hour reset window, plus hard block via HTTP 429.
  - Table extensions on `projects`:
    - `tier`: `VARCHAR(16)` default `'developer'` (or `'free'`). Values: `'developer'`, `'team'`, `'unlimited'`.
    - `daily_requests_cap`: `INTEGER` default `100` (for `'developer'`), `0` (meaning unlimited for `'team'`).
    - `max_active_adapters`: `INTEGER` default `2` (for `'developer'`), `0` (unlimited for `'team'`).
  - Table extensions on `usage_meters`:
    - `requests_today`: `INTEGER` default `0`.
    - `window_started_at`: `TIMESTAMP WITH TIME ZONE` default current timestamp.
  - Enforcement mechanism:
    - Before dispatching payment initiation or adapter endpoints, engine checks:
      - If `window_started_at` is older than 24 hours, reset `requests_today = 0`, `window_started_at = now`.
      - If `daily_requests_cap > 0` and `requests_today >= daily_requests_cap`:
        Return HTTP 429 Too Many Requests with headers:
        - `Retry-After: <seconds_until_window_reset>`
        - `X-RateLimit-Limit: 100`
        - `X-RateLimit-Remaining: 0`
        - `X-RateLimit-Reset: <timestamp>`
        - Body: `{"error": {"code": "daily_quota_exceeded", "message": "Daily request quota (100) exceeded. Please upgrade to Team plan."}}`
    - In `PATCH /api/v1/adapters/{id}`:
      - If request attempts to set `enabled: true`, query count of currently enabled adapters.
      - If `max_active_adapters > 0` and enabled count >= `max_active_adapters`:
        Return HTTP 403 Forbidden with:
        `{"error": {"code": "adapter_limit_exceeded", "message": "Developer plan allows max 2 active gateways. Please upgrade to Team plan to enable all 13 gateways."}}`
- **Rationale**:
  - Satisfies requirement Q3 (Option A: Hard block).
  - Atomic row-level lock on `Project`/`UsageMeter` guarantees zero race conditions during quota depletion.
  - Standard HTTP 429 with rate-limit headers is universally understood by HTTP clients and retry libraries.
- **Alternatives Considered**:
  - *Redis Token Bucket*: Requires adding Redis to the Docker Compose stack, violating ponytail ladder rung 1/2 when PostgreSQL row locking already serializes usage updates cleanly.

---

### Decision 4: Hosted Payment Simulation Page & State Lifecycle

- **Decision**: Reuse and solidify the existing `apps/engine/src/checkout/page.py` server-rendered HTML engine.
  - Validates `token` / `authority` against `Transaction` table.
  - Expiry: Reject payment attempts if `created_at` is older than 15 minutes (`TransactionStatus.expired`).
  - Actions:
    - "Pay": Sets transaction status to `approved` (or applies forced scenario like `pending` / `decline`), generates Shaparak trace metadata, and triggers redirect / callback.
    - "Cancel": Sets transaction status to `cancelled`, triggers return URL with cancellation parameters.
- **Rationale**:
  - Zero external assets or JavaScript runtime dependencies; works offline and inside private development networks.
  - Fully bilingual (RTL Persian / LTR English) with authentic gateway branding for all 13 supported adapters.

---

### Decision 5: Multi-Tenant Workspace & Local Profile Parity

- **Decision**:
  - In hosted mode (`ENGINE_PROFILE=hosted` or default production):
    - Requests to console routes require active session authentication.
    - Projects belong to a `user_id`. Each user has their own workspace, API keys, and transaction history.
  - In local self-hosted mode (`ENGINE_PROFILE=local`):
    - Default project created automatically without requiring login.
    - Quotas set to unlimited (`daily_requests_cap = 0`, `max_active_adapters = 0`) to preserve frictionless local DX.
- **Rationale**:
  - Balances commercial protection for hosted SaaS against zero-friction developer experience for local open-source users.
