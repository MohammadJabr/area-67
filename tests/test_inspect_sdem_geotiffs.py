import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from inspect_sdem_geotiffs import raster_metadata, same_grid  # noqa: E402


def write_raster(path, *, transform=None, crs="EPSG:4326", width=4, height=3):
    if transform is None:
        transform = from_origin(10, 20, 0.01, 0.01)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype="uint8",
        crs=crs,
        transform=transform,
        nodata=255,
    ) as dataset:
        dataset.write(np.ones((height, width), dtype="uint8"), 1)
        dataset.update_tags(TEST_TAG="header-only-test")


def test_reads_header_metadata_and_tags(tmp_path):
    path = tmp_path / "sample.tif"
    write_raster(path)

    metadata = raster_metadata(path)

    assert metadata["width"] == 4
    assert metadata["height"] == 3
    assert metadata["band_count"] == 1
    assert metadata["crs"] == "EPSG:4326"
    assert metadata["nodata"] == 255
    assert metadata["dataset_tags"]["TEST_TAG"] == "header-only-test"
    assert metadata["bounds"]["left"] == 10


def test_same_grid_requires_equal_crs_shape_and_transform(tmp_path):
    first = tmp_path / "first.tif"
    aligned = tmp_path / "aligned.tif"
    shifted = tmp_path / "shifted.tif"
    write_raster(first)
    write_raster(aligned)
    write_raster(shifted, transform=from_origin(10.01, 20, 0.01, 0.01))

    reference = raster_metadata(first)
    assert same_grid(reference, raster_metadata(aligned))
    assert not same_grid(reference, raster_metadata(shifted))


def test_compare_grids_explains_resolution_and_extent_differences():
    from inspect_sdem_geotiffs import compare_grids

    reference = {
        "crs_wkt": "same-crs",
        "width": 3200,
        "height": 3200,
        "resolution": [5.0, 5.0],
        "bounds": {"left": -19000.0, "bottom": -20000.0, "right": -3000.0, "top": -4000.0},
        "transform": [5.0, 0.0, -19000.0, 0.0, -5.0, -4000.0, 0.0, 0.0, 1.0],
    }
    companion = {
        "crs_wkt": "same-crs",
        "width": 1066,
        "height": 1066,
        "resolution": [15.0, 15.0],
        "bounds": {"left": -19000.0, "bottom": -19990.0, "right": -3010.0, "top": -4000.0},
        "transform": [15.0, 0.0, -19000.0, 0.0, -15.0, -4000.0, 0.0, 0.0, 1.0],
    }

    result = compare_grids(reference, companion)

    assert result["same_crs"] is True
    assert result["same_resolution"] is False
    assert result["same_extent_within_tolerance"] is False
    assert result["max_absolute_bound_delta_m"] == 10.0
    assert result["same_grid"] is False
