import hashlib
import io
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src.data.earth_dem_acquisition import download_tile


def make_tiff_bytes():
    buffer = io.BytesIO()
    with rasterio.open(
        buffer,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(-70, -24, 1 / 3600, 1 / 3600),
        nodata=-9999,
    ) as dataset:
        dataset.write(np.array([[1, 2], [3, 4]], dtype="float32"), 1)
    return buffer.getvalue()


class FakeResponse:
    status = 200

    def __init__(self, content):
        self.content = content
        self.headers = {"Content-Length": str(len(content))}
        self.stream = io.BytesIO(content)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.stream.close()

    def read(self, size=-1):
        return self.stream.read(size)


def test_download_tile_validates_raster_hash_and_never_overwrites(tmp_path):
    content = make_tiff_bytes()
    destination = tmp_path / "tile.tif"
    with patch("src.data.earth_dem_acquisition.urllib.request.urlopen", return_value=FakeResponse(content)):
        result = download_tile("yungay", destination)

    assert result["source_id"] == "Copernicus_DSM_COG_10_S25_00_W070_00_DEM"
    assert result["sha256"] == hashlib.sha256(content).hexdigest()
    assert result["raster_metadata"]["crs"] == "EPSG:4326"
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        download_tile("yungay", destination)
    assert destination.read_bytes() == content


def test_download_tile_rejects_oversize_before_writing(tmp_path):
    content = make_tiff_bytes()
    destination = tmp_path / "tile.tif"
    with patch("src.data.earth_dem_acquisition.urllib.request.urlopen", return_value=FakeResponse(content)):
        with pytest.raises(RuntimeError, match="above configured limit"):
            download_tile("askja", destination, max_bytes=10)
    assert not destination.exists()
    assert not destination.with_name("tile.tif.part").exists()


def test_download_tile_rejects_invalid_response_and_cleans_own_partial(tmp_path):
    destination = tmp_path / "tile.tif"
    with patch("src.data.earth_dem_acquisition.urllib.request.urlopen", return_value=FakeResponse(b"not a tiff")):
        with pytest.raises(RuntimeError, match="not a TIFF"):
            download_tile("askja", destination)
    assert not destination.exists()
    assert not destination.with_name("tile.tif.part").exists()


def test_download_tile_rejects_unknown_candidate(tmp_path):
    with pytest.raises(ValueError, match="Unknown candidate"):
        download_tile("unknown", tmp_path / "tile.tif")
