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
