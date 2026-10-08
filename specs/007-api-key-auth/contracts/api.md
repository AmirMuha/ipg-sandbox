# API Contracts: API Key Authentication

## REST API (FastAPI)

### 1. List API Keys
- **Endpoint**: `GET /api/v1/auth/api-keys`
- **Auth**: Requires existing session auth (Cookie/Bearer)
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "uuid",
        "name": "My Prod Key",
        "last_four": "a1b2",
        "created_at": "2026-10-08T12:00:00Z",
        "last_used_at": "2026-10-08T14:30:00Z",
        "revoked_at": null
      }
    ]
  }
  ```

### 2. Create API Key
- **Endpoint**: `POST /api/v1/auth/api-keys`
- **Auth**: Requires existing session auth
- **Request**:
  ```json
  {
    "name": "My Prod Key"
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "id": "uuid",
      "name": "My Prod Key",
      "token": "ipg_key_abcdef1234567890abcdef1234567890",
      "last_four": "7890",
      "created_at": "2026-10-08T12:00:00Z"
    }
  }
  ```
  *(Note: `token` is only returned once here)*

### 3. Revoke API Key
- **Endpoint**: `DELETE /api/v1/auth/api-keys/{id}`
- **Auth**: Requires existing session auth
- **Response**: `204 No Content`

### 4. Authentication Middleware
- **Header**: `Authorization: Bearer ipg_key_...`
- **Behavior**:
  - Extract token.
  - Compute SHA-256 hash.
  - Lookup active `ApiKey` by `key_hash`.
  - If found and not revoked, attach `user` to request context and update `last_used_at`.
  - Else, return `401 Unauthorized`.
