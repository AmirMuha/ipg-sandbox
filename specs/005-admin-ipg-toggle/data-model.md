# Data Model: Admin IPG Toggle

*Note: No new data models are required for this feature as the underlying data structures already exist in the codebase.*

## Existing Entities

### `AdapterConfig`

Represents a payment gateway configuration for a specific project.

**Fields of Interest:**
- `id` (UUID): Primary key
- `project_id` (UUID): Foreign key to the project
- `provider` (Enum): The payment gateway provider (e.g., `zarinpal`, `idpay`)
- `enabled` (Boolean): **The key field for this feature.** Defaults to `True` historically, but will be updated to default to `False` for non-Zarinpal IPGs.
- `credentials` (JSONB): The credentials for the IPG

**Validation Rules:**
- A project can only have one enabled row per provider (enforced by `uq_adapter_configs_enabled_provider` index).

**State Transitions:**
- `enabled` can be toggled between `True` and `False` via the `PATCH /adapters/{adapter_id}` endpoint.
