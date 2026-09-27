"""T013 guard: per-transaction force > header hint > project default > built-in `approve`.

The precedence is a spec edge case (data-model.md, research R5), so it is asserted pairwise
rather than only end-to-end: each rank must beat the one below it *and* lose to the one above.
"""

import pytest

from src.api.errors import ApiError, ErrorCode
from src.models import ScenarioOutcome
from src.scenarios.resolve import SCENARIO_HEADER, resolve_scenario, scenario_from_header


def test_per_transaction_force_beats_project_default():
    """The edge case in one line — a forced transaction ignores the project default."""
    assert (
        resolve_scenario(ScenarioOutcome.decline, project_default=ScenarioOutcome.approve)
        is ScenarioOutcome.decline
    )


def test_per_transaction_force_beats_header_and_default():
    assert (
        resolve_scenario(
            ScenarioOutcome.timeout,
            header="refund",
            project_default=ScenarioOutcome.decline,
        )
        is ScenarioOutcome.timeout
    )


def test_header_beats_project_default():
    """CI hint without a pre-seeded row (contracts/control-api.md)."""
    assert (
        resolve_scenario(header="verify_fail", project_default=ScenarioOutcome.approve)
        is ScenarioOutcome.verify_fail
    )


def test_project_default_used_when_nothing_forced():
    assert resolve_scenario(project_default=ScenarioOutcome.pending_settle) is (
        ScenarioOutcome.pending_settle
    )


def test_builtin_approve_when_nothing_set():
    """Last rung: no force, no header, no project default."""
    assert resolve_scenario() is ScenarioOutcome.approve


def test_blank_header_falls_through_to_project_default():
    """An absent or whitespace header is not a force — it must not resolve to a scenario."""
    for blank in (None, "", "   "):
        assert resolve_scenario(header=blank, project_default=ScenarioOutcome.decline) is (
            ScenarioOutcome.decline
        )


@pytest.mark.parametrize("scenario", list(ScenarioOutcome))
def test_every_scenario_is_resolvable_from_the_header(scenario):
    """All six wire values round-trip, so no scenario is unreachable from CI."""
    assert resolve_scenario(header=scenario.value) is scenario


@pytest.mark.parametrize("raw", ["declin", "APPROVE!", "approve decline", "null"])
def test_unknown_header_value_is_scenario_invalid(raw):
    """A typo must 400, not silently approve a payment CI expected to be declined."""
    with pytest.raises(ApiError) as excinfo:
        scenario_from_header(raw)

    assert excinfo.value.code is ErrorCode.scenario_invalid
    assert excinfo.value.status == 400


def test_header_name_matches_the_contract():
    assert SCENARIO_HEADER == "X-Sandbox-Scenario"
