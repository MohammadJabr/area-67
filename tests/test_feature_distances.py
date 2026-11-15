import copy
import math
import pytest

from src.matching.feature_distances import compare_terrain_fingerprints


def test_identical_fingerprints_have_zero_group_distances(
    target_fingerprint, earth_candidate, matching_tolerances
):
    result = compare_terrain_fingerprints(
        target_fingerprint, earth_candidate, matching_tolerances
    )

    assert result["group_distances"] == {
        "slope": 0.0,
        "tri": 0.0,
        "local_relief": 0.0,
        "terrain_distribution": 0.0,
        "spatial_pattern": 0.0,
    }
    assert result["missing_groups"] == []
    assert result["valid_raster_coverage_completeness"] == 0.95


def test_each_group_distance_uses_its_declared_tolerance(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate.update({
        "slope_median": 15.0,
        "slope_p90": 25.0,
        "tri_median": 4.0,
        "tri_p90": 7.0,
        "local_relief_p95_p5": 40.0,
        "terrain_low_pct": 30.0,
        "terrain_mid_pct": 40.0,
        "terrain_high_pct": 30.0,
        "largest_steep_patch_pct": 22.0,
    })

    result = compare_terrain_fingerprints(
        target_fingerprint, candidate, matching_tolerances
    )
    distances = result["group_distances"]

    assert math.isclose(distances["slope"], 1.0)
    assert math.isclose(distances["tri"], 1.0)
    assert math.isclose(distances["local_relief"], 1.0)
    assert math.isclose(distances["terrain_distribution"], math.sqrt(2 / 3))
    assert math.isclose(distances["spatial_pattern"], 1.0)


def test_missing_required_metric_marks_group_missing_not_zero(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate["tri_p90"] = None

    result = compare_terrain_fingerprints(
        target_fingerprint, candidate, matching_tolerances
    )

    assert result["group_distances"]["tri"] is None
    assert "tri" in result["missing_groups"]


def test_missing_method_metadata_marks_dependent_group_missing(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate.pop("relief_window_m")

    result = compare_terrain_fingerprints(
        target_fingerprint, candidate, matching_tolerances
    )

    assert result["group_distances"]["local_relief"] is None
    assert "local_relief" in result["missing_groups"]
    assert any("relief_window_m" in warning for warning in result["method_warnings"])


def test_incompatible_tri_definition_is_rejected(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate["tri_definition"] = "different TRI method"

    with pytest.raises(ValueError, match="Incompatible tri_definition"):
        compare_terrain_fingerprints(
            target_fingerprint, candidate, matching_tolerances
        )


def test_incompatible_analysis_scales_are_rejected(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate["analysis_scale_m"] = 40.0

    with pytest.raises(ValueError, match="Incompatible analysis scales"):
        compare_terrain_fingerprints(
            target_fingerprint, candidate, matching_tolerances
        )


def test_distribution_labels_are_not_silently_reinterpreted(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    for field in ("terrain_low_pct", "terrain_mid_pct", "terrain_high_pct"):
        candidate.pop(field)
    candidate.update({
        "terrain_flat_pct": 20.0,
        "terrain_moderate_pct": 50.0,
        "terrain_steep_pct": 30.0,
    })

    with pytest.raises(ValueError, match="class labels differ"):
        compare_terrain_fingerprints(
            target_fingerprint, candidate, matching_tolerances
        )


def test_distribution_percentages_must_sum_to_100(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate["terrain_high_pct"] = 50.0

    with pytest.raises(ValueError, match="must sum to 100"):
        compare_terrain_fingerprints(
            target_fingerprint, candidate, matching_tolerances
        )


def test_slope_and_elevation_units_are_converted_to_common_units(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate.update({
        "slope_unit": "radians",
        "slope_median": math.radians(10.0),
        "slope_p90": math.radians(20.0),
        "elevation_unit": "ft",
        "tri_median": 2.0 / 0.3048,
        "tri_p90": 5.0 / 0.3048,
        "local_relief_p95_p5": 30.0 / 0.3048,
    })

    result = compare_terrain_fingerprints(
        target_fingerprint, candidate, matching_tolerances
    )

    assert math.isclose(result["group_distances"]["slope"], 0.0, abs_tol=1e-12)
    assert math.isclose(result["group_distances"]["tri"], 0.0, abs_tol=1e-12)
    assert math.isclose(result["group_distances"]["local_relief"], 0.0, abs_tol=1e-12)


def test_lola_instrument_support_is_separate_from_nodata_coverage(
    target_fingerprint, earth_candidate, matching_tolerances
):
    result = compare_terrain_fingerprints(
        target_fingerprint, earth_candidate, matching_tolerances
    )

    assert result["target_direct_observation_coverage_pct"] == 9.1541
    assert result["target_valid_coverage_pct"] == 100.0
    assert result["valid_raster_coverage_completeness"] == 0.95


def test_non_earth_candidate_is_rejected(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate["planet"] = "Moon"

    with pytest.raises(ValueError, match="Earth candidate"):
        compare_terrain_fingerprints(
            target_fingerprint, candidate, matching_tolerances
        )

def test_missing_both_tri_method_fields_reports_both_warnings(
    target_fingerprint, earth_candidate, matching_tolerances
):
    candidate = dict(earth_candidate)
    candidate.pop("tri_definition")
    candidate.pop("tri_window_cells")

    result = compare_terrain_fingerprints(
        target_fingerprint, candidate, matching_tolerances
    )

    assert result["group_distances"]["tri"] is None
    assert "tri" in result["missing_groups"]
    warning_text = " ".join(result["method_warnings"])
    assert "tri_definition" in warning_text
    assert "tri_window_cells" in warning_text
