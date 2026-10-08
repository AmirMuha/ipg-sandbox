# Research: API Key Authentication

## Hashing Algorithm for API Keys
- **Decision**: SHA-256 for one-way hashing of API keys.
- **Rationale**: SHA-256 is fast, standard, and secure for high-entropy randomly generated tokens. Unlike user passwords (which require slow hashes like bcrypt/argon2 to prevent brute-forcing), API keys are 32+ character random strings, so they are not vulnerable to dictionary attacks. A fast hash like SHA-256 minimizes the `<50ms` auth overhead while ensuring the plaintext key isn't stored.
- **Alternatives considered**: bcrypt (too slow, adds unnecessary latency for API auth).

## Authentication Method (FastAPI)
- **Decision**: Bearer token via `Authorization: Bearer ipg_key_...` header.
- **Rationale**: Standard HTTP mechanism. FastAPI has built-in support for `HTTPBearer` which simplifies dependency injection for authenticated routes.
- **Alternatives considered**: Custom `X-API-Key` header. While valid, `Authorization: Bearer` is more standard for token-based auth.

## Next.js UI Integration
- **Decision**: Add an "API Keys" section to the user settings dashboard in `apps/web`.
- **Rationale**: Standard location for developer settings. Will allow viewing active keys (name, created at, last 4 chars), revoking keys, and a modal for creating new keys which displays the full key once.
- **Alternatives considered**: A dedicated top-level "Developers" page. Kept it in settings to reduce top-level navigation clutter for an MVP.
