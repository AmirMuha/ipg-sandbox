"""Engine settings from the environment (T010) — data-model.md, research R5/R11.

Plain `os.environ` parsing: `pydantic-settings` is not installed and this is five integers, so
the stdlib is the whole job. Invalid values raise `ConfigError` — never a silent clamp, because
a clamped delay is a CI run that hangs for a reason nobody can see.

These are the values a *new* `Project` is seeded with; the env-var names mirror `.env.example`.

`.env` is loaded at import so `pnpm dev` and `docker compose` agree on the database port.
Compose reads the same file, so without this the two paths drifted: the default below points at
5432, and on a machine where another project already owns 5432 `pnpm dev` silently dialled *that*
Postgres and failed with `database "ipg_sandbox" does not exist`.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# data-model.md Validation: delays >= 0 and < 300 (bounded so CI cannot hang).
DELAY_MAX_S = 299
# Bounded retry max: the model only floors it at 1, but an env-supplied 10**9 is a retry storm.
# ponytail: a sanity bound, not a spec number — raise it when a real gateway needs more.
WEBHOOK_RETRY_MAX_CEILING = 10


def load_env_file(path: Path) -> None:
    """Overlay a `.env` file onto `os.environ` without clobbering real env vars.

    Stdlib only — no `python-dotenv`. Handles the subset that matters here: `KEY=value`,
    `#` comments, blank lines, optional `export `, and single/double quotes. An already-set
    variable wins, so `DATABASE_URL=... pnpm dev` and compose's own `environment:` block still
    take precedence over the file.
    """
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


# apps/engine/src/config.py -> apps/engine/src -> apps/engine -> repo root
load_env_file(Path(__file__).resolve().parents[3] / ".env")


class ConfigError(ValueError):
    """An environment value is out of range or not a number."""


def _default_database_url() -> str:
    """Host-side Postgres URL, honouring `.env`'s published `POSTGRES_PORT`.

    Compose passes an explicit `DATABASE_URL` pointing at the in-network host `postgres:5432`,
    so this only runs for `pnpm dev` / pytest, which talk to the port published on the host.
    Reading `POSTGRES_PORT` here is what keeps the two paths on one source of truth — otherwise
    `pnpm dev` dials 5432 regardless of what `.env` says and, on a machine where another
    project owns 5432, connects to a stranger's database instead of failing loudly.
    """
    port = os.environ.get("POSTGRES_PORT", "").strip() or "5432"
    user = os.environ.get("POSTGRES_USER") or "postgres"
    password = os.environ.get("POSTGRES_PASSWORD") or "postgres"
    database = os.environ.get("POSTGRES_DB") or "ipg_sandbox"
    return f"postgresql://{user}:{password}@localhost:{port}/{database}"


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
        url = os.environ.get("DATABASE_URL") or _default_database_url()
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
