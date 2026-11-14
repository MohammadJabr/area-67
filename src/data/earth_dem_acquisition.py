"""Acquire explicitly selected, public Copernicus GLO-30 candidate tiles."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

import rasterio


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = REPO_ROOT / "data" / "raw" / "earth" / "copdem_glo30"
BASE_URL = "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
# Coordinates identify provisional candidate landmarks only. They are not AOIs.
CANDIDATE_TILES = {
    "haughton": "Copernicus_DSM_COG_10_N75_00_W090_00_DEM",
    "mcmurdo": "Copernicus_DSM_COG_10_S78_00_E162_00_DEM",
    "askja": "Copernicus_DSM_COG_10_N65_00_W017_00_DEM",
    "mauna_kea": "Copernicus_DSM_COG_10_N19_00_W156_00_DEM",
    "yungay": "Copernicus_DSM_COG_10_S25_00_W070_00_DEM",
}
TIFF_SIGNATURES = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")


def download_tile(
    site_id: str,
    destination: str | Path,
    *,
    timeout: int = 60,
    max_bytes: int = 100 * 1024 * 1024,
) -> dict[str, Any]:
    """Download one allow-listed source COG; never overwrite an existing file."""
    if site_id not in CANDIDATE_TILES:
        raise ValueError(f"Unknown candidate {site_id!r}; choose from {', '.join(CANDIDATE_TILES)}")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing raster: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if partial.exists():
        raise FileExistsError(f"Refusing to overwrite existing partial download: {partial}")

    tile = CANDIDATE_TILES[site_id]
    url = f"{BASE_URL}/{tile}/{tile}.tif"
    request = urllib.request.Request(url, headers={"User-Agent": "AREA67-earth-dem/1.0"})
    digest = hashlib.sha256()
    received = 0
    prefix = b""
    partial_created = False
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"HTTP {status} retrieving {url}")
            declared_length = response.headers.get("Content-Length")
            if declared_length is not None and int(declared_length) > max_bytes:
                raise RuntimeError(
                    f"Tile is {int(declared_length):,} bytes, above configured limit {max_bytes:,}"
                )
            with partial.open("xb") as output:
                partial_created = True
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > max_bytes:
                        raise RuntimeError(f"Download exceeded configured limit {max_bytes:,} bytes")
                    if len(prefix) < 4:
                        prefix += chunk[:4 - len(prefix)]
                    digest.update(chunk)
                    output.write(chunk)
        if prefix not in TIFF_SIGNATURES:
            raise RuntimeError(f"Response is not a TIFF/BigTIFF file: {url}")
        if declared_length is not None and received != int(declared_length):
            raise RuntimeError(f"Incomplete download: expected {declared_length}, received {received}")
        with rasterio.open(partial) as dataset:
            if dataset.count != 1:
                raise RuntimeError(f"Expected one DEM band, received {dataset.count}")
            if dataset.crs is None:
                raise RuntimeError("Downloaded DEM has no declared CRS")
            metadata = {
                "width": dataset.width,
                "height": dataset.height,
                "crs": dataset.crs.to_string(),
                "transform": list(dataset.transform)[:6],
                "nodata": dataset.nodata if dataset.nodata is not None else None,
            }
        partial.replace(destination)
        return {
            "site_id": site_id,
            "source_id": tile,
            "source_url": url,
            "path": str(destination),
            "file_size_bytes": received,
            "sha256": digest.hexdigest(),
            "raster_metadata": metadata,
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
        raise RuntimeError(f"Acquisition failed for {url}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", nargs="+", choices=tuple(CANDIDATE_TILES), required=True)
    parser.add_argument("--confirm-download", action="store_true", help="Acknowledge retrieval of the named source tiles")
    parser.add_argument("--max-file-mb", type=float, default=100.0, help="Per-file safety limit; default 100 MiB")
    args = parser.parse_args(argv)
    if not args.confirm_download:
        parser.error("download requires --confirm-download after reviewing selected sites")
    if args.max_file_mb <= 0:
        parser.error("--max-file-mb must be positive")
    results = []
    try:
        for site_id in args.sites:
            tile = CANDIDATE_TILES[site_id]
            destination = RAW_ROOT / site_id / f"{tile}.tif"
            results.append(download_tile(site_id, destination, max_bytes=int(args.max_file_mb * 1024 * 1024)))
            print(f"Downloaded {site_id}: {destination} ({results[-1]['file_size_bytes']:,} bytes)")
        print(json.dumps(results, indent=2))
        return 0
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError, OSError, rasterio.errors.RasterioError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
