"""T059: simulation guard (FR-012) — no real payments, no card data, no production gateways.

Two halves, both static assertions over the source tree:

1. **Egress.** The only outbound HTTP call the engine may make is a webhook POST to a target
   the caller configured. A new `httpx`/`requests`/`urllib` import anywhere else is the thing
   this guard exists to catch, so it scans imports rather than mocking a runtime.
2. **Card data.** No model column and no schema field may hold card data. The IDPay/Zarinpal
   adapters legitimately *emit* masked PAN strings — that is the gateway's response contract,
   not collection — so the card scan is scoped to the persistence layer and the emitted values
   are asserted to be static masked literals.

Scanning source is deliberate: a runtime mock would only prove the paths the suite happens to
exercise, and FR-012 is a claim about the whole engine.
"""

import ast
import re
from pathlib import Path

import pytest

import src

ENGINE_SRC = Path(src.__file__).parent
REPO_ROOT = ENGINE_SRC.parents[2]

# Modules that may open a socket. Everything else under src/ is on the deny list.
EGRESS_ALLOWLIST = {
    # Webhook delivery POSTs to tx.callback_url / project.webhook_url — the one caller-
    # configured egress path (FR-007), and the only reason httpx is a dependency at all.
    Path("webhooks/worker.py"),
}

NETWORK_MODULES = {"httpx", "httpx2", "requests", "urllib3", "aiohttp", "http.client", "socket"}

# `urllib.parse` is string manipulation, not egress — the adapter routes parse query strings
# with it. Only the network half of the stdlib counts.
NETWORK_SUBMODULES = {"urllib.request", "urllib.error"}

# Card-data vocabulary. Deliberately broad: a new column called `pan` or `cvv2` is the exact
# failure this catches, and a false positive here is a naming conversation, not a bug.
CARD_PATTERNS = [
    r"\bcard_?number\b",
    r"\bcard_?no\b",
    r"\bcard_?pan\b",
    r"\bcvv2?\b",
    r"\bcvc\b",
    r"\bexpiry_?date\b",
    r"\bcard_?holder\b",
    r"\bholder_?name\b",
    r"\btrack_?[12]\b",
    r"\biban\b",
]
CARD_RE = re.compile("|".join(CARD_PATTERNS), re.IGNORECASE)


def _relative(path: Path) -> Path:
    return path.relative_to(ENGINE_SRC)


def _imported_roots(tree: ast.AST) -> set[str]:
    """Fully-qualified dotted name of every import in a module.

    Full paths, not just the top-level package, so `urllib.parse` and `urllib.request` can be
    told apart: the first is string handling, the second opens a socket.
    """
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module)
    return roots


def _offending_network_imports(tree: ast.AST) -> set[str]:
    """Network-capable imports, matched at full path or at top-level package."""
    imports = _imported_roots(tree)
    return {
        name
        for name in imports
        if name in NETWORK_MODULES
        or name in NETWORK_SUBMODULES
        or name.split(".")[0] in NETWORK_MODULES
    }


def _engine_modules() -> list[Path]:
    return sorted(p for p in ENGINE_SRC.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize(
    "module",
    [m for m in _engine_modules() if _relative(m) not in EGRESS_ALLOWLIST],
    ids=lambda p: str(_relative(p)),
)
def test_no_network_client_imports_outside_the_webhook_worker(module: Path):
    """FR-012: the engine reaches no real gateway. Only the webhook worker may hold a client."""
    roots = _offending_network_imports(ast.parse(module.read_text(encoding="utf-8")))
    offending = roots
    assert not offending, (
        f"{_relative(module)} imports {sorted(offending)}; egress is restricted to "
        f"{sorted(str(p) for p in EGRESS_ALLOWLIST)} (configured callback targets only)"
    )


def test_webhook_egress_targets_are_caller_configured():
    """The one allowlisted module POSTs to tx.callback_url / project.webhook_url, nowhere else."""
    source = (ENGINE_SRC / "webhooks/worker.py").read_text(encoding="utf-8")

    assert "client.post(target" in source
    assert "_target_for" in source
    # No hardcoded external host may appear anywhere in the worker.
    assert not re.search(r"https?://(?!localhost|127\.0\.0\.1|host\.docker\.internal)", source)


def test_no_card_data_columns_in_orm_models():
    """FR-012: nothing card-shaped is persisted. A card field here would be a schema breach."""
    from src.models import Base

    offenders = [
        f"{table.name}.{column.name}"
        for table in Base.metadata.tables.values()
        for column in table.columns
        if CARD_RE.search(column.name)
    ]
    assert not offenders, f"card-data columns present: {offenders}"


def test_no_card_data_fields_in_any_pydantic_schema():
    """The engine exposes no BaseModel schema today; keep it that way (T059)."""
    schema_modules = [
        path for path in _engine_modules() if "BaseModel" in path.read_text(encoding="utf-8")
    ]
    assert not schema_modules, (
        "Pydantic schemas appeared in the engine; add a card-data scan for them: "
        f"{[str(_relative(p)) for p in schema_modules]}"
    )


def test_adapter_card_values_are_static_masked_literals():
    """IDPay/Zarinpal echo a masked PAN per the gateway contract. It must be a fixed literal.

    A *dynamic* PAN would mean the engine collected card data and is replaying it — the exact
    thing FR-012 forbids. So the guard is not "no PAN key" but "PAN key, constant value".
    """
    offenders: list[str] = []
    for adapter in ("idpay", "zarinpal"):
        path = ENGINE_SRC / "adapters" / adapter / "adapter.py"
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not CARD_RE.search(line):
                continue
            # Every card-shaped key must be assigned a quoted, fully-masked constant or masked_pan generator.
            match = re.search(r"""["'](\w+)["']\s*:\s*(.+)""", line)
            if match is None or not (
                re.fullmatch(r"""["'][^"']*["']\s*,?""", match.group(2).strip())
                or "masked_pan(" in match.group(2)
            ):
                offenders.append(f"{adapter}/adapter.py:{line_number}: {line.strip()}")
                continue
            if "masked_pan(" not in match.group(2) and not re.search(r"\*", match.group(2)):
                offenders.append(
                    f"{adapter}/adapter.py:{line_number}: unmasked value {line.strip()}"
                )

    assert not offenders, "card values must be static, fully masked literals: " + "; ".join(
        offenders
    )


def test_no_production_gateway_hosts_anywhere_in_source():
    """FR-012: no real gateway endpoint may be configured as a default anywhere.

    Matches a *URL*, not the bare brand name: the Behpardakht adapter documents itself as a
    Mellat PGW emulator, so the word appears in docstrings while the code stays offline.
    """
    source_files = [
        path for path in REPO_ROOT.glob("apps/*/src/**/*.py") if "__pycache__" not in path.parts
    ]
    production_hosts = (
        "zarinpal.com",
        "idpay.ir",
        "behpardakht.com",
        "nextpay",
        "mellat.ir",
    )
    url_re = re.compile(r"https?://[^\s\"'`<>)]+", re.IGNORECASE)
    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {url}"
        for path in source_files
        for url in url_re.findall(path.read_text(encoding="utf-8"))
        if any(host in url.lower() for host in production_hosts)
    ]
    assert not offenders, f"production gateway hosts referenced in source: {offenders}"
