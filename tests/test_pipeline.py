import copy

from src.matching.mission_profiles import get_mission_weights
from src.matching.pipeline import rank_terrain_fingerprints


def _candidate(base, site_id, **updates):
    result = copy.deepcopy(base)
    result["site_id"] = site_id
    result["planet"] = "Earth"
    result["source_id"] = f"DEM_{site_id}"
    result.update(updates)
    return result


def test_pipeline_ranks_fingerprints_and_returns_app_context(
    target_fingerprint, earth_candidate, matching_tolerances
):
    exact = _candidate(earth_candidate, "EARTH_EXACT")
    close = _candidate(
        earth_candidate,
        "EARTH_CLOSE",
        slope_median=12.0,
        slope_p90=22.0,
        tri_median=2.5,
        tri_p90=5.5,
        local_relief_p95_p5=33.0,
    )
    distant = _candidate(
        earth_candidate,
        "EARTH_DISTANT",
        slope_median=30.0,
        slope_p90=45.0,
        tri_median=10.0,
        tri_p90=20.0,
        local_relief_p95_p5=80.0,
        terrain_low_pct=5.0,
        terrain_mid_pct=25.0,
        terrain_high_pct=70.0,
        largest_steep_patch_pct=60.0,
    )

    result = rank_terrain_fingerprints(
        target_fingerprint,
        {
            "EARTH_CLOSE": close,
            "EARTH_DISTANT": distant,
            "EARTH_EXACT": exact,
        },
        get_mission_weights(),
        matching_tolerances,
        mission_profile="Rover Navigation / Terrain Traversal",
    )

    assert result["target_site_id"] == "MOON_SITE04"
    assert result["mission_profile"] == "Rover Navigation / Terrain Traversal"
    assert [item["site_id"] for item in result["ranking"]] == [
        "EARTH_EXACT",
        "EARTH_CLOSE",
        "EARTH_DISTANT",
    ]
    assert [item["rank"] for item in result["ranking"]] == [1, 2, 3]
    assert result["ranking"][0]["similarity_score"] == 100.0
    assert result["ranking"][0]["data_completeness"] == 0.95
    assert result["rejected_candidates"] == []


def test_pipeline_rejects_scale_mismatch_without_failing_other_candidates(
    target_fingerprint, earth_candidate, matching_tolerances
):
    good = _candidate(earth_candidate, "EARTH_GOOD")
    bad = _candidate(earth_candidate, "EARTH_BAD", analysis_scale_m=100.0)

    result = rank_terrain_fingerprints(
        target_fingerprint,
        {"EARTH_GOOD": good, "EARTH_BAD": bad},
        get_mission_weights(),
        matching_tolerances,
        mission_profile="Rover Navigation",
    )

    assert [item["site_id"] for item in result["ranking"]] == ["EARTH_GOOD"]
    assert result["rejected_candidates"][0]["site_id"] == "EARTH_BAD"
    assert "Incompatible analysis scales" in result["rejected_candidates"][0]["reason"]


def test_pipeline_completeness_reflects_missing_feature_group(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = _candidate(earth_candidate, "EARTH_PARTIAL")
    candidate.pop("spatial_pattern_definition")
    candidate.pop("largest_steep_patch_pct")

    result = rank_terrain_fingerprints(
        target_fingerprint,
        {"EARTH_PARTIAL": candidate},
        get_mission_weights(),
        matching_tolerances,
        mission_profile="Rover Navigation",
    )

    ranked = result["ranking"][0]
    assert ranked["group_distances"]["spatial_pattern"] is None
    assert ranked["feature_group_completeness"] == 0.8
    assert ranked["data_completeness"] == 0.8
