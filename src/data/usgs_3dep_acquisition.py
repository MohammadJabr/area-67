"""Safely acquire the catalog-verified Mauna Kea USGS 3DEP 1 m tile."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable

import rasterio
from pyproj import Transformer


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "646eeb74d34e4e58932cf87e"
TILE_ID = "USGS_1M_4_x86y220_HI_Hawaii_Island_Lidar_NOAA_2017_B17"
SOURCE_URL = (
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/"
    "HI_Hawaii_Island_Lidar_NOAA_2017_B17/TIFF/" + TILE_ID + ".tif"
)
EXPECTED_SIZE = 270_812_447
SITE_LON, SITE_LAT = -155.47, 19.82
DEFAULT_DESTINATION = (
    REPO_ROOT / "data/raw/earth/mauna_kea/usgs_3dep/1m" / f"{TILE_ID}.tif"
)
TIFF_SIGNATURES = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def acquire_tile(
    destination: str | Path = DEFAULT_DESTINATION,
    *,
    expected_sha256: str | None = None,
    expected_size: int = EXPECTED_SIZE,
    open_url: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    """Download only the catalog-listed tile; resume .part files and never overwrite.

    A complete existing target is only accepted when its checksum is explicitly
    supplied and matches. Interrupted partials remain available for safe resume.
    """
    destination = Path(destination)
    if expected_size <= 0:
        raise ValueError("expected_size must be positive")
    if destination.exists():
        digest = _sha256(destination)
        if expected_sha256 and digest.lower() == expected_sha256.lower():
            return {"status": "skipped_verified", "path": str(destination),
                    "file_size_bytes": destination.stat().st_size, "sha256": digest}
        raise FileExistsError(
            f"Refusing to overwrite existing file; provide its verified matching SHA-256 to skip: {destination}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > expected_size:
        raise ValueError(f"Existing partial exceeds expected tile size: {offset} > {expected_size}")
    headers = {"User-Agent": "AREA67-USGS-3DEP/1.0"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(SOURCE_URL, headers=headers)
    with open_url(request, timeout=90) as response:
        status = getattr(response, "status", 200)
        if offset:
            content_range = response.headers.get("Content-Range", "")
            if status != 206 or not content_range.startswith(f"bytes {offset}-"):
                raise RuntimeError(f"Server did not honor resume range at byte {offset}: HTTP {status}")
        elif status != 200:
            raise RuntimeError(f"Unexpected HTTP status {status} retrieving the USGS tile")
        declared = response.headers.get("Content-Length")
        expected_chunk = expected_size - offset
        if declared is not None and int(declared) != expected_chunk:
            raise RuntimeError(f"Unexpected response length {declared}; expected {expected_chunk}")
        mode = "ab" if offset else "xb"
        with partial.open(mode) as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                if output.tell() > expected_size:
                    raise RuntimeError("Response exceeded the catalog file size; partial retained")

    if not partial.exists() or partial.stat().st_size != expected_size:
        actual = partial.stat().st_size if partial.exists() else 0
        raise RuntimeError(f"Incomplete tile retained at {partial}: {actual} of {expected_size} bytes")
    with partial.open("rb") as stream:
        if stream.read(4) not in TIFF_SIGNATURES:
            raise RuntimeError("Downloaded object is not a TIFF/BigTIFF; partial retained")
    with rasterio.open(partial) as dataset:
        if dataset.count != 1 or dataset.crs is None:
            raise RuntimeError("Expected a single-band georeferenced DEM; partial retained")
        x, y = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True).transform(SITE_LON, SITE_LAT)
        bounds = dataset.bounds
        if not (bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top):
            raise RuntimeError("Catalog provisional coordinate is outside the downloaded tile; partial retained")
        metadata = {
            "width": dataset.width, "height": dataset.height, "band_count": dataset.count,
            "dtype": dataset.dtypes[0], "crs": dataset.crs.to_string(),
            "transform": list(dataset.transform)[:6], "bounds": list(bounds),
            "pixel_size": list(dataset.res), "nodata": dataset.nodata,
            "site_coordinate_covered": True,
        }
    digest = _sha256(partial)
    partial.replace(destination)
    return {
        "status": "downloaded", "source_id": SOURCE_ID, "tile_id": TILE_ID,
        "source_url": SOURCE_URL, "path": str(destination),
        "file_size_bytes": destination.stat().st_size, "sha256": digest,
        "raster_metadata": metadata,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-download", action="store_true", help="Required explicit confirmation")
    parser.add_argument("--expected-sha256", help="Only used to skip an existing verified complete tile")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args(argv)
    if not args.confirm_download:
        parser.error("supply --confirm-download after reviewing the allow-listed source")
    try:
        print(json.dumps(acquire_tile(args.destination, expected_sha256=args.expected_sha256), indent=2))
        return 0
    except (FileExistsError, RuntimeError, ValueError, OSError, rasterio.errors.RasterioError) as exc:
        print(f"ACQUISITION FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
