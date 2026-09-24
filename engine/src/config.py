"""Engine settings from the environment (T010) — data-model.md, research R5/R11.

Plain `os.environ` parsing: `pydantic-settings` is not installed and this is five integers, so
the stdlib is the whole job. Invalid values raise `ConfigError` — never a silent clamp, because
a clamped delay is a CI run that hangs for a reason nobody can see.

These are the values a *new* `Project` is seeded with; the env-var names mirror `.env.example`.
"""

import os
from dataclasses import dataclass

# data-model.md Validation: delays >= 0 and < 300 (bounded so CI cannot hang).
DELAY_MAX_S = 299
# Bounded retry max: the model only floors it at 1, but an env-supplied 10**9 is a retry storm.
# ponytail: a sanity bound, not a spec number — raise it when a real gateway needs more.
WEBHOOK_RETRY_MAX_CEILING = 10

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ipg_sandbox"


class ConfigError(ValueError):
    """An environment value is out of range or not a number."""


def _env_int(name: str, default: int, *, low: int, high: int | None = None) -> int:
    """Read an integer env var, or raise `ConfigError`. `low`/`high` are inclusive."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        value = default
    else:
        try:
            value = int(raw)
        except ValueError as exc:
            raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc

    bound = f">= {low}" if high is None else f">= {low} and <= {high}"
    if value < low or (high is not None and value > high):
        raise ConfigError(f"{name} must be {bound}, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    """Env-derived settings. Build with `from_env()` — the dataclass does not validate."""

    database_url: str
    history_cap: int
    webhook_retry_max: int
    pending_settle_delay_s: int
    timeout_delay_s: int

    @classmethod
    def from_env(cls) -> "Settings":
        url = os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
        # asyncpg is the project's only async driver; alembic/env.py performs the same upgrade.
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return cls(
            database_url=url,
            history_cap=_env_int("DEFAULT_HISTORY_CAP", 1000, low=1),
            webhook_retry_max=_env_int(
                "DEFAULT_WEBHOOK_RETRY_MAX", 3, low=1, high=WEBHOOK_RETRY_MAX_CEILING
            ),
            # clarification 5: pending_settle settles 5s after checkout by default.
            pending_settle_delay_s=_env_int(
                "DEFAULT_PENDING_SETTLE_DELAY_S", 5, low=0, high=DELAY_MAX_S
            ),
            timeout_delay_s=_env_int("DEFAULT_TIMEOUT_DELAY_S", 30, low=0, high=DELAY_MAX_S),
        )
