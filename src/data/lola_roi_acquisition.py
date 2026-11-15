"""Acquire and inspect NASA PGDA South-Pole LOLA ROI shapefile archives.

Only the five ROI archives explicitly listed on the PGDA product page are
allow-listed. This tool does not create AOIs, modify rasters, or infer which
ROI is scientifically appropriate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"
AVAILABLE_ROI_SITES = {
    "Site01": "Site01_ROIs.tgz",
    "Site04": "Site04_ROIs.tgz",
    "Site06": "Site06_ROIs.tgz",
    "Site07": "Site07_ROIs.tgz",
    "Site11": "Site11_ROIs.tgz",
}
RAW_ARCHIVE_ROOT = REPO_ROOT / "data/raw/moon/roi_archives"
EXTRACTED_ROOT = REPO_ROOT / "data/raw/moon/roi_shapes"
REPORT_ROOT = REPO_ROOT / "data/metadata/lola_rois"
GZIP_SIGNATURE = b"\x1f\x8b"
DEFAULT_MAX_ARCHIVE_MB = 50.0
MAX_MEMBERS = 5000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_roi_archive(
    site_id: str,
    destination: str | Path,
    *,
    timeout: int = 60,
    max_bytes: int = 50 * 1024 * 1024,
) -> dict[str, Any]:
    """Download one catalog-listed ROI archive without overwriting local data."""
    if site_id not in AVAILABLE_ROI_SITES:
        raise ValueError(
            f"Unknown ROI site {site_id!r}; choose from {', '.join(AVAILABLE_ROI_SITES)}"
        )
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")

    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing archive: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if partial.exists():
        raise FileExistsError(f"Refusing to overwrite existing partial archive: {partial}")

    filename = AVAILABLE_ROI_SITES[site_id]
    url = f"{BASE_URL}/{site_id}/{filename}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "AREA67-lola-roi/1.0"}
    )
    received = 0
    prefix = b""
    digest = hashlib.sha256()
    partial_created = False
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"HTTP {status} retrieving {url}")
            declared_length = response.headers.get("Content-Length")
            if declared_length is not None and int(declared_length) > max_bytes:
                raise RuntimeError(
                    f"Archive is {int(declared_length):,} bytes, above limit {max_bytes:,}"
                )
            with partial.open("xb") as output:
                partial_created = True
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > max_bytes:
                        raise RuntimeError(
                            f"Download exceeded configured limit {max_bytes:,} bytes"
                        )
                    if len(prefix) < len(GZIP_SIGNATURE):
                        prefix += chunk[: len(GZIP_SIGNATURE) - len(prefix)]
                    digest.update(chunk)
                    output.write(chunk)
        if prefix != GZIP_SIGNATURE:
            raise RuntimeError(f"Response is not a gzip archive: {url}")
        if declared_length is not None and received != int(declared_length):
            raise RuntimeError(
                f"Incomplete download: expected {declared_length}, received {received}"
            )
        # Validate the gzip/tar container before publishing the archive.
        with tarfile.open(partial, mode="r:gz") as archive:
            archive_members = archive.getmembers()
            if not archive_members:
                raise RuntimeError("ROI archive contains no members")
            if len(archive_members) > MAX_MEMBERS:
                raise RuntimeError(
                    f"ROI archive has {len(archive_members)} members; limit is {MAX_MEMBERS}"
                )
        partial.replace(destination)
        return {
            "site_id": site_id,
            "source_url": url,
            "archive_path": str(destination),
            "file_size_bytes": received,
            "sha256": digest.hexdigest(),
            "archive_member_count": len(archive_members),
        }
    except KeyboardInterrupt:
        if partial_created:
            partial.unlink(missing_ok=True)
        raise
    except Exception as exc:
        if partial_created:
            partial.unlink(missing_ok=True)
        if isinstance(exc, (ValueError, FileExistsError)):
            raise
        raise RuntimeError(f"ROI archive download failed for {site_id}: {exc}") from exc


def _safe_member_parts(member: tarfile.TarInfo) -> tuple[str, ...]:
    """Reject path traversal, links, and special files before extraction."""
    name = member.name
    if not name or "\\" in name:
        raise ValueError(f"Unsafe archive member path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or re.match(r"^[A-Za-z]:", name):
        raise ValueError(f"Absolute archive member path is not allowed: {name!r}")
    parts = tuple(part for part in path.parts if part not in ("", "."))
    if not parts or any(part == ".." for part in parts):
        raise ValueError(f"Path traversal is not allowed: {name!r}")
    if member.issym() or member.islnk() or member.isdev() or member.isfifo():
        raise ValueError(f"Links and special files are not allowed: {name!r}")
    if not (member.isdir() or member.isfile()):
        raise ValueError(f"Unsupported archive member type: {name!r}")
    return parts


def extract_roi_archive(
    archive_path: str | Path,
    destination: str | Path,
    *,
    max_uncompressed_bytes: int = 100 * 1024 * 1024,
) -> list[Path]:
    """Safely extract regular files from a tar.gz into a new destination.

    Extraction is staged and the final folder is published only after all
    members pass validation. Existing destinations are never overwritten.
    """
    archive_path = Path(archive_path)
    destination = Path(destination)
    if not archive_path.is_file():
        raise FileNotFoundError(f"ROI archive not found: {archive_path}")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite extracted ROI folder: {destination}")
    if max_uncompressed_bytes < 1:
        raise ValueError("max_uncompressed_bytes must be positive")

    staging = destination.with_name(destination.name + ".staging")
    if staging.exists():
        raise FileExistsError(f"Staging folder already exists; preserving it: {staging}")
    staging.mkdir(parents=True, exist_ok=False)
    written: list[Path] = []
    total_size = 0
    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            members = archive.getmembers()
            if len(members) > MAX_MEMBERS:
                raise ValueError(
                    f"Archive has {len(members)} members; limit is {MAX_MEMBERS}"
                )
            validated: list[tuple[tarfile.TarInfo, tuple[str, ...]]] = []
            for member in members:
                parts = _safe_member_parts(member)
                if member.isfile():
                    total_size += member.size
                    if total_size > max_uncompressed_bytes:
                        raise ValueError(
                            "ROI archive expands beyond configured uncompressed-size limit"
                        )
                validated.append((member, parts))

            for member, parts in validated:
                target = staging.joinpath(*parts)
                target_resolved = target.resolve()
                if staging.resolve() not in target_resolved.parents and target_resolved != staging.resolve():
                    raise ValueError(f"Archive member escapes extraction root: {member.name!r}")
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError(f"Could not read archive member: {member.name}")
                with source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                written.append(destination.joinpath(*parts))

        staging.replace(destination)
        return written
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def inspect_extracted_rois(site_id: str, extracted_dir: str | Path) -> dict[str, Any]:
    """Inspect shapefile geometry metadata without reprojecting or editing it."""
    if site_id not in AVAILABLE_ROI_SITES:
        raise ValueError(f"Unknown ROI site {site_id!r}")
    extracted_dir = Path(extracted_dir)
    if not extracted_dir.is_dir():
        raise FileNotFoundError(f"Extracted ROI directory not found: {extracted_dir}")

    shp_files = sorted(extracted_dir.rglob("*.shp"))
    result: dict[str, Any] = {
        "site_id": site_id,
        "status": "review_required",
        "source_catalog": "https://pgda.gsfc.nasa.gov/products/78",
        "extracted_directory": str(extracted_dir),
        "shapefile_count": len(shp_files),
        "shapefiles": [],
        "warnings": [],
        "limitations": [
            "The provider's ROI polygons are source-defined regions of interest, not automatic AREA 67 study-area approvals.",
            "No coordinate transformation, geometry repair, clipping, or resampling is performed.",
            "Area values are only reported in native CRS units squared when a projected CRS exists.",
        ],
    }
    if not shp_files:
        result["warnings"].append("No .shp files were found in the extracted archive.")
        return result

    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError("ROI geometry inspection requires geopandas from requirements.txt") from exc

    for shp_path in shp_files:
        relative_name = shp_path.relative_to(extracted_dir).as_posix()
        try:
            frame = gpd.read_file(shp_path)
        except Exception as exc:
            result["warnings"].append(
                f"{relative_name}: could not read shapefile: {type(exc).__name__}: {exc}"
            )
            continue
        geometries = frame.geometry
        geom_types = sorted(str(value) for value in geometries.geom_type.dropna().unique())
        null_count = int(geometries.isna().sum())
        empty_count = int(geometries.is_empty.sum())
        invalid_count = int(
            ((~geometries.is_valid) & (~geometries.is_empty) & geometries.notna()).sum()
        )
        usable = geometries.notna() & ~geometries.is_empty
        bounds = None
        if usable.any():
            raw_bounds = frame.loc[usable].total_bounds.tolist()
            if all(math.isfinite(float(value)) for value in raw_bounds):
                bounds = [float(value) for value in raw_bounds]
            else:
                result["warnings"].append(
                    f"{relative_name}: geometry bounds include non-finite values."
                )
        projected = bool(frame.crs and not frame.crs.is_geographic)
        area_native_units2 = (
            float(geometries.area.sum()) if projected and usable.any() else None
        )
        item = {
            "shapefile": relative_name,
            "feature_count": int(len(frame)),
            "crs": frame.crs.to_string() if frame.crs else None,
            "geometry_types": geom_types,
            "bounds": bounds,
            "null_geometry_count": null_count,
            "empty_geometry_count": empty_count,
            "invalid_geometry_count": invalid_count,
            "area_native_units2": area_native_units2,
            "fields": [str(column) for column in frame.columns if column != frame.geometry.name],
        }
        if frame.crs is None:
            result["warnings"].append(
                f"{item['shapefile']}: CRS is missing; do not guess or reproject."
            )
        if null_count:
            result["warnings"].append(
                f"{item['shapefile']}: {null_count} features have null geometries."
            )
        if invalid_count:
            result["warnings"].append(
                f"{item['shapefile']}: {invalid_count} invalid geometries require review."
            )
        result["shapefiles"].append(item)

    result["status"] = "review_required" if result["warnings"] else "inventory_complete"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    download = sub.add_parser("download", help="Download official PGDA ROI archives")
    download.add_argument("--sites", nargs="+", choices=tuple(AVAILABLE_ROI_SITES), required=True)
    download.add_argument("--confirm-download", action="store_true")
    download.add_argument("--max-archive-mb", type=float, default=DEFAULT_MAX_ARCHIVE_MB)

    inspect = sub.add_parser("inspect", help="Safely extract and inventory downloaded ROI archives")
    inspect.add_argument("--sites", nargs="+", choices=tuple(AVAILABLE_ROI_SITES), required=True)
    inspect.add_argument("--max-uncompressed-mb", type=float, default=100.0)

    args = parser.parse_args(argv)
    try:
        if args.command == "download":
            if not args.confirm_download:
                parser.error("download requires --confirm-download after reviewing the selected sites")
            if args.max_archive_mb <= 0:
                parser.error("--max-archive-mb must be positive")
            for site_id in args.sites:
                destination = RAW_ARCHIVE_ROOT / site_id / AVAILABLE_ROI_SITES[site_id]
                if destination.exists():
                    print(f"Already present; leaving unchanged: {destination}")
                    continue
                result = download_roi_archive(
                    site_id, destination, max_bytes=int(args.max_archive_mb * 1024 * 1024)
                )
                print(json.dumps(result, indent=2))

        else:
            if args.max_uncompressed_mb <= 0:
                parser.error("--max-uncompressed-mb must be positive")
            for site_id in args.sites:
                archive = RAW_ARCHIVE_ROOT / site_id / AVAILABLE_ROI_SITES[site_id]
                extracted = EXTRACTED_ROOT / site_id
                if not extracted.exists():
                    extract_roi_archive(
                        archive, extracted,
                        max_uncompressed_bytes=int(args.max_uncompressed_mb * 1024 * 1024),
                    )
                report = inspect_extracted_rois(site_id, extracted)
                report_path = REPORT_ROOT / f"{site_id}_roi_inspection.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    json.dumps(report, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                )
                print(json.dumps(report, indent=2))
                print(f"Inspection report: {report_path}")
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, OSError, tarfile.TarError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
