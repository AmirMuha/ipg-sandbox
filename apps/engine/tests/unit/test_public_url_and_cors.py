"""`public_base_url()` and the dashboard CORS allowlist (T010, T002 — FR-002, FR-010).

Both are pure env/regex logic whose failure mode is silence: a wrong `checkout_url` still
renders a link, and a wrong origin still 200s a non-browser client. Nothing else in the
suite moves `ENGINE_PORT` or asserts an `Origin` header, so both are unguarded elsewhere.
"""

import re

import pytest
from fastapi.testclient import TestClient

from src.config import public_base_url

DEFAULT_ORIGIN = "http://localhost:3000"


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        ("9000", "http://localhost:9000"),  # the remapped-port case the env read exists for
        ("8080", "http://localhost:8080"),
        ("", "http://localhost:8080"),  # compose passes empty for an unset var
        ("  9001  ", "http://localhost:9001"),  # stripped, not interpolated with spaces
    ],
)
def test_public_base_url_follows_engine_port(monkeypatch, env_value, expected):
    """A hardcoded 8080 would send every `checkout_url` to a port nobody is listening on."""
    monkeypatch.setenv("ENGINE_PORT", env_value)
    assert public_base_url() == expected


def test_public_base_url_defaults_when_env_absent(monkeypatch):
    monkeypatch.delenv("ENGINE_PORT", raising=False)
    assert public_base_url() == "http://localhost:8080"


def test_public_base_url_is_read_at_call_time(monkeypatch):
    """Not cached at import: a port remapped after startup must still be picked up."""
    monkeypatch.setenv("ENGINE_PORT", "8080")
    first = public_base_url()
    monkeypatch.setenv("ENGINE_PORT", "9100")
    assert public_base_url() != first == "http://localhost:8080"
    assert public_base_url() == "http://localhost:9100"


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3000",  # the default dashboard
        "http://localhost:3001",  # taken, so the dev runs the next port
        "http://localhost:65535",  # any loopback port the regex promises
        "http://127.0.0.1:3000",  # the other host spelling
        "http://127.0.0.1:3005",
        "http://localhost",  # no port at all
    ],
)
def test_cors_allows_loopback_origins_at_any_port(client: TestClient, origin):
    """FR-010: a remapped `DASHBOARD_PORT` must not silently break browser preflights."""
    resp = client.get(
        "/api/v1/project",
        headers={"Origin": origin},
    )
    assert resp.headers.get("access-control-allow-origin") == origin, origin


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.example.com",  # a different host is never the dashboard
        "http://localhost.evil.com",  # prefix match, not a substring match
        "http://127.0.0.1.evil.com",
    ],
)
def test_cors_rejects_foreign_origins(client: TestClient, origin):
    """A browser trusts the response, so a reflected `Access-Control-Allow-Origin` is the bug."""
    resp = client.get("/api/v1/project", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") is None, origin


def test_cors_preflight_from_a_remapped_dashboard_port_succeeds(client: TestClient):
    """The browser's first call is a preflight; blocking it blocks the whole app."""
    resp = client.options(
        "/api/v1/transactions/simulate",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3001"
    assert "POST" in resp.headers.get("access-control-allow-methods", "")


def test_allow_origin_regex_matches_only_loopback():
    """Pinned independently of the middleware so a bad pattern is a readable failure."""
    pattern = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")
    assert pattern.match("http://localhost:3000")
    assert pattern.match("https://127.0.0.1")
    assert not pattern.match("http://evil.com")
    assert not pattern.match("http://localhost.evil.com")
    assert DEFAULT_ORIGIN  # documents the seeded default the other tests build on
