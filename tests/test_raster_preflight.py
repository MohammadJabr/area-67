import numpy as np
import rasterio
from rasterio.transform import Affine, from_origin

from src.data.raster_preflight import preflight_raster


def write_dem(path, *, crs="EPSG:32631", transform=None, nodata=-9999, count=1):
    values = np.arange(36, dtype="float32").reshape(6, 6)
    with rasterio.open(
        path, "w", driver="GTiff", width=6, height=6, count=count,
        dtype="float32", crs=crs, transform=transform or from_origin(500000, 1000, 10, 10),
        nodata=nodata,
    ) as ds:
        for band in range(1, count + 1):
            ds.write(values, band)


def check(report, name):
    return next(item for item in report["checks"] if item["name"] == name)


def test_valid_projected_raster_passes_structural_preflight(tmp_path):
    path = tmp_path / "valid.tif"
    write_dem(path)
    report = preflight_raster(path, elevation_unit="m", vertical_reference="Synthetic test datum",
                              require_projected_metre_grid=True)

    assert report["status"] == "PASS"
    assert report["scientific_approval"] is False
    assert check(report, "mask_support")["value"]["valid_coverage_pct"] == 100
    assert check(report, "horizontal_grid")["status"] == "PASS"


def test_missing_product_metadata_is_review_not_inferred(tmp_path):
    path = tmp_path / "metadata_missing.tif"
    write_dem(path, crs="EPSG:4326", transform=from_origin(-16.8, 65.1, 0.001, 0.001))
    report = preflight_raster(path)

    assert report["status"] == "REVIEW"
    assert check(report, "horizontal_grid")["status"] == "REVIEW"
    assert check(report, "elevation_unit")["status"] == "REVIEW"
    assert check(report, "vertical_reference")["status"] == "REVIEW"


def test_strict_projected_metre_requirement_fails_geographic_grid(tmp_path):
    path = tmp_path / "geographic.tif"
    write_dem(path, crs="EPSG:4326", transform=from_origin(-16.8, 65.1, 0.001, 0.001))
    report = preflight_raster(path, require_projected_metre_grid=True)

    assert report["status"] == "FAIL"
    assert check(report, "horizontal_grid")["status"] == "FAIL"


def test_rotated_transform_fails_and_no_data_support_is_counted(tmp_path):
    path = tmp_path / "rotated.tif"
    rotated = Affine(10, 1, 500000, 0, -10, 1000)
    values = np.arange(36, dtype="float32").reshape(6, 6)
    values[0, 0] = -9999
    with rasterio.open(path, "w", driver="GTiff", width=6, height=6, count=1,
                       dtype="float32", crs="EPSG:32631", transform=rotated, nodata=-9999) as ds:
        ds.write(values, 1)
    report = preflight_raster(path)

    assert report["status"] == "FAIL"
    assert check(report, "transform_rotation")["status"] == "FAIL"
    assert check(report, "mask_support")["value"]["valid_pixels"] == 35
    assert check(report, "mask_support")["value"]["invalid_pixels"] == 1


def test_missing_crs_fails_preflight(tmp_path):
    path = tmp_path / "no_crs.tif"
    write_dem(path, crs=None)
    report = preflight_raster(path)

    assert report["status"] == "FAIL"
    assert check(report, "crs")["status"] == "FAIL"


def test_reversed_axis_orientation_fails(tmp_path):
    path = tmp_path / "reversed.tif"
    write_dem(path, transform=Affine(-10, 0, 500060, 0, 10, 940))
    report = preflight_raster(path)

    assert report["status"] == "FAIL"
    assert check(report, "orientation")["status"] == "FAIL"


def test_quality_grid_misalignment_is_reported_as_review(tmp_path):
    dem = tmp_path / "dem.tif"
    quality = tmp_path / "quality.tif"
    write_dem(dem)
    write_dem(quality, transform=from_origin(500010, 1000, 10, 10))

    report = preflight_raster(dem, quality_paths={"uncertainty": quality})

    assert report["quality_layers"][0]["status"] == "REVIEW"
    assert report["quality_layers"][0]["grid_aligned"] is False


def test_missing_file_fails_without_opening_or_modifying_anything(tmp_path):
    report = preflight_raster(tmp_path / "absent.tif")

    assert report["status"] == "FAIL"
    assert report["checks"][0]["name"] == "readability"


def test_multiband_raster_requires_band_review(tmp_path):
    path = tmp_path / "multiband.tif"
    write_dem(path, count=2)
    report = preflight_raster(path)

    assert report["status"] == "REVIEW"
    assert check(report, "band_count")["status"] == "REVIEW"


def test_non_elevation_layer_does_not_require_vertical_reference(tmp_path):
    path = tmp_path / "slope.tif"
    write_dem(path)
    report = preflight_raster(
        path,
        data_kind="slope",
        value_unit="degrees",
        vertical_reference_applicable=False,
        coordinate_reference_frame="MOON_ME/DE421",
        coordinate_reference_frame_source="NASA PGDA Product 78",
    )

    assert report["status"] == "PASS"
    assert report["raster"]["data_kind"] == "slope"
    assert check(report, "value_unit")["status"] == "PASS"
    assert check(report, "vertical_reference")["value"] == "not_applicable"
    assert check(report, "coordinate_reference_frame")["status"] == "PASS"


def test_elevation_layer_keeps_missing_vertical_reference_in_review(tmp_path):
    path = tmp_path / "lunar_surface.tif"
    write_dem(path)
    report = preflight_raster(
        path,
        elevation_unit="m",
        coordinate_reference_frame="MOON_ME/DE421",
        coordinate_reference_frame_source="NASA PGDA Product 78",
    )

    assert report["status"] == "REVIEW"
    assert check(report, "elevation_unit")["status"] == "PASS"
    assert check(report, "vertical_reference")["status"] == "REVIEW"
    assert check(report, "coordinate_reference_frame")["status"] == "PASS"
