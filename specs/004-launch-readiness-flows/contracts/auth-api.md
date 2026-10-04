# Authentication API Contract (004-launch-readiness-flows)

Base path: `/api/v1/auth`

---

## 1. Register with Email / Password

`POST /api/v1/auth/register`

### Request

```json
{
  "email": "developer@company.com",
  "password": "StrongPassword123!",
  "full_name": "Reza Rahmani"
}
```

### Response (201 Created)

Sets HTTP-only cookie: `ipg_session=<token>; Path=/; Max-Age=604800; SameSite=Lax; HttpOnly`

```json
{
  "user": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "developer@company.com",
    "full_name": "Reza Rahmani",
    "auth_provider": "local",
    "created_at": "2026-10-04T12:00:00Z"
  },
  "project": {
    "id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    "name": "developer's workspace",
    "tier": "developer"
  }
}
```

### Error Responses

- `400 Bad Request`: `{"error": {"code": "email_exists", "message": "Email is already registered."}}`
- `422 Unprocessable Entity`: Password < 8 characters or invalid email format.

---

## 2. Login with Email / Password

`POST /api/v1/auth/login`

### Request

```json
{
  "email": "developer@company.com",
  "password": "StrongPassword123!"
}
```

### Response (200 OK)

Sets HTTP-only cookie `ipg_session=<token>`.

```json
{
  "user": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "developer@company.com",
    "full_name": "Reza Rahmani"
  },
  "token": "32_byte_hex_session_token"
}
```

### Error Responses

- `401 Unauthorized`: `{"error": {"code": "invalid_credentials", "message": "Invalid email or password."}}`

---

## 3. Current Authenticated User & Workspace

`GET /api/v1/auth/me`

Headers: `Cookie: ipg_session=<token>` OR `Authorization: Bearer <token>`

### Response (200 OK)

```json
{
  "user": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "developer@company.com",
    "full_name": "Reza Rahmani"
  },
  "project": {
    "id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    "name": "developer's workspace",
    "tier": "developer",
    "daily_requests_cap": 100,
    "max_active_adapters": 2
  }
}
```

### Error Responses

- `401 Unauthorized`: `{"error": {"code": "unauthenticated", "message": "Session expired or invalid."}}`

---

## 4. Logout

`POST /api/v1/auth/logout`

Clears cookie and deletes active session from database.

### Response (200 OK)

```json
{
  "status": "ok"
}
```

---

## 5. OAuth Initiation & Callbacks

### GitHub OAuth
- `GET /api/v1/auth/oauth/github`: Redirects browser to `https://github.com/login/oauth/authorize?client_id=...&scope=read:user,user:email`
- `GET /api/v1/auth/oauth/github/callback?code=...`: Exchanges code for access token, fetches profile, creates/logs in user, sets session cookie, redirects to `/console`.

### Google OAuth
- `GET /api/v1/auth/oauth/google`: Redirects browser to Google OAuth consent URL.
- `GET /api/v1/auth/oauth/google/callback?code=...`: Exchanges code, retrieves Google userinfo, provisions user, redirects to `/console`.
