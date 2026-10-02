"""T010 guards: bad env values raise instead of being clamped.

`Settings.from_env()` reads `os.environ` directly, so each case patches the mapping and asserts
both directions — that a bad value raises *and* that the documented default survives the trip.
"""

import os

import pytest

from src.config import ConfigError, Settings, load_env_file

# Every knob plus the value that must be rejected for it. 300 is the exclusive upper bound
# (data-model.md); -1 is under every floor.
OUT_OF_RANGE = [
    ("DEFAULT_PENDING_SETTLE_DELAY_S", "300"),
    ("DEFAULT_PENDING_SETTLE_DELAY_S", "-1"),
    ("DEFAULT_TIMEOUT_DELAY_S", "300"),
    ("DEFAULT_TIMEOUT_DELAY_S", "-1"),
    ("DEFAULT_HISTORY_CAP", "0"),
    ("DEFAULT_HISTORY_CAP", "-1"),
    ("DEFAULT_WEBHOOK_RETRY_MAX", "0"),
    ("DEFAULT_WEBHOOK_RETRY_MAX", "9999"),  # bounded max, not just a floor
]


@pytest.mark.parametrize(("name", "value"), OUT_OF_RANGE)
def test_out_of_range_env_value_raises(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError):
        Settings.from_env()


@pytest.mark.parametrize("value", ["abc", "1.5", ""])
def test_non_integer_delay_raises(monkeypatch, value):
    """`""` is treated as unset (compose passes empty for an unset var); text is not."""
    monkeypatch.setenv("DEFAULT_TIMEOUT_DELAY_S", value)
    if value == "":
        assert Settings.from_env().timeout_delay_s == 30
    else:
        with pytest.raises(ConfigError):
            Settings.from_env()


def test_defaults_match_the_spec(monkeypatch):
    for name in (
        "DEFAULT_HISTORY_CAP",
        "DEFAULT_WEBHOOK_RETRY_MAX",
        "DEFAULT_PENDING_SETTLE_DELAY_S",
        "DEFAULT_TIMEOUT_DELAY_S",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings.pending_settle_delay_s == 5  # clarification 5 — must not drift
    assert settings.timeout_delay_s == 30  # < 300, service default
    assert settings.history_cap == 1000  # FR-006
    assert settings.webhook_retry_max == 3
    assert settings.database_url.startswith("postgresql+asyncpg://")


@pytest.mark.parametrize("value", ["0", "299"])
def test_delay_bounds_are_inclusive_at_zero_and_exclusive_at_300(monkeypatch, value):
    """0 is legal, 299 is legal, 300 is not — the guard must not be off-by-one either way."""
    monkeypatch.setenv("DEFAULT_PENDING_SETTLE_DELAY_S", value)
    assert Settings.from_env().pending_settle_delay_s == int(value)


def test_plain_postgres_url_is_upgraded_to_asyncpg(monkeypatch):
    """compose passes `postgresql://`; asyncpg is the only async driver installed."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db:5432/x")
    assert Settings.from_env().database_url == "postgresql+asyncpg://u:p@db:5432/x"


# --- .env loading and host-port resolution --------------------------------------------------
# `pnpm dev` used to dial localhost:5432 regardless of `.env`, so on a machine where another
# project owns 5432 it connected to a stranger's database and died with
# `database "ipg_sandbox" does not exist`.


def test_env_file_overlays_but_never_clobbers(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# a comment",
                "",
                "FROM_FILE=file-value",
                'QUOTED="quoted value"',
                "SINGLE='single value'",
                "export EXPORTED=exported-value",
                "WITH_HASH=value # not a comment here",
            ]
        )
    )
    monkeypatch.delenv("FROM_FILE", raising=False)
    monkeypatch.setenv("ALREADY_SET", "original")

    load_env_file(env_file)

    assert os.environ["FROM_FILE"] == "file-value"
    assert os.environ["QUOTED"] == "quoted value"
    assert os.environ["SINGLE"] == "single value"
    assert os.environ["EXPORTED"] == "exported-value"
    assert os.environ["ALREADY_SET"] == "original", "a real env var must win over the file"


def test_env_file_absent_is_not_an_error(tmp_path):
    load_env_file(tmp_path / "does-not-exist.env")  # must not raise


def test_database_url_uses_the_published_postgres_port(monkeypatch):
    """`pnpm dev` talks to the published host port, not the in-network container one."""
    for name in (
        "DATABASE_URL",
        "POSTGRES_PORT",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("POSTGRES_PORT", "55432")

    url = Settings.from_env().database_url

    assert "localhost:55432" in url
    assert url.startswith("postgresql+asyncpg://")


def test_explicit_database_url_still_wins(monkeypatch):
    """An exported DATABASE_URL overrides `.env`/defaults — compose relies on this."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.internal:5433/other")
    monkeypatch.setenv("POSTGRES_PORT", "55432")

    url = Settings.from_env().database_url

    assert url == "postgresql+asyncpg://u:p@db.internal:5433/other"
