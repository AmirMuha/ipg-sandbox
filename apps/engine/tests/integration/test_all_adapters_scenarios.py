"""Integration tests covering all 13 gateways × 6 scenarios (T037) — SC-004."""

import pytest

from src.models import Provider, ScenarioOutcome
from src.scenarios.adapter_mappings import SCENARIO_MAPPINGS, get_scenario_response


def test_matrix_is_6_outcomes_by_13_adapters():
    """Verify SC-004: All 13 gateways x 6 scenarios exist in the mapping matrix."""
    assert len(SCENARIO_MAPPINGS) == 13
    assert set(SCENARIO_MAPPINGS.keys()) == set(Provider)
    for p in Provider:
        assert len(SCENARIO_MAPPINGS[p]) == 6
        for s in ScenarioOutcome:
            resp = get_scenario_response(p, s)
            assert "code" in resp
            assert "message" in resp


@pytest.mark.parametrize("provider", list(Provider))
@pytest.mark.parametrize("scenario", list(ScenarioOutcome))
def test_scenario_mapping_completeness(provider: Provider, scenario: ScenarioOutcome):
    resp = get_scenario_response(provider, scenario)
    assert resp is not None
    assert resp["code"] is not None
    assert isinstance(resp["message"], str)
    assert len(resp["message"]) > 0
