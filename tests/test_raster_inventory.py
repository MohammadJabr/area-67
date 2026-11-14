import hashlib

import numpy as np
import rasterio
from rasterio.transform import from_origin

from src.data.earth_dem_qa import build_qa_report, markdown_report
from src.data.raster_inventory import inventory_many, inventory_raster


def write_raster(path, data, *, transform=None, crs="EPSG:32610", nodata=-9999):
    data = np.asarray(data, dtype="float32")
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=data.shape[1],
        height=data.shape[0],
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform or from_origin(500000, 4100000, 10, 10),
        nodata=nodata,
    ) as dataset:
        dataset.write(data, 1)


def test_inventory_reports_grid_mask_statistics_and_checksum(tmp_path):
    path = tmp_path / "synthetic_dem.tif"
    write_raster(path, [[1, 2], [3, -9999]])
    report = inventory_raster(path)

    assert report["width"] == report["height"] == 2
    assert report["crs"] == "EPSG:32610"
    assert report["pixel_size_x"] == report["pixel_size_y"] == 10
    assert report["bands"][0]["statistics"]["valid_pixel_count"] == 3
    assert report["bands"][0]["statistics"]["valid_coverage_pct"] == 75
    assert report["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_inventory_counts_nonfinite_values_even_without_nodata_mask(tmp_path):
    path = tmp_path / "nan_dem.tif"
    write_raster(path, [[1, np.nan], [3, 4]], nodata=-9999)
    report = inventory_raster(path, checksum=False)

    assert report["sha256"] is None
    assert report["bands"][0]["nonfinite_pixel_count"] == 1
    assert report["bands"][0]["statistics"]["valid_pixel_count"] == 3


def test_optional_quality_grid_alignment_and_configured_range_screen(tmp_path):
    dem = tmp_path / "dem.tif"
    quality = tmp_path / "quality.tif"
    write_raster(dem, [[-10, 10], [20, 30]])
    write_raster(quality, [[1, 1], [0, 1]])

    report = build_qa_report(dem, {"mask": quality}, elevation_range=(0, 25))
    assert report["status"] == "checks_passed"
    assert report["quality_layers"][0]["grid_aligned_with_dem"]
    assert report["dem"]["bands"][0]["configured_range_screen"]["outside_pixel_count"] == 2
    assert "not a universal physical validity threshold" in report["dem"]["bands"][0]["configured_range_screen"]["interpretation"]
    assert "Vertical datum" in markdown_report(report)


def test_misaligned_quality_grid_is_reported_as_review_required(tmp_path):
    dem = tmp_path / "dem.tif"
    quality = tmp_path / "misaligned_quality.tif"
    write_raster(dem, [[1, 2], [3, 4]])
    write_raster(quality, [[1, 1], [1, 1]], transform=from_origin(500010, 4100000, 10, 10))

    report = build_qa_report(dem, {"uncertainty": quality}, checksum=False)
    assert report["status"] == "review_required"
    assert report["quality_layers"][0]["grid_aligned_with_dem"] is False
    assert any("does not exactly match" in warning for warning in report["warnings"])


def test_inventory_many_reports_grid_mismatch(tmp_path):
    first = tmp_path / "first.tif"
    second = tmp_path / "second.tif"
    write_raster(first, [[1, 2], [3, 4]])
    write_raster(second, [[1, 2], [3, 4]], transform=from_origin(500010, 4100000, 10, 10))

    report = inventory_many([first, second], checksum=False)
    assert report["raster_count"] == 2
    assert report["rasters"][0]["grid_matches_first_raster"] is True
    assert report["rasters"][1]["grid_matches_first_raster"] is False
