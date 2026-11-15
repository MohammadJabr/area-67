from src.matching.mission_profiles import get_mission_weights
from src.matching.tolerance_sensitivity import run_tolerance_sensitivity


def test_tolerance_sensitivity_runs_baseline_and_one_at_a_time_scenarios(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate_a = dict(earth_candidate)
    candidate_a["site_id"] = "EARTH_A"
    candidate_b = dict(earth_candidate)
    candidate_b.update({
        "site_id": "EARTH_B",
        "slope_median": 25.0,
        "slope_p90": 35.0,
        "tri_median": 8.0,
        "tri_p90": 12.0,
        "local_relief_p95_p5": 60.0,
        "largest_steep_patch_pct": 35.0,
    })

    result = run_tolerance_sensitivity(
        target_fingerprint,
        {"EARTH_A": candidate_a, "EARTH_B": candidate_b},
        get_mission_weights(),
        matching_tolerances,
        mission_profile="Rover Navigation / Terrain Traversal",
        min_feature_group_completeness=1.0,
        min_data_completeness=0.95,
    )

    assert result["scenario_count"] == 11
    assert result["factors"] == [0.5, 1.0, 1.5]
    assert result["baseline_order"] == ["EARTH_A", "EARTH_B"]
    assert len(result["scenario_rankings"]) == 11
    assert set(result["top_k_counts"]) == {1, 3, 5}
    assert "EARTH_A" in result["top_k_counts"][1]


def test_tolerance_sensitivity_rejects_invalid_factors(
    target_fingerprint, earth_candidate, matching_tolerances
):
    import pytest

    with pytest.raises(ValueError, match="factors"):
        run_tolerance_sensitivity(
            target_fingerprint,
            {"EARTH_A": earth_candidate},
            get_mission_weights(),
            matching_tolerances,
            mission_profile="Rover Navigation / Terrain Traversal",
            min_feature_group_completeness=1.0,
            min_data_completeness=0.95,
            factors=(0.5, 0.8, 1.5),
        )
