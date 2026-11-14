import pytest


@pytest.fixture
def matching_tolerances():
    # Illustrative test tolerances only; the team must approve real-study values.
    return {
        "slope_deg": 5.0,
        "tri_m": 2.0,
        "local_relief_m": 10.0,
        "terrain_distribution_pp": 10.0,
        "spatial_pattern_pct": 10.0,
    }


@pytest.fixture
def target_fingerprint():
    return {
        "site_id": "MOON_SITE04",
        "planet": "Moon",
        "source_id": "NASA_LOLA_SITE04",
        "analysis_scale_m": 20.0,
        "slope_unit": "degrees",
        "elevation_unit": "m",
        "slope_median": 10.0,
        "slope_p90": 20.0,
        "tri_median": 2.0,
        "tri_p90": 5.0,
        "tri_definition": "Riley eight-neighbour",
        "tri_window_cells": 1,
        "local_relief_p95_p5": 30.0,
        "relief_window_m": 100.0,
        "terrain_low_pct": 20.0,
        "terrain_mid_pct": 50.0,
        "terrain_high_pct": 30.0,
        "terrain_class_thresholds": "low:0-5;mid:5-15;high:>15 degrees",
        "largest_steep_patch_pct": 12.0,
        "spatial_pattern_definition": "largest connected high-slope patch; >15 deg; 8-neighbour",
        "nodata_pct": 0.0,
        "valid_coverage_pct": 100.0,
        "direct_observation_coverage_pct": 9.1541,
    }


@pytest.fixture
def earth_candidate(target_fingerprint):
    candidate = dict(target_fingerprint)
    candidate.update({
        "site_id": "EARTH_A",
        "planet": "Earth",
        "source_id": "EARTH_DEM_A",
        "nodata_pct": 5.0,
        "valid_coverage_pct": 95.0,
        "direct_observation_coverage_pct": 100.0,
    })
    return candidate
