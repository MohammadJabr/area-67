from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from affine import Affine
from pyproj import CRS
from rasterio.transform import from_origin
from shapely.geometry import Polygon, box

from src.data.screen_lola_roi_candidates import (
    ASSETS,
    compare_roi_raster_crs,
    numeric_stats,
    read_candidate,
    roi_window,
)


def _write_layers(directory: Path, *, crs="EPSG:3857", shifted_layer: str | None = None):
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    transform = from_origin(0, 20, 5, 5)
    for name in ASSETS:
        path = directory / f"{name}.tif"
        layer_transform = transform
        if name == shifted_layer:
            layer_transform = from_origin(5, 20, 5, 5)
        data = np.arange(16, dtype=np.float32).reshape(4, 4)
        if name == "counts":
            data = np.array(
                [[0, 1, 0, 1], [1, 0, 0, 1], [0, 0, 1, 0], [1, 0, 1, 0]],
                dtype=np.float32,
            )
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=4,
            height=4,
            count=1,
            dtype="float32",
            crs=crs,
            transform=layer_transform,
            nodata=-9999.0,
        ) as dst:
            dst.write(data, 1)
        paths[name] = path
    return paths


def test_numeric_stats_ignores_nonfinite_values():
    stats = numeric_stats(np.array([1.0, 2.0, np.nan, np.inf]), "m")
    assert stats["valid_n"] == 2
    assert stats["min"] == 1.0
    assert stats["max"] == 2.0
    assert stats["median_p50"] == 1.5


def test_crs_comparison_accepts_exact_match():
    result = compare_roi_raster_crs("EPSG:3857", "EPSG:3857")
    assert result["crs_objects_equal"] is True
    assert result["physical_moon_fixed_frame_resolved"] is False


def test_crs_comparison_accepts_same_polar_stereographic_math_with_different_encoding():
    raster = CRS.from_proj4(
        "+proj=stere +lat_0=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m"
    )
    roi = CRS.from_proj4(
        "+proj=stere +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m"
    )
    result = compare_roi_raster_crs(roi, raster)
    assert result["crs_objects_equal"] is False
    assert result["nominal_polar_stereographic_parameters_equal"] is True
    assert result["physical_moon_fixed_frame_resolved"] is False
    assert "do not resolve" in result["warning"]


def test_crs_comparison_rejects_unrelated_coordinate_systems():
    with pytest.raises(ValueError, match="do not match"):
        compare_roi_raster_crs("EPSG:32636", "EPSG:3857")


def test_crs_comparison_rejects_geographic_coordinates_even_when_equal():
    with pytest.raises(ValueError, match="projected in metres"):
        compare_roi_raster_crs("EPSG:4326", "EPSG:4326")


def test_crs_comparison_rejects_different_standard_parallel_and_scale():
    reference = CRS.from_proj4(
        "+proj=stere +lat_0=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +k=1 +units=m"
    )
    different_parallel = CRS.from_proj4(
        "+proj=stere +lat_ts=-80 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m"
    )
    different_scale = CRS.from_proj4(
        "+proj=stere +lat_0=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +k=0.9 +units=m"
    )
    with pytest.raises(ValueError, match="do not match"):
        compare_roi_raster_crs(reference, different_parallel)
    with pytest.raises(ValueError, match="do not match"):
        compare_roi_raster_crs(reference, different_scale)


def test_read_candidate_reports_native_layer_coverage(tmp_path):
    paths = _write_layers(tmp_path / "rasters")
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[box(5, 5, 15, 15)], crs="EPSG:3857")

    result = read_candidate("Synthetic", 0, gdf, paths)

    assert result["pixel_center_sample_n"] == 4
    assert all(
        layer["valid_pct_of_roi_pixel_centers"] == 100.0
        for layer in result["layer_coverage"].values()
    )
    assert result["lola_direct_support"]["positive_count_n"] == 1
    assert result["crs_screening"]["crs_objects_equal"] is True


def test_read_candidate_rejects_mismatched_roi_crs(tmp_path):
    paths = _write_layers(tmp_path / "rasters")
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[box(5, 5, 15, 15)], crs="EPSG:32636")

    with pytest.raises(ValueError, match="do not match"):
        read_candidate("Synthetic", 0, gdf, paths)


def test_read_candidate_rejects_misaligned_raster_layer(tmp_path):
    paths = _write_layers(tmp_path / "rasters", shifted_layer="slope")
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[box(5, 5, 15, 15)], crs="EPSG:3857")

    with pytest.raises(ValueError, match="does not exactly match elevation"):
        read_candidate("Synthetic", 0, gdf, paths)


def test_read_candidate_rejects_invalid_source_geometry(tmp_path):
    paths = _write_layers(tmp_path / "rasters")
    bow_tie = Polygon([(5, 5), (15, 15), (5, 15), (15, 5), (5, 5)])
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[bow_tie], crs="EPSG:3857")

    with pytest.raises(ValueError, match="invalid, empty, or missing geometry"):
        read_candidate("Synthetic", 0, gdf, paths)


def test_roi_window_rejects_sheared_grid(tmp_path):
    path = tmp_path / "sheared.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype="float32",
        crs="EPSG:3857",
        transform=Affine(5, 1, 0, 0, -5, 20),
    ) as dst:
        dst.write(np.ones((4, 4), dtype=np.float32), 1)

    with rasterio.open(path) as src:
        with pytest.raises(ValueError, match="north-up, non-rotated"):
            roi_window((5, 5, 15, 15), src)
