# Quota Enforcement Contract (004-launch-readiness-flows)

Defines system responses and headers when plan limitations or restrictions are encountered.

---

## 1. Daily Request Quota Reached (HTTP 429)

Triggered on any IPG payment initiation or public API endpoint when `project.daily_requests_cap > 0` and `usage_meter.requests_today >= project.daily_requests_cap`.

### HTTP Status
`429 Too Many Requests`

### Response Headers
```http
Retry-After: 43200
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1728086400
Content-Type: application/json
```

### Response Body
```json
{
  "error": {
    "code": "daily_quota_exceeded",
    "message": "Daily request quota of 100 requests has been exhausted for this workspace.",
    "details": {
      "limit": 100,
      "current": 100,
      "resets_in_seconds": 43200,
      "upgrade_url": "/pricing"
    }
  }
}
```

---

## 2. Gateway Adapter Limit Exceeded (HTTP 403)

Triggered on `PATCH /api/v1/adapters/{id}` when `project.max_active_adapters > 0`, payload contains `{"enabled": true}`, and the count of currently enabled adapters for the project already equals `project.max_active_adapters`.

### HTTP Status
`403 Forbidden`

### Response Body
```json
{
  "error": {
    "code": "adapter_limit_exceeded",
    "message": "Developer plan is limited to 2 active payment gateways simultaneously.",
    "details": {
      "max_active": 2,
      "currently_active": 2,
      "upgrade_url": "/pricing"
    }
  }
}
```

---

## 3. Quota Usage Query

`GET /api/v1/meters`

Returns current consumption and active plan ceilings.

### Response (200 OK)

```json
{
  "tier": "developer",
  "requests_total": 420,
  "requests_today": 84,
  "daily_requests_cap": 100,
  "requests_remaining_today": 16,
  "active_adapters_count": 2,
  "max_active_adapters": 2,
  "transactions_total": 312,
  "history_retained": 312,
  "history_cap": 1000,
  "window_resets_at": "2026-10-05T00:00:00Z"
}
```
