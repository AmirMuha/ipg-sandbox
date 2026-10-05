# Research Findings: Admin IPG Toggle

## Existing Implementation

1. **Database & API:**
   - The `AdapterConfig` model (`apps/engine/src/models/models.py`) already has an `enabled` boolean field.
   - The API (`apps/engine/src/api/routes/__init__.py`) exposes `GET /adapters` and `PATCH /adapters/{adapter_id}` which fully supports toggling the `enabled` state.
   - The `checkout_path` and `_resolve_adapter` functions in `apps/engine/src/api/routes/transactions.py` already filter out disabled IPGs, ensuring they cannot be used in checkout.

2. **Dashboard UI:**
   - The project console (`apps/dashboard/src/app/[locale]/(console)/settings/page.tsx`) already renders a list of `AdapterSettings` components.
   - The `AdapterSettings` component (`apps/dashboard/src/components/AdapterSettings.tsx`) already contains a working toggle switch that calls the `PATCH` endpoint to enable or disable an IPG.

## Decision: Fulfilling the Specific Request

The feature specification requested: "admin-dashboard for enabling and disabling the ipgs, let's say I only need to enable the zarinpal for now and disable the other ipgs".

Because the dashboard and API already fully support this capability, no new UI or API endpoints need to be built. To satisfy the specific requirement of "only enable Zarinpal for now and disable the other IPGs" as the default state for the application:

- **Decision**: Update the initialization logic so that Zarinpal is enabled by default and all other IPGs are disabled by default.
- **Rationale**: This gives the user exactly what they asked for ("only enable Zarinpal for now") without removing the other IPGs from the codebase, preserving the ability to enable them later via the existing dashboard UI.
- **Alternatives considered**: We could write a one-off database script to disable them for the current user only, but updating the default seed logic ensures the system behaves this way consistently for any new projects/users.

## Changes Required
1. Modify `seed_configs` in `apps/engine/src/adapters/registry.py` to set `enabled=True` for Zarinpal and `enabled=False` for all other providers.
2. (Optional but recommended) Create an Alembic migration to update existing `AdapterConfig` rows in the database to reflect this preference.
