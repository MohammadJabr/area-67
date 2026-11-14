import hashlib
from io import BytesIO

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src.data.usgs_3dep_acquisition import NEIGHBOR_TILE_ID, acquire_tile


class FakeResponse(BytesIO):
    def __init__(self, data, *, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def make_tiff(path):
    with rasterio.open(
        path, "w", driver="GTiff", width=2, height=2, count=1,
        dtype="float32", crs="EPSG:4326",
        transform=from_origin(-155.50, 19.90, 0.1, 0.1),
    ) as dataset:
        dataset.write(np.array([[1, 2], [3, 4]], dtype="float32"), 1)
    return path.read_bytes()


def test_download_validates_tile_and_resumes_interrupted_partial(tmp_path):
    payload = make_tiff(tmp_path / "fixture.tif")
    destination = tmp_path / "candidate.tif"
    partial = destination.with_name(destination.name + ".part")
    split = len(payload) // 2
    partial.write_bytes(payload[:split])

    def opener(request, timeout):
        assert request.get_header("Range") == f"bytes={split}-"
        return FakeResponse(payload[split:], status=206, headers={
            "Content-Length": str(len(payload) - split),
            "Content-Range": f"bytes {split}-{len(payload)-1}/{len(payload)}",
        })

    result = acquire_tile(destination, expected_size=len(payload), open_url=opener)

    assert result["status"] == "downloaded"
    assert result["raster_metadata"]["site_coordinate_covered"]
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == result["sha256"]
    assert not partial.exists()


def test_verified_existing_file_is_skipped_and_mismatch_is_never_overwritten(tmp_path):
    payload = make_tiff(tmp_path / "fixture.tif")
    destination = tmp_path / "candidate.tif"
    destination.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    result = acquire_tile(destination, expected_sha256=digest, expected_size=len(payload))
    assert result["status"] == "skipped_verified"
    with pytest.raises(FileExistsError):
        acquire_tile(destination, expected_sha256="0" * 64, expected_size=len(payload))
    assert destination.read_bytes() == payload


def test_failed_response_leaves_partial_for_inspection(tmp_path):
    payload = make_tiff(tmp_path / "fixture.tif")
    destination = tmp_path / "candidate.tif"

    def opener(request, timeout):
        return FakeResponse(payload[:20], headers={"Content-Length": str(len(payload))})

    with pytest.raises(RuntimeError, match="Incomplete tile"):
        acquire_tile(destination, expected_size=len(payload), open_url=opener)
    assert destination.with_name(destination.name + ".part").read_bytes() == payload[:20]
    assert not destination.exists()


def test_adjacent_catalog_tile_uses_its_own_allowlisted_url_and_size(tmp_path):
    payload = make_tiff(tmp_path / "fixture.tif")
    destination = tmp_path / "neighbor.tif"
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(payload, headers={"Content-Length": str(len(payload))})

    result = acquire_tile(destination, tile_id=NEIGHBOR_TILE_ID,
                          expected_size=len(payload), open_url=opener)
    assert result["tile_id"] == NEIGHBOR_TILE_ID
    assert "USGS_1M_5_x24y220" in calls[0]
    assert result["raster_metadata"]["site_coordinate_covered"]


def test_unknown_tile_is_rejected_before_network_or_filesystem_write(tmp_path):
    called = False

    def opener(request, timeout):
        nonlocal called
        called = True
        raise AssertionError("network must not be used for an unknown tile")

    with pytest.raises(ValueError, match="allowlist"):
        acquire_tile(tmp_path / "unknown.tif", tile_id="unlisted", open_url=opener)
    assert not called
    assert not (tmp_path / "unknown.tif").exists()
