import io
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from zenodo_range_zip import RemoteRangeZip, find_member  # noqa: E402


class MemoryRangeZip(RemoteRangeZip):
    def __init__(self, archive_bytes: bytes):
        super().__init__("memory://test-archive")
        self.archive_bytes = archive_bytes
        self.file_size = len(archive_bytes)
        self.requested_ranges = []

    def _fetch_range(self, start: int, end: int) -> bytes:
        if start < 0 or end < start or end >= len(self.archive_bytes):
            raise ValueError(f"Invalid test range {start}-{end}")
        self.requested_ranges.append((start, end))
        return self.archive_bytes[start : end + 1]


def make_zip(*, member_name="nested/A306_GLDMASK_005.tif", payload=None):
    if payload is None:
        payload = b"fake-geotiff-mask-data" * 100
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member_name, payload)
        archive.writestr("README.txt", "archive readme")
    return stream.getvalue(), payload


def test_lists_remote_archive_using_only_small_ranges():
    archive_bytes, payload = make_zip(payload=b"x" * 750_000)
    reader = MemoryRangeZip(archive_bytes)

    entries = reader.list_entries()

    assert len(entries) == 2
    mask = find_member(entries, "A306_GLDMASK_005.tif")
    assert mask.uncompressed_size == len(payload)
    assert mask.compression == zipfile.ZIP_DEFLATED
    # The central directory and end records are fetched, not the large member body.
    assert sum(end - start + 1 for start, end in reader.requested_ranges) < 100_000


def test_extracts_one_member_and_verifies_its_crc(tmp_path):
    archive_bytes, expected = make_zip()
    reader = MemoryRangeZip(archive_bytes)
    entry = find_member(reader.list_entries(), "nested/A306_GLDMASK_005.tif")

    result = reader.extract_entry(entry, tmp_path)

    assert result == tmp_path / "nested" / "A306_GLDMASK_005.tif"
    assert result.read_bytes() == expected


def test_rejects_crc_mismatch(tmp_path):
    archive_bytes, _ = make_zip()
    reader = MemoryRangeZip(archive_bytes)
    entry = find_member(reader.list_entries(), "A306_GLDMASK_005.tif")

    with pytest.raises(RuntimeError, match="CRC32 mismatch"):
        reader.extract_entry(replace(entry, crc32=entry.crc32 ^ 1), tmp_path)


def test_rejects_path_traversal(tmp_path):
    archive_bytes, _ = make_zip(member_name="../outside.tif")
    reader = MemoryRangeZip(archive_bytes)
    entry = find_member(reader.list_entries(), "../outside.tif")

    with pytest.raises(RuntimeError, match="Unsafe ZIP member path"):
        reader.extract_entry(entry, tmp_path)
    assert not (tmp_path.parent / "outside.tif").exists()
