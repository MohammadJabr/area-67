import gzip
import hashlib
import io
import sys
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from lola_roi_acquisition import (  # noqa: E402
    AVAILABLE_ROI_SITES,
    download_roi_archive,
    extract_roi_archive,
    inspect_extracted_rois,
)


def make_tar_gz(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in entries:
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_allowlist_contains_only_published_roi_archives():
    assert AVAILABLE_ROI_SITES == {
        "Site01": "Site01_ROIs.tgz",
        "Site04": "Site04_ROIs.tgz",
        "Site06": "Site06_ROIs.tgz",
        "Site07": "Site07_ROIs.tgz",
        "Site11": "Site11_ROIs.tgz",
    }


def test_download_roi_archive_streams_gzip_without_overwrite(tmp_path):
    payload = make_tar_gz([("roi/readme.txt", b"official test fixture")])

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

    destination = tmp_path / "Site04_ROIs.tgz"
    with patch("lola_roi_acquisition.urllib.request.urlopen", return_value=FakeResponse()):
        result = download_roi_archive("Site04", destination)

    assert destination.read_bytes() == payload
    assert result["sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["archive_member_count"] == 1

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        download_roi_archive("Site04", destination)


def test_download_rejects_unknown_site_and_non_gzip_response(tmp_path):
    with pytest.raises(ValueError, match="Unknown ROI site"):
        download_roi_archive("Site99", tmp_path / "unknown.tgz")

    payload = b"<html>not an archive</html>"

    class FakeResponse:
        status = 200
        headers = {"Content-Length": str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def read(self, size=-1):
            nonlocal payload
            chunk, payload = payload[:size], payload[size:]
            return chunk

    destination = tmp_path / "bad.tgz"
    with patch("lola_roi_acquisition.urllib.request.urlopen", return_value=FakeResponse()):
        with pytest.raises(RuntimeError, match="not a gzip archive"):
            download_roi_archive("Site04", destination)

    assert not destination.exists()
    assert not destination.with_name(destination.name + ".part").exists()


def test_extract_roi_archive_preserves_nested_regular_files(tmp_path):
    archive_path = tmp_path / "site04.tgz"
    archive_path.write_bytes(
        make_tar_gz([
            ("Site04_ROIs/roi_a/readme.txt", b"ROI metadata"),
            ("Site04_ROIs/roi_a/boundary.prj", b"projection text"),
        ])
    )
    destination = tmp_path / "extracted"
    written = extract_roi_archive(archive_path, destination)

    assert (destination / "Site04_ROIs/roi_a/readme.txt").read_bytes() == b"ROI metadata"
    assert (destination / "Site04_ROIs/roi_a/boundary.prj").read_bytes() == b"projection text"
    assert len(written) == 2

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        extract_roi_archive(archive_path, destination)


@pytest.mark.parametrize("unsafe_name", ["../outside.txt", "/absolute.txt", "C:/drive.txt", r"..\outside.txt"])
def test_extract_rejects_unsafe_member_paths(tmp_path, unsafe_name):
    archive_path = tmp_path / "unsafe.tgz"
    archive_path.write_bytes(make_tar_gz([(unsafe_name, b"bad")]))
    destination = tmp_path / "out"

    with pytest.raises(ValueError, match="Unsafe|Absolute|Path traversal"):
        extract_roi_archive(archive_path, destination)

    assert not destination.exists()
    assert not destination.with_name(destination.name + ".staging").exists()


def test_extract_enforces_uncompressed_size_limit(tmp_path):
    archive_path = tmp_path / "large.tgz"
    archive_path.write_bytes(make_tar_gz([("large.bin", b"x" * 100)]))
    with pytest.raises(ValueError, match="uncompressed-size limit"):
        extract_roi_archive(archive_path, tmp_path / "out", max_uncompressed_bytes=10)


def test_inspection_reports_missing_shapefiles_without_inventing_geometry(tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()
    report = inspect_extracted_rois("Site04", folder)
    assert report["shapefile_count"] == 0
    assert report["status"] == "review_required"
    assert "No .shp files" in report["warnings"][0]


def test_inspection_rejects_unknown_site(tmp_path):
    with pytest.raises(ValueError, match="Unknown ROI site"):
        inspect_extracted_rois("Site99", tmp_path)


def test_inspection_reports_crs_bounds_and_null_geometries(tmp_path):
    import geopandas as gpd
    from shapely.geometry import Polygon

    extracted = tmp_path / "roi_shapes"
    extracted.mkdir()
    shape_path = extracted / "candidate_rois.shp"
    frame = gpd.GeoDataFrame(
        {"roi_name": ["valid", "missing"], "geometry": [
            Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]), None
        ]},
        crs="EPSG:3031",
    )
    frame.to_file(shape_path)

    report = inspect_extracted_rois("Site04", extracted)
    assert report["shapefile_count"] == 1
    shape = report["shapefiles"][0]
    assert shape["feature_count"] == 2
    assert shape["crs"] == "EPSG:3031"
    assert shape["bounds"] == [0.0, 0.0, 10.0, 10.0]
    assert shape["null_geometry_count"] == 1
    assert shape["area_native_units2"] == 100.0
    assert report["status"] == "review_required"
