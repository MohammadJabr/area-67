
import math

from src.matching.sensitivity import (
    build_weight_scenarios,
    run_weight_sensitivity,
)


WEIGHTS = {
    "slope": 0.30,
    "tri": 0.25,
    "local_relief": 0.20,
    "spatial_pattern": 0.20,
    "terrain_distribution": 0.05,
}

CANDIDATES = {
    "Site_A": {
        "slope": 0.2,
        "tri": 0.3,
        "local_relief": 0.4,
        "spatial_pattern": 0.2,
        "terrain_distribution": 0.3,
    },
    "Site_B": {
        "slope": 0.5,
        "tri": 0.6,
        "local_relief": 0.5,
        "spatial_pattern": 0.4,
        "terrain_distribution": 0.5,
    },
    "Site_C": {
        "slope": 0.1,
        "tri": 0.2,
        "local_relief": 0.2,
        "spatial_pattern": 0.1,
        "terrain_distribution": 0.2,
    },
}


def test_weight_scenarios_sum_to_one():
    scenarios = build_weight_scenarios(WEIGHTS)

    assert len(scenarios) == 11

    for weights in scenarios.values():
        assert math.isclose(sum(weights.values()), 1.0)


def test_baseline_weights_are_preserved():
    scenarios = build_weight_scenarios(WEIGHTS)

    assert scenarios["baseline"] == WEIGHTS


def test_sensitivity_counts_are_generated():
    result = run_weight_sensitivity(
        candidates=CANDIDATES,
        base_weights=WEIGHTS,
    )

    assert result["scenario_count"] == 11

    assert set(result["top_k_counts"]) == {3, 5}

    for k, counts in result["top_k_counts"].items():
        assert all(
            0 <= count <= 11
            for count in counts.values()
        )


def test_invalid_relative_change_is_rejected():
    try:
        build_weight_scenarios(WEIGHTS, relative_change=1.0)
        assert False, "Expected ValueError"
    except ValueError:
        pass
