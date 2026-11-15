#!/usr/bin/env python3
"""Inspect or selectively extract members of a remote ZIP over HTTP byte ranges.

Only the ZIP end records, central directory, local header, and requested member
data are fetched. The complete remote archive is never downloaded.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

DEFAULT_URL = (
    "https://zenodo.org/records/17954508/files/"
    "A3CLR22_6_Connecting_Ridge.zip?download=1"
)
RANGE_RE = re.compile(r"^bytes\s+(\d+)-(\d+)/(\d+)$", re.IGNORECASE)
MAX_CENTRAL_DIRECTORY_BYTES = 128 * 1024 * 1024
DEFAULT_MAX_MEMBER_MIB = 512

EOCD_SIGNATURE = b"PK\x05\x06"
ZIP64_LOCATOR_SIGNATURE = b"PK\x06\x07"
ZIP64_EOCD_SIGNATURE = b"PK\x06\x06"
CENTRAL_SIGNATURE = b"PK\x01\x02"
LOCAL_SIGNATURE = b"PK\x03\x04"


@dataclass(frozen=True)
class ZipEntry:
    name: str
    flags: int
    compression: int
    crc32: int
    compressed_size: int
    uncompressed_size: int
    local_header_offset: int


class RemoteRangeZip:
    """Minimal single-file ZIP reader backed by HTTP Range requests."""

    def __init__(self, url: str, timeout: int = 60):
        self.url = url
        self.timeout = timeout
        self.file_size: int | None = None
        self._entries: list[ZipEntry] | None = None

    def _fetch_range(self, start: int, end: int) -> bytes:
        if start < 0 or end < start:
            raise ValueError(f"Invalid byte range: {start}-{end}")

        request = urllib.request.Request(
            self.url,
            headers={
                "Range": f"bytes={start}-{end}",
                "User-Agent": "AREA67-range-zip-inspector/1.0",
                "Accept-Encoding": "identity",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = getattr(response, "status", response.getcode())
                content_range = response.headers.get("Content-Range", "")
                match = RANGE_RE.match(content_range.strip())
                if status != 206 or not match:
                    raise RuntimeError(
                        "Server did not honor the byte-range request. "
                        f"HTTP={status}, Content-Range={content_range!r}. "
                        "Stopping to avoid downloading the full archive."
                    )
                actual_start, actual_end, total_size = map(int, match.groups())
                if actual_start != start or actual_end != end:
                    raise RuntimeError(
                        f"Server returned bytes {actual_start}-{actual_end}, "
                        f"but requested {start}-{end}."
                    )
                if self.file_size is not None and total_size != self.file_size:
                    raise RuntimeError(
                        f"Remote file size changed during inspection: "
                        f"{self.file_size} -> {total_size}."
                    )
                self.file_size = total_size
                payload = response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"HTTP range request failed ({exc.code}) for bytes {start}-{end}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error while requesting bytes {start}-{end}: {exc}") from exc

        expected = end - start + 1
        if len(payload) != expected:
            raise RuntimeError(
                f"Short range response: received {len(payload)} bytes, expected {expected}."
            )
        return payload

    @staticmethod
    def _zip64_values(extra: bytes, need_uncompressed: bool,
                      need_compressed: bool, need_offset: bool,
                      need_disk: bool) -> tuple[int | None, int | None, int | None, int | None]:
        cursor = 0
        while cursor + 4 <= len(extra):
            field_id, field_size = struct.unpack_from("<HH", extra, cursor)
            cursor += 4
            field = extra[cursor: cursor + field_size]
            if len(field) != field_size:
                raise RuntimeError("Malformed ZIP extra field.")
            cursor += field_size
            if field_id != 0x0001:
                continue

            pos = 0

            def take(fmt: str) -> int:
                nonlocal pos
                size = struct.calcsize(fmt)
                if pos + size > len(field):
                    raise RuntimeError("Truncated ZIP64 extra field.")
                value = struct.unpack_from(fmt, field, pos)[0]
                pos += size
                return value

            uncompressed = take("<Q") if need_uncompressed else None
            compressed = take("<Q") if need_compressed else None
            offset = take("<Q") if need_offset else None
            disk = take("<L") if need_disk else None
            return uncompressed, compressed, offset, disk
        if any((need_uncompressed, need_compressed, need_offset, need_disk)):
            raise RuntimeError("ZIP64 values are required but the ZIP64 extra field is missing.")
        return None, None, None, None

    def _read_end_record(self) -> tuple[int, int, int]:
        # The maximum EOCD + ZIP comment length is 22 + 65,535 bytes.
        if self.file_size is None:
            self._fetch_range(0, 0)
        assert self.file_size is not None
        if self.file_size < 22:
            raise RuntimeError("Remote file is too small to be a ZIP archive.")

        tail_start = max(0, self.file_size - (22 + 65535))
        tail = self._fetch_range(tail_start, self.file_size - 1)
        eocd_index = tail.rfind(EOCD_SIGNATURE)
        if eocd_index < 0 or eocd_index + 22 > len(tail):
            raise RuntimeError("ZIP end-of-central-directory record was not found.")

        (
            _signature,
            disk_number,
            central_disk,
            entries_on_disk,
            entries_total,
            central_size,
            central_offset,
            comment_length,
        ) = struct.unpack_from("<4s4H2LH", tail, eocd_index)

        if eocd_index + 22 + comment_length != len(tail):
            raise RuntimeError("ZIP end record/comment does not end at the remote file boundary.")
        if disk_number != 0 or central_disk != 0:
            raise RuntimeError("Multi-disk ZIP archives are not supported.")
        if entries_on_disk != entries_total and entries_on_disk != 0xFFFF:
            raise RuntimeError("Central directory spans multiple disks.")

        needs_zip64 = (
            entries_total == 0xFFFF
            or central_size == 0xFFFFFFFF
            or central_offset == 0xFFFFFFFF
        )
        if needs_zip64:
            locator_index = eocd_index - 20
            if locator_index < 0 or tail[locator_index:locator_index + 4] != ZIP64_LOCATOR_SIGNATURE:
                raise RuntimeError("ZIP64 end locator is missing.")
            _, zip64_disk, zip64_offset, total_disks = struct.unpack_from(
                "<4sLQL", tail, locator_index
            )
            if zip64_disk != 0 or total_disks != 1:
                raise RuntimeError("Multi-disk ZIP64 archives are not supported.")
            zip64_record = self._fetch_range(zip64_offset, zip64_offset + 55)
            if zip64_record[:4] != ZIP64_EOCD_SIGNATURE:
                raise RuntimeError("ZIP64 end-of-central-directory record is invalid.")
            (
                _sig,
                _record_size,
                _made_by,
                _needed,
                disk_number,
                central_disk,
                entries_on_disk,
                entries_total,
                central_size,
                central_offset,
            ) = struct.unpack_from("<4sQ2H2L4Q", zip64_record)
            if disk_number != 0 or central_disk != 0 or entries_on_disk != entries_total:
                raise RuntimeError("Multi-disk ZIP64 archives are not supported.")

        if central_size > MAX_CENTRAL_DIRECTORY_BYTES:
            raise RuntimeError(
                f"Central directory is unexpectedly large ({central_size} bytes); "
                f"safety limit is {MAX_CENTRAL_DIRECTORY_BYTES} bytes."
            )
        if central_offset + central_size > self.file_size:
            raise RuntimeError("Central directory points outside the remote ZIP.")
        return int(central_offset), int(central_size), int(entries_total)

    def list_entries(self) -> list[ZipEntry]:
        if self._entries is not None:
            return list(self._entries)

        central_offset, central_size, expected_entries = self._read_end_record()
        central = (
            self._fetch_range(central_offset, central_offset + central_size - 1)
            if central_size
            else b""
        )
        entries: list[ZipEntry] = []
        cursor = 0

        while cursor < len(central):
            if cursor + 46 > len(central):
                raise RuntimeError("Truncated ZIP central directory.")
            fields = struct.unpack_from("<4s6H3L5H2L", central, cursor)
            if fields[0] != CENTRAL_SIGNATURE:
                raise RuntimeError(f"Invalid central-directory signature at byte {cursor}.")

            flags = fields[3]
            compression = fields[4]
            crc32_value = fields[7]
            compressed_size = fields[8]
            uncompressed_size = fields[9]
            name_length = fields[10]
            extra_length = fields[11]
            comment_length = fields[12]
            disk_start = fields[13]
            local_header_offset = fields[16]

            start = cursor + 46
            name_bytes = central[start:start + name_length]
            extra_start = start + name_length
            extra = central[extra_start:extra_start + extra_length]
            record_end = extra_start + extra_length + comment_length
            if record_end > len(central):
                raise RuntimeError("ZIP central-directory entry extends beyond its declared size.")

            encoding = "utf-8" if flags & (1 << 11) else "cp437"
            try:
                name = name_bytes.decode(encoding)
            except UnicodeDecodeError as exc:
                raise RuntimeError("Unable to decode a ZIP member filename.") from exc

            need_usize = uncompressed_size == 0xFFFFFFFF
            need_csize = compressed_size == 0xFFFFFFFF
            need_offset = local_header_offset == 0xFFFFFFFF
            need_disk = disk_start == 0xFFFF
            z_usize, z_csize, z_offset, z_disk = self._zip64_values(
                extra, need_usize, need_csize, need_offset, need_disk
            )
            if need_usize:
                uncompressed_size = int(z_usize)
            if need_csize:
                compressed_size = int(z_csize)
            if need_offset:
                local_header_offset = int(z_offset)
            if need_disk:
                disk_start = int(z_disk)
            if disk_start != 0:
                raise RuntimeError("ZIP member resides on another disk; unsupported.")

            entries.append(
                ZipEntry(
                    name=name,
                    flags=flags,
                    compression=compression,
                    crc32=crc32_value,
                    compressed_size=int(compressed_size),
                    uncompressed_size=int(uncompressed_size),
                    local_header_offset=int(local_header_offset),
                )
            )
            cursor = record_end

        if len(entries) != expected_entries:
            raise RuntimeError(
                f"Central directory declares {expected_entries} entries, "
                f"but {len(entries)} were parsed."
            )

        self._entries = entries
        return list(entries)

    def extract_entry(self, entry: ZipEntry, output_dir: Path,
                      max_member_bytes: int = DEFAULT_MAX_MEMBER_MIB * 1024 * 1024) -> Path:
        if entry.flags & 0x1:
            raise RuntimeError(f"Encrypted ZIP member is not supported: {entry.name}")
        if entry.uncompressed_size > max_member_bytes:
            raise RuntimeError(
                f"{entry.name} expands to {entry.uncompressed_size:,} bytes, exceeding "
                f"the configured limit of {max_member_bytes:,} bytes."
            )

        local_header = self._fetch_range(
            entry.local_header_offset, entry.local_header_offset + 29
        )
        fields = struct.unpack("<4s5H3L2H", local_header)
        if fields[0] != LOCAL_SIGNATURE:
            raise RuntimeError(f"Invalid local ZIP header for {entry.name}.")
        local_flags = fields[2]
        local_compression = fields[3]
        filename_length = fields[9]
        extra_length = fields[10]
        if local_compression != entry.compression:
            raise RuntimeError(f"Compression-method mismatch for {entry.name}.")
        if bool(local_flags & 0x1) != bool(entry.flags & 0x1):
            raise RuntimeError(f"Encryption-flag mismatch for {entry.name}.")

        data_start = entry.local_header_offset + 30 + filename_length + extra_length
        if entry.compressed_size:
            compressed = self._fetch_range(
                data_start, data_start + entry.compressed_size - 1
            )
        else:
            compressed = b""

        if entry.compression == 0:
            payload = compressed
        elif entry.compression == 8:
            try:
                payload = zlib.decompress(compressed, -15)
            except zlib.error as exc:
                raise RuntimeError(f"DEFLATE decompression failed for {entry.name}: {exc}") from exc
        else:
            raise RuntimeError(
                f"Unsupported ZIP compression method {entry.compression} for {entry.name}."
            )

        if len(payload) != entry.uncompressed_size:
            raise RuntimeError(
                f"Uncompressed size mismatch for {entry.name}: got {len(payload)}, "
                f"expected {entry.uncompressed_size}."
            )
        actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
        if actual_crc != entry.crc32:
            raise RuntimeError(
                f"CRC32 mismatch for {entry.name}: got {actual_crc:08x}, "
                f"expected {entry.crc32:08x}."
            )

        member_path = PurePosixPath(entry.name)
        if (
            member_path.is_absolute()
            or "\\" in entry.name
            or ":" in entry.name
            or any(part in ("", ".", "..") for part in member_path.parts)
        ):
            raise RuntimeError(f"Unsafe ZIP member path rejected: {entry.name!r}")

        root = output_dir.resolve()
        destination = root.joinpath(*member_path.parts).resolve()
        if destination != root and root not in destination.parents:
            raise RuntimeError(f"ZIP member would escape output directory: {entry.name}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        return destination


def find_member(entries: Iterable[ZipEntry], query: str) -> ZipEntry:
    normalized = query.replace("\\", "/").casefold()
    exact = [entry for entry in entries if entry.name.casefold() == normalized]
    matches = exact or [
        entry for entry in entries
        if PurePosixPath(entry.name).name.casefold() == normalized
    ]
    if not matches:
        raise RuntimeError(f"No ZIP member matched {query!r}. Use the 'list' command first.")
    if len(matches) > 1:
        names = "\n".join(f"  {entry.name}" for entry in matches)
        raise RuntimeError(
            f"Member name {query!r} is ambiguous. Use its full archive path:\n{names}"
        )
    return matches[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List or selectively extract a remote ZIP using HTTP Range requests."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Remote ZIP URL.")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List archive paths and sizes without downloading members.")

    extract_parser = subparsers.add_parser("extract", help="Download only the requested ZIP members.")
    extract_parser.add_argument(
        "--member", action="append", required=True,
        help="Exact member path or unique filename. Repeat to extract multiple members.",
    )
    extract_parser.add_argument(
        "--output-dir", type=Path,
        default=Path("data/raw/moon/sdem_connecting_ridge"),
        help="Destination directory (default: data/raw/moon/sdem_connecting_ridge).",
    )
    extract_parser.add_argument(
        "--max-member-mib", type=int, default=DEFAULT_MAX_MEMBER_MIB,
        help=f"Maximum uncompressed size per member (default: {DEFAULT_MAX_MEMBER_MIB} MiB).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive.")
    reader = RemoteRangeZip(args.url, timeout=args.timeout)

    if args.command == "list":
        entries = reader.list_entries()
        print(f"Remote ZIP size: {reader.file_size:,} bytes")
        print(f"Members: {len(entries)}")
        print(f"{'UNCOMPRESSED':>15} {'COMPRESSED':>15} {'METHOD':>8}  MEMBER")
        for entry in entries:
            if entry.name.endswith("/"):
                continue
            method = {0: "stored", 8: "deflate"}.get(
                entry.compression, str(entry.compression)
            )
            print(
                f"{entry.uncompressed_size:15,} {entry.compressed_size:15,} "
                f"{method:>8}  {entry.name}"
            )
        return 0

    if args.max_member_mib <= 0:
        raise SystemExit("--max-member-mib must be positive.")
    entries = reader.list_entries()
    for query in args.member:
        entry = find_member(entries, query)
        destination = reader.extract_entry(
            entry,
            args.output_dir,
            max_member_bytes=args.max_member_mib * 1024 * 1024,
        )
        print(
            f"Extracted {entry.name}\n"
            f"  -> {destination}\n"
            f"  {entry.uncompressed_size:,} bytes; CRC32 verified"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
