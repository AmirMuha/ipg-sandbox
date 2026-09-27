"""T010 guards: bad env values raise instead of being clamped.

`Settings.from_env()` reads `os.environ` directly, so each case patches the mapping and asserts
both directions — that a bad value raises *and* that the documented default survives the trip.
"""

import pytest

from src.config import ConfigError, Settings

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
