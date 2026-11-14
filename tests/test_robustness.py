from src.matching.mission_profiles import get_mission_weights
from src.matching.pipeline import rank_terrain_fingerprints
from src.matching.sensitivity import run_matching_robustness


def test_matching_robustness_combines_weight_sensitivity_and_slope_baseline(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate_a = dict(earth_candidate)
    candidate_a["site_id"] = "EARTH_A"
    candidate_a["source_id"] = "DEM_A"
    candidate_a["slope_median"] = 12.0
    candidate_a["slope_p90"] = 22.0

    candidate_b = dict(earth_candidate)
    candidate_b["site_id"] = "EARTH_B"
    candidate_b["source_id"] = "DEM_B"
    candidate_b["slope_median"] = 20.0
    candidate_b["slope_p90"] = 30.0
    candidate_b["tri_median"] = 4.0
    candidate_b["tri_p90"] = 7.0
    candidate_b["local_relief_p95_p5"] = 50.0

    matching = rank_terrain_fingerprints(
        target_fingerprint,
        {"EARTH_A": candidate_a, "EARTH_B": candidate_b},
        get_mission_weights(),
        matching_tolerances,
        mission_profile="Rover Navigation / Terrain Traversal",
    )

    result = run_matching_robustness(matching, get_mission_weights())

    sensitivity = result["weight_sensitivity"]
    baseline = result["slope_only_baseline"]

    assert sensitivity["scenario_count"] == 11
    assert set(sensitivity["top_k_counts"]) == {3, 5}
    assert len(baseline["slope_only_ranking"]) == 2
    assert len(baseline["rank_comparison"]) == 2
