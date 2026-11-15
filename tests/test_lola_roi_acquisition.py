import gzip
import hashlib
import json
import io
import sys
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from lola_roi_acquisition import (  # noqa: E402
    AVAILABLE_ROI_SITES,
    download_requested_sites,
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


def test_extract_skips_symbolic_links_and_records_them_in_manifest(tmp_path):
    archive_path = tmp_path / "site01.tgz"
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        payload = b"shape-index-placeholder"
        regular = tarfile.TarInfo("Site01_ROIs.shp")
        regular.size = len(payload)
        archive.addfile(regular, io.BytesIO(payload))

        link = tarfile.TarInfo("Site01_ROIs.gmt")
        link.type = tarfile.SYMTYPE
        link.linkname = "Site01_final_adj_5mpp_01_regionProps_avgillGT070.gmt"
        archive.addfile(link)

    archive_path.write_bytes(buffer.getvalue())
    destination = tmp_path / "extracted"
    written = extract_roi_archive(archive_path, destination)

    assert (destination / "Site01_ROIs.shp").read_bytes() == b"shape-index-placeholder"
    assert not (destination / "Site01_ROIs.gmt").exists()
    assert len(written) == 1

    manifest = json.loads(
        (destination / "archive_extraction_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["source_archive"] == "site01.tgz"
    assert manifest["skipped_symbolic_links"] == [
        {
            "member_name": "Site01_ROIs.gmt",
            "link_target": "Site01_final_adj_5mpp_01_regionProps_avgillGT070.gmt",
            "target_member_listed": False,
            "action": "skipped_not_created_or_followed",
        }
    ]


def test_inspection_reports_skipped_symbolic_links(tmp_path):
    folder = tmp_path / "extracted"
    folder.mkdir()
    (folder / "archive_extraction_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_archive": "Site01_ROIs.tgz",
                "extracted_regular_files": [],
                "skipped_symbolic_links": [
                    {
                        "member_name": "Site01_ROIs.gmt",
                        "link_target": "Site01_final_adj_5mpp_01_regionProps_avgillGT070.gmt",
                        "target_member_listed": False,
                        "action": "skipped_not_created_or_followed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = inspect_extracted_rois("Site01", folder)
    assert report["status"] == "review_required"
    assert len(report["skipped_symbolic_links"]) == 1
    assert any("Site01_ROIs.gmt" in warning for warning in report["warnings"])


def test_extract_rejects_symbolic_link_targets_that_escape_root(tmp_path):
    archive_path = tmp_path / "unsafe-link.tgz"
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        link = tarfile.TarInfo("nested/unsafe.gmt")
        link.type = tarfile.SYMTYPE
        link.linkname = "../../outside.gmt"
        archive.addfile(link)

    archive_path.write_bytes(buffer.getvalue())
    destination = tmp_path / "out"
    with pytest.raises(ValueError, match="Symbolic-link target escapes"):
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


def test_inspection_reports_invalid_geometry_reasons_and_source_attributes(tmp_path):
    import geopandas as gpd
    from shapely.geometry import Polygon, box

    extracted = tmp_path / "invalid_roi"
    extracted.mkdir()
    frame = gpd.GeoDataFrame(
        {
            "X": [123.0, 456.0],
            "Y": [-10.0, -20.0],
            "roi_name": ["valid", "self_intersection"],
            "geometry": [
                box(0, 0, 10, 10),
                Polygon([(0, 0), (10, 10), (0, 10), (10, 0), (0, 0)]),
            ],
        },
        crs="EPSG:3031",
    )
    frame.to_file(extracted / "candidate_rois.shp")

    report = inspect_extracted_rois("Site04", extracted)
    shapefile = report["shapefiles"][0]

    assert shapefile["invalid_geometry_count"] == 1
    assert len(shapefile["invalid_geometry_details"]) == 1
    invalid = shapefile["invalid_geometry_details"][0]
    assert invalid["feature_index"] == 1
    assert invalid["properties"] == {
        "X": 456.0,
        "Y": -20.0,
        "roi_name": "self_intersection",
    }
    assert "self-intersection" in invalid["validity_reason"].lower()


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


def test_batch_download_continues_after_provider_error_and_preserves_successes(
    tmp_path, monkeypatch, capsys
):
    import lola_roi_acquisition as acquisition

    monkeypatch.setattr(acquisition, "RAW_ARCHIVE_ROOT", tmp_path)

    def fake_download(site_id, destination, *, max_bytes):
        if site_id == "Site06":
            raise RuntimeError("HTML error page from provider")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"test-archive-placeholder")
        return {"site_id": site_id, "path": str(destination)}

    monkeypatch.setattr(acquisition, "download_roi_archive", fake_download)
    failures = download_requested_sites(
        ["Site01", "Site06", "Site07"], max_bytes=1024
    )

    assert failures == ["Site06"]
    assert (tmp_path / "Site01" / "Site01_ROIs.tgz").is_file()
    assert (tmp_path / "Site07" / "Site07_ROIs.tgz").is_file()
    output = capsys.readouterr().out
    assert "ERROR downloading Site06" in output
    assert "Successful archives were preserved" in output


def test_download_non_gzip_error_includes_response_diagnostics(tmp_path):
    payload = b"<html><title>Temporary server page</title></html>"

    class FakeResponse:
        status = 200
        headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "text/html",
        }
        url = "https://example.invalid/error"

        def __init__(self):
            self.stream = io.BytesIO(payload)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.stream.close()

        def read(self, size=-1):
            return self.stream.read(size)

    destination = tmp_path / "bad.tgz"
    with patch("lola_roi_acquisition.urllib.request.urlopen", return_value=FakeResponse()):
        with pytest.raises(RuntimeError) as exc:
            download_roi_archive("Site06", destination)

    message = str(exc.value)
    assert "HTTP=200" in message
    assert "content_type='text/html'" in message
    assert "Temporary server page" in message
    assert not destination.exists()
    assert not destination.with_name(destination.name + ".part").exists()
