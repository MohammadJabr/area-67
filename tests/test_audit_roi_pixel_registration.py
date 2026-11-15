import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from affine import Affine
from rasterio.transform import from_origin
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from audit_roi_pixel_registration import audit_shapefile_registration  # noqa: E402


def write_raster(path: Path, *, crs="EPSG:3031"):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="float32",
        crs=crs,
        transform=from_origin(0, 10, 1, 1),
    ) as dataset:
        dataset.write(np.zeros((10, 10), dtype="float32"), 1)
    return path


def write_shapefile(path: Path, geometry, *, crs="EPSG:3031"):
    frame = gpd.GeoDataFrame(
        {"label": ["test_roi"], "geometry": [geometry]},
        crs=crs,
    )
    frame.to_file(path)
    return path


def test_reports_vertices_aligned_to_pixel_centres(tmp_path):
    raster = write_raster(tmp_path / "reference.tif")
    shapefile = write_shapefile(
        tmp_path / "roi.shp",
        box(0.5, 8.5, 2.5, 9.5),
    )

    report = audit_shapefile_registration(shapefile, raster)

    assert report["status"] == "inventory_complete"
    assert report["summary"]["alignment_class"] == "pixel_centres"
    assert report["summary"]["vertex_count"] == 5
    assert report["summary"]["pixel_center_aligned_vertex_count"] == 5
    assert report["summary"]["pixel_center_aligned_pct"] == 100.0
    assert report["summary"]["maximum_pixel_center_residual_m"] <= 1e-12


def test_handles_rotated_and_sheared_affine_pixel_centres(tmp_path):
    transform = Affine(1.0, 0.2, 100.0, 0.1, -1.0, 200.0)
    raster_path = tmp_path / "sheared.tif"
    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="float32",
        crs="EPSG:3031",
        transform=transform,
    ) as dataset:
        dataset.write(np.zeros((10, 10), dtype="float32"), 1)

    ring = [
        transform @ (0.5, 0.5),
        transform @ (4.5, 0.5),
        transform @ (4.5, 4.5),
        transform @ (0.5, 4.5),
        transform * (0.5, 0.5),
    ]
    shapefile = write_shapefile(
        tmp_path / "sheared_roi.shp",
        Polygon(ring),
    )

    report = audit_shapefile_registration(shapefile, raster_path)

    assert report["summary"]["alignment_class"] == "pixel_centres"
    assert report["summary"]["pixel_center_aligned_pct"] == 100.0
    assert report["summary"]["maximum_pixel_center_residual_m"] == 0.0


def test_reports_vertices_aligned_to_pixel_corners(tmp_path):
    raster = write_raster(tmp_path / "reference.tif")
    shapefile = write_shapefile(
        tmp_path / "roi.shp",
        box(0.0, 8.0, 2.0, 10.0),
    )

    report = audit_shapefile_registration(shapefile, raster)

    assert report["summary"]["alignment_class"] == "pixel_corners"
    assert report["summary"]["pixel_corner_aligned_pct"] == 100.0


def test_reports_vertices_not_on_either_grid_lattice(tmp_path):
    raster = write_raster(tmp_path / "reference.tif")
    shapefile = write_shapefile(
        tmp_path / "roi.shp",
        box(0.25, 8.25, 2.25, 9.25),
    )

    report = audit_shapefile_registration(shapefile, raster)

    assert report["summary"]["alignment_class"] == "off_grid"
    assert report["summary"]["pixel_center_aligned_pct"] == 0.0
    assert report["summary"]["pixel_corner_aligned_pct"] == 0.0


def test_rejects_crs_mismatch_without_reprojecting(tmp_path):
    raster = write_raster(tmp_path / "reference.tif")
    shapefile = write_shapefile(
        tmp_path / "roi.shp",
        box(-1.0, -1.0, 1.0, 1.0),
        crs="EPSG:4326",
    )

    try:
        audit_shapefile_registration(shapefile, raster)
    except ValueError as exc:
        assert "not nominally compatible" in str(exc)
    else:
        raise AssertionError("Expected mismatched CRS to be rejected")


def test_rejects_nonmetre_projected_crs_when_reporting_metres(tmp_path):
    raster = write_raster(tmp_path / "reference.tif", crs="EPSG:2263")
    shapefile = write_shapefile(
        tmp_path / "roi.shp",
        box(0.5, 8.5, 2.5, 9.5),
        crs="EPSG:2263",
    )

    try:
        audit_shapefile_registration(shapefile, raster)
    except ValueError as exc:
        assert "requires a metre-based projected CRS" in str(exc)
    else:
        raise AssertionError("Expected non-metre CRS to be rejected")


def test_rejects_nonpositive_tolerance(tmp_path):
    raster = write_raster(tmp_path / "reference.tif")
    shapefile = write_shapefile(
        tmp_path / "roi.shp",
        box(0.5, 8.5, 2.5, 9.5),
    )

    try:
        audit_shapefile_registration(shapefile, raster, tolerance_m=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("Expected invalid tolerance to be rejected")
