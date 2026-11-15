import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from lola_roi_quality import ASSET_NAMES, build_roi_quality_report, same_crs  # noqa: E402


def write_site_rasters(folder: Path, *, crs="EPSG:3031", nodata_cell=False):
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    transform = from_origin(0, 10, 1, 1)
    arrays = {
        "elevation": np.arange(100, dtype="float32").reshape(10, 10) + 100,
        "counts": np.zeros((10, 10), dtype="float32"),
        "slope": np.full((10, 10), 10.0, dtype="float32"),
        "z_uncertainty": np.full((10, 10), 0.4, dtype="float32"),
        "slope_uncertainty": np.full((10, 10), 2.0, dtype="float32"),
    }
    arrays["counts"][5:7, 2:4] = 1.0
    if nodata_cell:
        arrays["elevation"][5, 1] = -9999
        arrays["counts"][5, 1] = -9999

    for name in ASSET_NAMES:
        path = folder / f"{name}.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=10,
            height=10,
            count=1,
            dtype="float32",
            crs=crs,
            transform=transform,
            nodata=-9999,
        ) as dataset:
            dataset.write(arrays[name], 1)
        paths[name] = path
    return paths


def write_rois(folder: Path, *, crs="EPSG:3031", geometries=None):
    folder.mkdir(parents=True, exist_ok=True)
    if geometries is None:
        geometries = [box(1, 1, 5, 5)]
    frame = gpd.GeoDataFrame(
        {"roi_label": [f"roi_{index}" for index in range(len(geometries))],
         "priority": list(range(1, len(geometries) + 1)),
         "geometry": geometries},
        crs=crs,
    )
    path = folder / "site_rois.shp"
    frame.to_file(path)
    return path


SITE04_SHAPEFILE_CRS_WKT = """PROJCS["unknown",GEOGCS["unknown",DATUM["unknown",SPHEROID["unknown",1737400,0]],PRIMEM["Reference meridian",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",-90],PARAMETER["central_meridian",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",NORTH],AXIS["Northing",NORTH]]"""

SITE04_RASTER_CRS_WKT = """PROJCS["unnamed",GEOGCS["unnamed ellipse",DATUM["unknown",SPHEROID["unnamed",1737400,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",-90],PARAMETER["central_meridian",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1],AXIS["Easting",NORTH],AXIS["Northing",NORTH]]"""


def test_same_crs_accepts_equivalent_lunar_polar_stereographic_wkt():
    assert same_crs(SITE04_SHAPEFILE_CRS_WKT, SITE04_RASTER_CRS_WKT)


def test_same_crs_rejects_different_lunar_projection_parameters():
    different_meridian = SITE04_SHAPEFILE_CRS_WKT.replace(
        'PARAMETER["central_meridian",0]',
        'PARAMETER["central_meridian",1]',
    )
    different_body_radius = SITE04_SHAPEFILE_CRS_WKT.replace(
        'SPHEROID["unknown",1737400,0]',
        'SPHEROID["unknown",1737401,0]',
    )

    assert not same_crs(SITE04_SHAPEFILE_CRS_WKT, different_meridian)
    assert not same_crs(SITE04_SHAPEFILE_CRS_WKT, different_body_radius)
    assert not same_crs("EPSG:4326", "EPSG:3857")


def test_roi_quality_audit_reports_support_and_uncertainty_by_polygon(tmp_path):
    raster_paths = write_site_rasters(tmp_path / "rasters")
    roi_dir = tmp_path / "roi"
    write_rois(roi_dir)

    report = build_roi_quality_report("Site04", roi_dir, raster_paths=raster_paths)

    assert report["status"] == "inventory_complete"
    assert report["feature_count"] == 1
    feature = report["shapefiles"][0]["features"][0]
    assert feature["roi_pixel_center_count"] == 16
    assert feature["elevation_valid_coverage_pct"] == 100.0
    assert feature["counts_valid_coverage_pct"] == 100.0
    assert feature["counts_positive_direct_support_pct"] == 25.0
    assert feature["counts_zero_interpolated_pct"] == 75.0
    assert feature["counts_negative_value_count"] == 0
    assert feature["z_uncertainty_median"] == pytest.approx(0.4)
    assert feature["slope_uncertainty_median"] == pytest.approx(2.0)
    assert feature["properties"]["roi_label"] == "roi_0"


def test_roi_quality_audit_keeps_nodata_separate_from_zero_ldec(tmp_path):
    raster_paths = write_site_rasters(tmp_path / "rasters", nodata_cell=True)
    roi_dir = tmp_path / "roi"
    write_rois(roi_dir)

    report = build_roi_quality_report("Site04", roi_dir, raster_paths=raster_paths)
    feature = report["shapefiles"][0]["features"][0]

    assert feature["roi_pixel_center_count"] == 16
    assert feature["elevation_valid_coverage_pct"] == pytest.approx(93.75)
    assert feature["counts_valid_coverage_pct"] == pytest.approx(93.75)
    assert feature["counts_positive_direct_support_pct"] == pytest.approx(4 / 15 * 100)
    assert feature["counts_zero_interpolated_pct"] == pytest.approx(11 / 15 * 100)
    assert feature["counts_invalid_or_missing_pixel_count"] == 1


def test_roi_quality_audit_fails_closed_on_mismatched_shape_crs(tmp_path):
    raster_paths = write_site_rasters(tmp_path / "rasters")
    roi_dir = tmp_path / "roi"
    write_rois(roi_dir, crs="EPSG:4326")

    report = build_roi_quality_report("Site04", roi_dir, raster_paths=raster_paths)

    assert report["status"] == "review_required"
    assert report["shapefiles"] == []
    assert any("CRS differs" in warning for warning in report["warnings"])


def test_roi_quality_audit_rejects_grid_mismatch(tmp_path):
    raster_paths = write_site_rasters(tmp_path / "rasters")
    slope_path = tmp_path / "rasters" / "misaligned_slope.tif"
    with rasterio.open(
        slope_path,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="float32",
        crs="EPSG:3031",
        transform=from_origin(0.5, 10, 1, 1),
        nodata=-9999,
    ) as dataset:
        dataset.write(np.ones((10, 10), dtype="float32"), 1)
    raster_paths["slope"] = slope_path
    roi_dir = tmp_path / "roi"
    write_rois(roi_dir)

    with pytest.raises(ValueError, match="grid does not exactly match"):
        build_roi_quality_report("Site04", roi_dir, raster_paths=raster_paths)


def test_roi_quality_audit_reports_roi_outside_raster(tmp_path):
    raster_paths = write_site_rasters(tmp_path / "rasters")
    roi_dir = tmp_path / "roi"
    write_rois(roi_dir, geometries=[box(100, 100, 110, 110)])

    report = build_roi_quality_report("Site04", roi_dir, raster_paths=raster_paths)
    feature = report["shapefiles"][0]["features"][0]

    assert report["status"] == "review_required"
    assert feature["status"] == "review_required"
    assert any("does not overlap" in warning for warning in feature["warnings"])


def test_roi_quality_audit_rejects_unknown_site_and_missing_directory(tmp_path):
    with pytest.raises(ValueError, match="Unknown site"):
        build_roi_quality_report("Site99", tmp_path)
    with pytest.raises(FileNotFoundError, match="ROI directory"):
        build_roi_quality_report("Site04", tmp_path / "missing")
