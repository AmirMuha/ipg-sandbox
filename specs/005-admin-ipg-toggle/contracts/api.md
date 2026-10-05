# API Contracts: Admin IPG Toggle

*Note: No new API endpoints are required. This document outlines the existing API contracts used by this feature.*

## Existing Endpoints

### `PATCH /api/v1/adapters/{adapter_id}`

Updates the configuration of an adapter, including its enabled state.

**Request Body:**
```json
{
  "enabled": boolean
}
```

**Response:**
Returns the updated adapter object.

### `GET /api/v1/adapters`

Lists all adapters for the authenticated user's project, including their current `enabled` status.
