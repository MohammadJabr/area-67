import csv
import json

import numpy as np
import pytest
import rasterio
from affine import Affine
from rasterio.transform import from_origin

from src.routes.raster_io import load_aligned_route_rasters
from src.routes.workflow import plan_route_from_rasters


def _write_raster(path, values, *, transform=None, crs="EPSG:32632", nodata=-9999):
    values = np.asarray(values, dtype="float32")
    transform = transform or from_origin(500000, 4000000, 10, 10)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dataset:
        dataset.write(values, 1)


def test_aligned_rasters_load_and_preserve_combined_nodata_mask(tmp_path):
    elevation = np.full((3, 3), 100.0, dtype="float32")
    slope = np.full((3, 3), 5.0, dtype="float32")
    tri = np.full((3, 3), 2.0, dtype="float32")
    tri[0, 0] = -9999.0

    elevation_path = tmp_path / "elevation.tif"
    slope_path = tmp_path / "slope.tif"
    tri_path = tmp_path / "tri.tif"

    _write_raster(elevation_path, elevation)
    _write_raster(slope_path, slope)
    _write_raster(tri_path, tri)

    result = load_aligned_route_rasters(
        elevation_path,
        slope_path,
        tri_path,
        elevation_unit="m",
        slope_unit="degrees",
        tri_unit="m",
    )

    assert result["valid_mask"].shape == (3, 3)
    assert not result["valid_mask"][0, 0]
    assert np.isnan(result["tri_m"][0, 0])
    assert result["grid_metadata"]["cell_size_m"] == 10.0
    assert result["grid_metadata"]["crs"] == "EPSG:32632"


def test_aligned_raster_loader_converts_declared_units(tmp_path):
    elevation_path = tmp_path / "elevation_ft.tif"
    slope_path = tmp_path / "slope_rad.tif"
    tri_path = tmp_path / "tri_ft.tif"

    _write_raster(elevation_path, np.full((2, 2), 100.0))
    _write_raster(slope_path, np.full((2, 2), np.pi / 2))
    _write_raster(tri_path, np.full((2, 2), 3.280839895))

    result = load_aligned_route_rasters(
        elevation_path,
        slope_path,
        tri_path,
        elevation_unit="ft",
        slope_unit="radians",
        tri_unit="ft",
    )

    assert np.allclose(result["elevation_m"], 30.48)
    assert np.allclose(result["slope_deg"], 90.0)
    assert np.allclose(result["tri_m"], 1.0, atol=1e-6)


def test_misaligned_rasters_are_rejected(tmp_path):
    elevation_path = tmp_path / "elevation.tif"
    slope_path = tmp_path / "slope.tif"
    tri_path = tmp_path / "tri.tif"

    _write_raster(elevation_path, np.ones((3, 3)))
    _write_raster(slope_path, np.ones((3, 3)), transform=from_origin(500010, 4000000, 10, 10))
    _write_raster(tri_path, np.ones((3, 3)))

    with pytest.raises(ValueError, match="transform does not match"):
        load_aligned_route_rasters(
            elevation_path,
            slope_path,
            tri_path,
            elevation_unit="m",
            slope_unit="degrees",
            tri_unit="m",
        )


def test_route_workflow_exports_profile_and_map_coordinates(tmp_path):
    elevation_path = tmp_path / "elevation.tif"
    slope_path = tmp_path / "slope.tif"
    tri_path = tmp_path / "tri.tif"

    _write_raster(elevation_path, np.full((3, 3), 100.0))
    _write_raster(slope_path, np.zeros((3, 3)))
    _write_raster(tri_path, np.zeros((3, 3)))

    output_path = tmp_path / "route.csv"
    result = plan_route_from_rasters(
        elevation_path,
        slope_path,
        tri_path,
        (0, 0),
        (2, 2),
        elevation_unit="m",
        slope_unit="degrees",
        tri_unit="m",
        slope_scale_deg=10,
        tri_scale_m=5,
        output_path=output_path,
    )

    assert output_path.is_file()
    assert result["route"]["status"] == "success"

    with output_path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == len(result["route"]["path_cells"])
    assert rows[0]["map_x"] != ""
    assert rows[0]["map_y"] != ""
    assert rows[0]["crs"] == "EPSG:32632"
    assert rows[-1]["cumulative_cost_m"] == rows[-1]["total_route_cost_m"]



def test_sheared_affine_grid_is_rejected_even_when_pixel_basis_lengths_match(tmp_path):
    elevation_path = tmp_path / "elevation.tif"
    slope_path = tmp_path / "slope.tif"
    tri_path = tmp_path / "tri.tif"
    sheared = Affine(10, 1, 500000, 0, -(99 ** 0.5), 4000000)

    _write_raster(elevation_path, np.ones((3, 3)), transform=sheared)
    _write_raster(slope_path, np.ones((3, 3)), transform=sheared)
    _write_raster(tri_path, np.ones((3, 3)), transform=sheared)

    with pytest.raises(ValueError, match="not orthogonal"):
        load_aligned_route_rasters(
            elevation_path,
            slope_path,
            tri_path,
            elevation_unit="m",
            slope_unit="degrees",
            tri_unit="m",
        )


def test_raster_loader_rejects_oversized_grid_before_reading_arrays(tmp_path):
    elevation_path = tmp_path / "elevation.tif"
    slope_path = tmp_path / "slope.tif"
    tri_path = tmp_path / "tri.tif"
    for path in (elevation_path, slope_path, tri_path):
        _write_raster(path, np.ones((3, 3)))

    with pytest.raises(ValueError, match="exceeding max_grid_cells"):
        load_aligned_route_rasters(
            elevation_path,
            slope_path,
            tri_path,
            elevation_unit="m",
            slope_unit="degrees",
            tri_unit="m",
            max_grid_cells=8,
        )


def test_route_metadata_sidecar_records_parameters_and_source_checksums(tmp_path):
    elevation_path = tmp_path / "elevation.tif"
    slope_path = tmp_path / "slope.tif"
    tri_path = tmp_path / "tri.tif"
    for path in (elevation_path, slope_path, tri_path):
        _write_raster(path, np.ones((3, 3)))

    csv_path = tmp_path / "route.csv"
    metadata_path = tmp_path / "route_metadata.json"
    result = plan_route_from_rasters(
        elevation_path,
        slope_path,
        tri_path,
        (0, 0),
        (2, 2),
        elevation_unit="m",
        slope_unit="degrees",
        tri_unit="m",
        slope_scale_deg=10,
        tri_scale_m=5,
        alpha=0.75,
        beta=1.25,
        connectivity=4,
        output_path=csv_path,
        metadata_output_path=metadata_path,
        max_grid_cells=100,
    )

    assert csv_path.is_file()
    assert metadata_path.is_file()
    document = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert document["parameters"]["start_cell"] == [0, 0]
    assert document["parameters"]["goal_cell"] == [2, 2]
    assert document["parameters"]["alpha"] == 0.75
    assert document["parameters"]["beta"] == 1.25
    assert document["parameters"]["connectivity"] == 4
    assert document["parameters"]["max_grid_cells"] == 100
    assert document["grid_metadata"]["cell_size_m"] == 10.0
    assert document["input_rasters"]["elevation"]["sha256"]
    assert result["route_metadata_json"] == metadata_path
