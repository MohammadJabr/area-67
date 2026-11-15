import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from lola_south_pole import (  # noqa: E402
    ASSETS,
    SITES,
    asset_filename,
    asset_url,
    download_site_asset,
    site_asset_paths,
)


def test_pgda_target_allowlist_and_asset_paths():
    assert set(SITES) == {"Site01", "Site04", "Site06", "Site07", "Site11"}
    assert asset_filename("Site01", "elevation") == "Site01_final_adj_5mpp_surf.tif"
    assert asset_filename("Site07", "counts") == "Site07_final_adj_5mpp_ldec.tif"
    assert asset_filename("Site11", "z_uncertainty") == "Site11_final_adj_5mpp_toterr.tif"
    assert asset_url("Site01", "elevation").endswith(
        "/Site01/Site01_final_adj_5mpp_surf.tif"
    )
    paths = site_asset_paths("Site01", ["elevation", "counts"])
    assert paths["elevation"].parent == paths["counts"].parent
    assert paths["elevation"].name == "Site01_final_adj_5mpp_surf.tif"


def test_unknown_site_and_asset_are_rejected():
    with pytest.raises(ValueError, match="Unknown site"):
        asset_filename("Site99", "elevation")
    with pytest.raises(ValueError, match="Unknown asset"):
        asset_filename("Site01", "clone_001")


def test_download_uses_allowlisted_asset_and_never_overwrites(tmp_path):
    payload = b"II*\x00fake-tiff-payload"

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

    class FakeCRS:
        def to_string(self):
            return "EPSG:3031"

    class FakeDataset:
        count = 1
        crs = FakeCRS()
        width = 4
        height = 3
        transform = (5, 0, 0, 0, -5, 0)
        nodata = None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    destination = tmp_path / "Site01_final_adj_5mpp_surf.tif"
    with (
        patch("lola_south_pole.urllib.request.urlopen", return_value=FakeResponse()),
        patch("lola_south_pole.rasterio.open", return_value=FakeDataset()),
    ):
        result = download_site_asset("Site01", "elevation", destination)

    assert destination.read_bytes() == payload
    assert result["site_id"] == "Site01"
    assert result["asset"] == "elevation"
    assert result["raster_metadata"]["crs"] == "EPSG:3031"

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        download_site_asset("Site01", "elevation", destination)


def test_download_cleans_partial_on_invalid_response(tmp_path):
    payload = b"<html>not a raster</html>"

    class FakeResponse:
        status = 200
        headers = {"Content-Length": str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def read(self, size=-1):
            return payload

    destination = tmp_path / "bad.tif"
    with patch("lola_south_pole.urllib.request.urlopen", return_value=FakeResponse()):
        with pytest.raises(RuntimeError, match="not a TIFF"):
            download_site_asset("Site01", "elevation", destination)

    assert not destination.exists()
    assert not destination.with_name(destination.name + ".part").exists()


def test_download_enforces_declared_size_limit(tmp_path):
    payload = b"II*\x00payload"

    class FakeResponse:
        status = 200
        headers = {"Content-Length": str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def read(self, size=-1):
            return payload

    with patch("lola_south_pole.urllib.request.urlopen", return_value=FakeResponse()):
        with pytest.raises(RuntimeError, match="above limit"):
            download_site_asset("Site01", "elevation", tmp_path / "large.tif", max_bytes=4)


def test_asset_contract_contains_only_five_measured_layers():
    assert set(ASSETS) == {
        "elevation", "counts", "slope", "z_uncertainty", "slope_uncertainty"
    }
