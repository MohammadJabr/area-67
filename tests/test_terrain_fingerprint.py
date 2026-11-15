import json

import numpy as np
import pandas as pd
import pytest

from src.features.terrain_fingerprint import (
    TerrainConfig,
    analyze_geotiff,
    analyze_run_config,
    calculate_terrain_fingerprint,
)
from src.features.validation import compare_scale_runs, feature_correlation_audit, validate_fingerprint_rows


def config(scale=10.0, relief=40.0, **kwargs):
    # Synthetic tests declare the analytical support fraction explicitly.
    kwargs.setdefault("local_relief_min_valid_fraction", 0.8)
    return TerrainConfig(analysis_scale_m=scale, relief_window_m=relief, **kwargs)


def test_synthetic_flat_surface_has_zero_slope_tri_and_local_relief():
    z = np.full((31, 31), 125.0)
    metrics, maps = calculate_terrain_fingerprint(z, 10, 10, config())
    assert metrics["slope_median"] == pytest.approx(0.0, abs=1e-10)
    assert metrics["tri_median"] == pytest.approx(0.0, abs=1e-10)
    assert metrics["local_relief_p95_p5"] == pytest.approx(0.0, abs=1e-10)
    assert np.nanmax(maps["slope"]) == pytest.approx(0.0, abs=1e-10)


def test_synthetic_plane_returns_analytic_slope():
    rows, cols = np.indices((41, 41))
    dx = dy = 10.0
    a, b = 0.12, 0.05
    z = a * cols * dx + b * rows * dy
    metrics, maps = calculate_terrain_fingerprint(z, dx, dy, config())
    expected = np.degrees(np.arctan(np.hypot(a, b)))
    assert metrics["slope_median"] == pytest.approx(expected, abs=1e-10)
    assert metrics["slope_p90"] == pytest.approx(expected, abs=1e-10)
    assert np.nanmax(maps["slope"]) == pytest.approx(expected, abs=1e-10)


def test_riley_tri_is_positive_around_synthetic_bump_and_nan_at_edges():
    z = np.zeros((31, 31), dtype=float)
    z[15, 15] = 20.0
    metrics, maps = calculate_terrain_fingerprint(z, 10, 10, config())
    assert np.nanmax(maps["tri"]) > 0
    assert maps["tri"][15, 15] > 0
    assert np.isnan(maps["tri"][0, 0])


def test_nodata_is_not_interpolated_and_coverage_is_separately_counted():
    z = np.full((31, 31), 10.0)
    z[15, 15] = np.nan
    metrics, maps = calculate_terrain_fingerprint(z, 10, 10, config())
    assert metrics["valid_cell_count"] == 31 * 31 - 1
    assert np.isnan(maps["slope"][15, 15])
    assert np.isnan(maps["tri"][14, 14])
    # Local relief uses a moving neighbourhood, but an invalid centre must
    # remain NoData rather than receiving a value from surrounding cells.
    assert np.isnan(maps["local_relief"][15, 15])
    assert metrics["local_relief_valid_cell_count"] < metrics["valid_cell_count"]
    assert metrics["slope_valid_cell_count"] < metrics["valid_cell_count"]


def test_terrain_distribution_sums_to_one_hundred_percent():
    rows, cols = np.indices((51, 51))
    z = np.where(cols < 17, 0.0, np.where(cols < 34, rows * 2.0, rows * 10.0))
    metrics, _ = calculate_terrain_fingerprint(z, 10, 10, config())
    assert metrics["slope_distribution_sum_pct"] == pytest.approx(100.0, abs=1e-9)
    assert sum(metrics[k] for k in ("terrain_low_pct", "terrain_mid_pct", "terrain_high_pct")) == pytest.approx(100.0)


def test_spatial_pattern_distinguishes_one_connected_patch_from_separated_patches():
    rows, cols = np.indices((61, 61))
    # A constant-gradient plane creates a connected high-slope region; a stepped
    # elevation surface creates multiple separated steep boundaries.
    one_patch = (cols * 10.0).astype(float)
    metrics_a, _ = calculate_terrain_fingerprint(
        one_patch, 10, 10, config(steep_threshold_deg=30, slope_low_max_deg=10, slope_mid_max_deg=25)
    )
    stripes = np.where((cols % 12) < 2, rows * 8.0, 0.0)
    metrics_b, _ = calculate_terrain_fingerprint(
        stripes, 10, 10, config(steep_threshold_deg=30, slope_low_max_deg=10, slope_mid_max_deg=25)
    )
    assert metrics_a["largest_steep_patch_pct"] > metrics_b["largest_steep_patch_pct"]


def test_analysis_scale_mismatch_is_rejected():
    with pytest.raises(ValueError, match="pixel dimensions do not match"):
        calculate_terrain_fingerprint(np.zeros((20, 20)), 30, 30, config(scale=10))


def test_relief_window_records_actual_odd_kernel_and_span():
    metrics, _ = calculate_terrain_fingerprint(np.zeros((31, 31)), 10, 10, config(relief=40))
    assert metrics["relief_window_cells"] == 5
    assert metrics["relief_window_span_m"] == 40


def test_feature_contract_rejects_scale_or_percentage_inconsistency():
    row = {
        "site_id": "X", "planet": "Moon", "source_id": "SRC",
        "analysis_scale_m": 10, "relief_window_m": 40, "nodata_pct": 0,
        "valid_coverage_pct": 100, "slope_unit": "degrees", "slope_median": 1,
        "slope_p90": 2, "tri_definition": "Riley", "tri_window_cells": 1,
        "tri_median": 1, "local_relief_p95_p5": 3, "terrain_class_thresholds": "test",
        "terrain_low_pct": 40, "terrain_mid_pct": 40, "terrain_high_pct": 20,
        "spatial_pattern_definition": "largest patch", "largest_steep_patch_pct": 5,
    }
    assert validate_fingerprint_rows(pd.DataFrame([row])) == []
    row["terrain_high_pct"] = 30
    assert any("sum to approximately 100" in e for e in validate_fingerprint_rows(pd.DataFrame([row])))


def test_correlation_audit_does_not_claim_correlations_for_fewer_than_three_sites():
    result = feature_correlation_audit(pd.DataFrame({"slope_median": [1, 2], "tri_median": [2, 3]}))
    assert result["status"] == "insufficient_sites"


def test_resolution_sensitivity_reports_change_without_claiming_validation():
    fine = {"site_id": "S1", "analysis_scale_m": 10, "slope_median": 10.0}
    coarse = {"site_id": "S1", "analysis_scale_m": 30, "slope_median": 12.0}
    result = compare_scale_runs(fine, coarse, metrics=["slope_median"])
    assert result.loc[0, "absolute_change_coarse_minus_fine"] == 2.0
    assert result.loc[0, "relative_change_pct_vs_fine"] == 20.0


def test_geotiff_aoi_pipeline_writes_contract_ready_metrics(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin

    dem_path = tmp_path / "plane.tif"
    aoi_path = tmp_path / "aoi.geojson"
    rows, cols = np.indices((31, 31))
    elevation = (0.1 * cols * 10.0).astype(np.float32)
    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        height=elevation.shape[0],
        width=elevation.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:32631",
        transform=from_origin(500000, 1000, 10, 10),
        nodata=-9999,
    ) as dataset:
        dataset.write(elevation, 1)

    aoi = {
        "type": "Polygon",
        "coordinates": [[[500010, 990], [500290, 990], [500290, 990-280], [500010, 990-280], [500010, 990]]],
    }
    aoi_path.write_text(__import__("json").dumps(aoi), encoding="utf-8")
    site = {
        "site_id": "TEST_EARTH", "planet": "Earth", "source_id": "SYNTHETIC_TEST",
        "site_name": "Synthetic test site", "elevation_unit": "m", "aoi_crs": "EPSG:32631",
        "vertical_reference": "Synthetic local datum", "effective_resolution_note": "Synthetic grid",
        "quality_layer": "Synthetic quality mask", "direct_observation_coverage_pct": 9.1541,
    }
    result = analyze_geotiff(
        dem_path, aoi_path, site, config(scale=10, relief=40), write_maps_to=tmp_path / "maps"
    )
    assert result["site_id"] == "TEST_EARTH"
    assert result["analysis_scale_m"] == 10
    assert result["valid_coverage_pct"] == pytest.approx(100)
    assert result["nodata_pct"] == pytest.approx(0)
    assert result["slope_median"] == pytest.approx(np.degrees(np.arctan(0.1)), abs=1e-5)
    assert validate_fingerprint_rows(pd.DataFrame([result])) == []
    assert result["direct_observation_coverage_pct"] == pytest.approx(9.1541)
    assert result["quality_status"] == "REVIEW"
    assert "low_direct_observation_support_review_required" not in result["quality_flags"]
    assert (tmp_path / "maps" / "TEST_EARTH" / "TEST_EARTH_slope.tif").exists()


def test_geotiff_pipeline_rejects_unprojected_degree_grid(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin
    import json

    dem_path = tmp_path / "geographic.tif"
    aoi_path = tmp_path / "aoi.geojson"
    with rasterio.open(
        dem_path, "w", driver="GTiff", height=10, width=10, count=1,
        dtype="float32", crs="EPSG:4326", transform=from_origin(0, 1, 0.0001, 0.0001),
    ) as dataset:
        dataset.write(np.ones((10, 10), dtype=np.float32), 1)
    aoi_path.write_text(json.dumps({"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}),encoding="utf-8")
    site = {"site_id":"BAD_GRID","planet":"Earth","source_id":"TEST","elevation_unit":"m","vertical_reference":"Unknown for CRS validation test"}
    with pytest.raises(ValueError, match="projected metric CRS"):
        analyze_geotiff(dem_path,aoi_path,site,config(scale=10,relief=40))


def test_geotiff_pipeline_requires_explicit_vertical_reference():
    with pytest.raises(ValueError, match="explicit vertical_reference"):
        analyze_geotiff(
            "not-needed.tif",
            "not-needed.geojson",
            {"site_id": "X", "planet": "Earth", "source_id": "SRC"},
            config(),
        )


def test_geotiff_pipeline_accepts_integer_elevation_raster(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    import json
    from rasterio.transform import from_origin

    dem_path = tmp_path / "integer_dem.tif"
    aoi_path = tmp_path / "integer_aoi.geojson"
    rows, cols = np.indices((21, 21))
    elevation = cols.astype(np.int16)
    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        height=elevation.shape[0],
        width=elevation.shape[1],
        count=1,
        dtype="int16",
        crs="EPSG:32631",
        transform=from_origin(500000, 1000, 10, 10),
        nodata=-32768,
    ) as dataset:
        dataset.write(elevation, 1)

    aoi = {
        "type": "Polygon",
        "coordinates": [[[500010, 990], [500190, 990], [500190, 810], [500010, 810], [500010, 990]]],
    }
    aoi_path.write_text(json.dumps(aoi), encoding="utf-8")
    site = {
        "site_id": "INTEGER_EARTH",
        "planet": "Earth",
        "source_id": "SYNTHETIC_INT16",
        "elevation_unit": "m",
        "aoi_crs": "EPSG:32631",
        "vertical_reference": "Synthetic local datum",
        "quality_layer": "Synthetic mask",
        "effective_resolution_note": "Synthetic 10 m integer grid",
    }
    result = analyze_geotiff(dem_path, aoi_path, site, config(scale=10, relief=40))
    assert result["slope_median"] == pytest.approx(np.degrees(np.arctan(0.1)), abs=1e-5)
    assert result["valid_coverage_pct"] == pytest.approx(100.0)


def test_local_relief_support_fraction_cannot_be_omitted():
    with pytest.raises(ValueError, match="must be explicitly set"):
        TerrainConfig(
            analysis_scale_m=10,
            relief_window_m=40,
            local_relief_min_valid_fraction=None,
        ).validate()


@pytest.mark.parametrize(
    ("coverage_setting", "expected_threshold"),
    [
        ("omitted", None),
        ("null", None),
        ("explicit", 85.0),
    ],
)
def test_run_config_preserves_optional_minimum_coverage_threshold(
    tmp_path, monkeypatch, coverage_setting, expected_threshold
):
    from src.features import terrain_fingerprint as fingerprint_module

    document = {
        "analysis_scale_m": 10,
        "relief_window_m": 40,
        "local_relief_min_valid_fraction": 0.8,
        "sites": [
            {
                "site_id": "TEST_MOON",
                "planet": "Moon",
                "source_id": "SYNTHETIC_TEST",
                "dem_path": "unused-dem.tif",
                "aoi_path": "unused-aoi.geojson",
            }
        ],
    }
    if coverage_setting == "null":
        document["minimum_valid_coverage_pct"] = None
    elif coverage_setting == "explicit":
        document["minimum_valid_coverage_pct"] = expected_threshold

    config_path = tmp_path / "terrain_run.json"
    output_path = tmp_path / "terrain_fingerprints.csv"
    config_path.write_text(json.dumps(document), encoding="utf-8")

    captured = []

    def fake_analyze_geotiff(dem_path, aoi_path, site, run_config, write_maps_to=None):
        captured.append(run_config)
        return {
            "site_id": "TEST_MOON",
            "planet": "Moon",
            "source_id": "SYNTHETIC_TEST",
            "analysis_scale_m": 10.0,
            "nodata_pct": 0.0,
            "valid_coverage_pct": 100.0,
            "slope_unit": "degrees",
            "slope_median": 1.0,
            "slope_p90": 2.0,
            "tri_definition": "Riley eight-neighbour",
            "tri_window_cells": 1,
            "tri_median": 1.0,
            "relief_window_m": 40.0,
            "local_relief_p95_p5": 3.0,
            "terrain_class_thresholds": "low < 10; mid 10-25; high >= 25",
            "terrain_low_pct": 40.0,
            "terrain_mid_pct": 40.0,
            "terrain_high_pct": 20.0,
            "spatial_pattern_definition": "largest connected steep patch",
            "largest_steep_patch_pct": 5.0,
        }

    monkeypatch.setattr(fingerprint_module, "analyze_geotiff", fake_analyze_geotiff)

    analyze_run_config(config_path, output_path)

    assert len(captured) == 1
    assert captured[0].minimum_valid_coverage_pct == expected_threshold
    assert output_path.is_file()


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"analysis_scale_m": 0}, "analysis_scale_m"),
        ({"relief_window_m": float("nan")}, "relief_window_m"),
        ({"local_relief_min_valid_fraction": 0}, "local_relief_min_valid_fraction"),
        ({"connectivity": 6}, "connectivity"),
        ({"steep_threshold_deg": 91}, "steep_threshold_deg"),
        ({"minimum_valid_coverage_pct": 101}, "minimum_valid_coverage_pct"),
    ],
)
def test_terrain_config_rejects_invalid_physical_or_threshold_settings(overrides, message):
    values = {
        "analysis_scale_m": 10.0,
        "relief_window_m": 40.0,
        "local_relief_min_valid_fraction": 0.8,
    }
    values.update(overrides)
    with pytest.raises(ValueError, match=message):
        TerrainConfig(**values).validate()


def test_all_derived_maps_preserve_source_nodata_mask():
    z = np.full((25, 25), 50.0)
    z[12, 12] = np.nan
    _, maps = calculate_terrain_fingerprint(z, 10, 10, config())
    for name, layer in maps.items():
        assert np.isnan(layer[12, 12]), f"{name} must preserve the source NoData centre"


def test_terrain_class_threshold_boundaries_are_documented_and_applied():
    # The output contract uses low < 10°, mid 10–25°, high >= 25°.
    # A plane with a 0.1763 rise/run gradient is approximately 10°.
    rows, cols = np.indices((41, 41))
    z = np.where(cols < 14, 0.0, np.where(cols < 27, rows * 1.7633, rows * 4.6631))
    metrics, _ = calculate_terrain_fingerprint(
        z, 10, 10, config(steep_threshold_deg=25.0)
    )
    assert metrics["terrain_class_thresholds"] == (
        "low < 10; mid >= 10 and < 25; high >= 25 degrees"
    )
    assert metrics["slope_distribution_sum_pct"] == pytest.approx(100.0, abs=1e-9)
