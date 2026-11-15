from pathlib import Path
import subprocess
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin

from src.data.build_exploratory_pilot import (
    centered_bounds,
    read_native_window,
    resample_elevation,
    summarize_count_layer,
    matching,
    ranking_csv_rows,
)


def test_centered_bounds_returns_exact_square():
    assert centered_bounds(-100.0, 250.0, 990.0) == (
        -595.0, -245.0, 395.0, 745.0
    )


def test_count_summary_keeps_zero_ldec_separate_from_nodata():
    values = np.ma.array(
        [[0, 1, 0], [2, 0, 0]],
        mask=[[False, False, True], [False, False, False]],
    )
    result = summarize_count_layer(values)
    assert result["native_quality_total_cells"] == 6
    assert result["native_quality_valid_cells"] == 5
    assert result["native_quality_nodata_cells"] == 1
    assert result["ldec_positive_cells"] == 2
    assert result["ldec_zero_cells"] == 3
    assert result["direct_observation_coverage_pct"] == 40.0
    assert result["ldec_zero_count_pct"] == 60.0
    assert abs(result["ldec_nodata_pct"] - (100.0 / 6.0)) < 1e-9


def test_native_support_window_is_exact_and_pixel_aligned(tmp_path: Path):
    path = tmp_path / "native.tif"
    values = np.arange(36, dtype=np.float32).reshape(6, 6)
    values[0, 0] = -9999.0
    transform = from_origin(0.0, 30.0, 5.0, 5.0)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=6,
        height=6,
        count=1,
        dtype="float32",
        crs="EPSG:32616",
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(values, 1)

    reference = {
        "width": 6,
        "height": 6,
        "transform": transform,
        "crs": rasterio.crs.CRS.from_epsg(32616),
    }
    sample = read_native_window(
        path,
        (0.0, 0.0, 30.0, 30.0),
        reference_profile=reference,
        expected_shape=(6, 6),
    )
    assert sample.shape == (6, 6)
    assert int(np.ma.getmaskarray(sample).sum()) == 1


def test_resampling_uses_declared_projected_metre_grid(tmp_path: Path):
    path = tmp_path / "source.tif"
    values = np.arange(36, dtype=np.float32).reshape(6, 6)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=6,
        height=6,
        count=1,
        dtype="float32",
        crs="EPSG:32616",
        transform=from_origin(0.0, 30.0, 5.0, 5.0),
        nodata=None,
    ) as dst:
        dst.write(values, 1)

    output, transform, analysis_crs, metadata = resample_elevation(
        path,
        (0.0, 0.0, 30.0, 30.0),
        "EPSG:32616",
        3,
        3,
    )
    assert output.shape == (3, 3)
    assert np.isfinite(output).all()
    assert analysis_crs.to_epsg() == 32616
    assert transform.a == 10.0
    assert transform.e == -10.0
    assert metadata["resampling"] == "GDAL/Rasterio bilinear elevation resampling"


def test_builder_module_help_is_available():
    completed = subprocess.run(
        [sys.executable, "-m", "src.data.build_exploratory_pilot", "--help"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--raw-root" in completed.stdout
    assert "--config" in completed.stdout


def test_native_window_uses_pixel_centres_when_bounds_are_half_cell_shifted(tmp_path: Path):
    path = tmp_path / "half-cell.tif"
    values = np.arange(36, dtype=np.float32).reshape(6, 6)
    transform = from_origin(0.0, 30.0, 5.0, 5.0)
    crs = rasterio.crs.CRS.from_epsg(32616)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=6,
        height=6,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=None,
    ) as dst:
        dst.write(values, 1)

    reference = {"width": 6, "height": 6, "transform": transform, "crs": crs}
    # The requested bounds are shifted by half a 5m cell in Y. All selected
    # pixel centres still lie inside the intended footprint, even though cell
    # edge bounds are not numerically identical to the requested bounds.
    sample = read_native_window(
        path,
        (0.0, -2.5, 30.0, 27.5),
        reference_profile=reference,
        expected_shape=(6, 6),
    )
    assert sample.shape == (6, 6)
    assert np.isfinite(sample).all()


def test_pilot_matching_includes_tolerance_sensitivity(
    target_fingerprint, earth_candidate, matching_tolerances
):
    from src.matching.mission_profiles import (
        ROVER_NAVIGATION_PROFILE,
        get_mission_weights,
    )

    candidate = dict(earth_candidate)
    candidate["site_id"] = "EARTH_A"
    candidate["source_id"] = "DEM_A"
    config = {
        "target": {"site_id": target_fingerprint["site_id"]},
        "earth_candidates": [{"site_id": "EARTH_A"}],
        "matching": {
            "mission_profile": ROVER_NAVIGATION_PROFILE["name"],
            "weights": get_mission_weights(),
            "tolerances": matching_tolerances,
            "min_feature_group_completeness": 1.0,
            "min_data_completeness": 0.95,
            "scale_relative_tolerance": 0.01,
            "distribution_sum_tolerance_pp": 0.5,
            "weight_sensitivity_relative_change": 0.20,
        },
    }

    result, weight_sensitivity, tolerance_sensitivity = matching(
        {
            target_fingerprint["site_id"]: target_fingerprint,
            "EARTH_A": candidate,
        },
        config,
    )

    assert result["ranking"][0]["site_id"] == "EARTH_A"
    assert weight_sensitivity["weight_sensitivity"]["scenario_count"] == 11
    assert tolerance_sensitivity["scenario_count"] == 11
    assert tolerance_sensitivity["factors"] == [0.5, 1.0, 1.5]

    # The user-facing note must be computed from actual per-scenario ranks,
    # not a separately maintained count that could drift from the sidecar.
    tolerance_sensitivity["rank_by_scenario"] = {
        "baseline": {"EARTH_A": 1},
        "slope_0.5x": {"EARTH_A": 2},
        "slope_1.5x": {"EARTH_A": 1},
    }
    tolerance_sensitivity["scenario_count"] = 3
    csv_rows = ranking_csv_rows(
        result,
        weight_sensitivity,
        tolerance_sensitivity,
        {
            target_fingerprint["site_id"]: target_fingerprint,
            "EARTH_A": candidate,
        },
        config,
    )
    assert csv_rows[0]["tolerance_top1_scenarios"] == 2
    assert csv_rows[0]["tolerance_sensitivity_scenario_count"] == 3
    assert "tolerance Top-1 in 2/3" in csv_rows[0]["ranking_stability_note"]
    assert "undefined" not in csv_rows[0]["ranking_stability_note"]
