import json
import io
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from lola_site04 import ASSETS, download_asset, inspect_raster  # noqa: E402
from lola_site04_qa import analyze_arrays, load_rasters, run  # noqa: E402


def synthetic_arrays():
    return {
        "elevation": np.array([[10.0, 11.0], [12.0, 13.0]], dtype="float32"),
        "counts": np.array([[1.0, 0.0], [2.0, 0.0]], dtype="float32"),
        "slope": np.array([[0.0, 10.0], [20.0, 30.0]], dtype="float32"),
        "z_uncertainty": np.array([[0.2, 0.4], [0.3, 0.5]], dtype="float32"),
        "slope_uncertainty": np.array([[1.0, 2.0], [3.0, 4.0]], dtype="float32"),
    }


def test_ldec_zero_counts_are_not_mistaken_for_invalid_data():
    arrays = synthetic_arrays()
    masks = {name: np.ones((2, 2), dtype=bool) for name in ASSETS}
    report = analyze_arrays(arrays, masks=masks, tile_size=1)
    support = report["layers"]["counts"]["direct_observation_support"]
    assert support["positive_count_pixel_count"] == 2
    assert support["zero_count_pixel_count"] == 2
    assert report["grid_qa"]["common_valid_coverage_pct"] == 100.0


def test_nonfinite_and_masked_pixels_are_excluded():
    arrays = synthetic_arrays()
    arrays["elevation"][0, 0] = np.nan
    masks = {name: np.ones((2, 2), dtype=bool) for name in ASSETS}
    masks["slope"][1, 1] = False
    report = analyze_arrays(arrays, masks=masks, tile_size=1)
    assert report["grid_qa"]["per_asset_valid_pixel_count"]["elevation"] == 3
    assert report["grid_qa"]["per_asset_valid_pixel_count"]["slope"] == 3
    assert report["grid_qa"]["common_valid_pixel_count"] == 2


def test_unphysical_values_are_flagged():
    arrays = synthetic_arrays()
    arrays["slope"][0, 0] = 91
    arrays["z_uncertainty"][0, 0] = -1
    arrays["counts"][0, 0] = -2
    report = analyze_arrays(arrays, tile_size=1)
    assert report["layers"]["slope"]["screening_flags"]["outside_0_to_90_degrees"] == 1
    assert report["layers"]["z_uncertainty"]["screening_flags"]["negative_values"] == 1
    assert report["layers"]["counts"]["screening_flags"]["negative_values"] == 1


def test_dimension_mismatch_fails():
    arrays = synthetic_arrays()
    arrays["slope"] = np.ones((1, 2), dtype="float32")
    with pytest.raises(ValueError, match="dimension mismatch"):
        analyze_arrays(arrays)


def test_raster_loader_preserves_mask_and_metadata(tmp_path):
    paths = {}
    transform = from_origin(-9000, 1000, 5, 5)
    for name in ASSETS:
        path = tmp_path / f"{name}.tif"
        data = synthetic_arrays()[name]
        with rasterio.open(path, "w", driver="GTiff", width=2, height=2, count=1,
                           dtype="float32", crs="EPSG:4326", transform=transform,
                           nodata=np.nan) as ds:
            ds.write(data, 1)
        paths[name] = path
    arrays, metadata = load_rasters(paths)
    assert arrays["counts"].shape == (2, 2)
    assert metadata["elevation"]["width"] == 2
    assert metadata["_masks"]["elevation"].all()


def test_inspection_counts_nodata_and_nonfinite_separately(tmp_path):
    path = tmp_path / "inspection.tif"
    data = np.array([[1.0, np.nan], [3.0, 4.0]], dtype="float32")
    with rasterio.open(path, "w", driver="GTiff", width=2, height=2, count=1,
                       dtype="float32", crs="EPSG:4326",
                       transform=from_origin(0, 2, 1, 1), nodata=np.nan) as ds:
        ds.write(data, 1)
    info = inspect_raster(path)
    assert info["nodata"] == "NaN"
    assert info["nodata_masked_pixel_count"] == 1
    assert info["nonfinite_pixel_count_band_1"] == 1
    assert info["statistics_band_1"]["valid_pixel_count"] == 3
    json.dumps(info, allow_nan=False)


def test_download_streams_tiff_without_overwriting(tmp_path):
    payload = b"II*\x00synthetic-tiff-content"

    class FakeResponse:
        status = 200

        def __init__(self):
            self.headers = {"Content-Length": str(len(payload))}
            self.stream = io.BytesIO(payload)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.stream.close()

        def read(self, size=-1):
            return self.stream.read(size)

    destination = tmp_path / "counts.tif"
    with patch("lola_site04.urllib.request.urlopen", return_value=FakeResponse()):
        assert download_asset("counts", destination) == destination
    assert destination.read_bytes() == payload
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        download_asset("counts", destination)
    assert destination.read_bytes() == payload


def test_download_rejects_non_tiff_and_cleans_partial_file(tmp_path):
    payload = b"<html>not a raster</html>"

    class FakeResponse:
        status = 200
        headers = {"Content-Length": str(len(payload))}

        def __init__(self):
            self.stream = io.BytesIO(payload)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.stream.close()

        def read(self, size=-1):
            return self.stream.read(size)

    destination = tmp_path / "counts.tif"
    with patch("lola_site04.urllib.request.urlopen", return_value=FakeResponse()):
        with pytest.raises(RuntimeError, match="not a TIFF"):
            download_asset("counts", destination)
    assert not destination.exists()
    assert not destination.with_name(destination.name + ".part").exists()


def test_run_requires_exact_georeferencing_alignment(tmp_path):
    paths = {}
    for name in ASSETS:
        path = tmp_path / f"{name}.tif"
        transform = from_origin(-9000, 1000, 5, 5)
        if name == "slope":
            transform = from_origin(-8995, 1000, 5, 5)
        with rasterio.open(path, "w", driver="GTiff", width=2, height=2, count=1,
                           dtype="float32", crs="EPSG:4326", transform=transform,
                           nodata=np.nan) as ds:
            ds.write(synthetic_arrays()[name], 1)
        paths[name] = path
    with pytest.raises(ValueError, match="Grid georeferencing mismatch"):
        run(paths)
