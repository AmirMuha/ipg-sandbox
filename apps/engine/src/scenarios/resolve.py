"""Scenario resolution (T013) — research R5, data-model.md `effective_scenario`.

Precedence, highest first:
1. per-transaction force (`Transaction.forced_scenario` — dashboard or CI pre-seed)
2. `X-Sandbox-Scenario` request header (CI hint; acts as the per-transaction force)
3. project `default_scenario`
4. built-in `approve`

(2) and (1) both express "per-transaction", so a transaction that was *pre-seeded* with an
explicit force keeps it and the header cannot overwrite it.
"""

from src.api.errors import ApiError, ErrorCode
from src.models import ScenarioOutcome

SCENARIO_HEADER = "X-Sandbox-Scenario"
BUILTIN_SCENARIO = ScenarioOutcome.approve

_ALLOWED = tuple(member.value for member in ScenarioOutcome)


def scenario_from_header(raw: str | None) -> ScenarioOutcome | None:
    """Parse the hint header. `None` when absent/blank; `scenario_invalid` when unknown.

    A bad hint is a 400 rather than a silent fall back to the project default — a CI run that
    asked for `declin` must not quietly get an approved payment.
    """
    if raw is None or not raw.strip():
        return None
    try:
        return ScenarioOutcome(raw.strip().lower())
    except ValueError:
        raise ApiError(
            ErrorCode.scenario_invalid,
            f"unknown scenario {raw!r}",
            details={"allowed": list(_ALLOWED)},
        ) from None


def resolve_scenario(
    forced: ScenarioOutcome | None = None,
    *,
    header: str | None = None,
    project_default: ScenarioOutcome | None = None,
) -> ScenarioOutcome:
    """Resolve the scenario for a transaction about to be initiated."""
    if forced is not None:
        return forced
    hinted = scenario_from_header(header)
    if hinted is not None:
        return hinted
    if project_default is not None:
        return project_default
    return BUILTIN_SCENARIO
