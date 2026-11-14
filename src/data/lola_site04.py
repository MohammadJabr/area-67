"""Download and inspect NASA GSFC PGDA's lunar LOLA Site04 rasters.

The study area is a provisional choice: Site04 (Shackleton rim). This script
downloads only the explicitly selected assets and never downloads the 100
optional clone rasters.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "moon" / "site04"
REPORT_PATH = REPO_ROOT / "data" / "metadata" / "site04_inspection.json"
BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site04/"
ASSETS = {
    "elevation": "Site04_final_adj_5mpp_surf.tif",
    "counts": "Site04_final_adj_5mpp_ldec.tif",
    "slope": "Site04_final_adj_5mpp_slp.tif",
    "z_uncertainty": "Site04_final_adj_5mpp_toterr.tif",
    "slope_uncertainty": "Site04_final_adj_5mpp_slperr.tif",
}


def download_asset(name: str, destination: Path, timeout: int = 60) -> Path:
    """Stream one catalog-listed asset to disk; remove partial files on error."""
    if name not in ASSETS:
        raise ValueError(f"Unknown asset {name!r}; choose from: {', '.join(ASSETS)}")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing data: {destination}")
    url = BASE_URL + ASSETS[name]
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if partial.exists():
        raise FileExistsError(f"Partial download already exists; preserving it: {partial}")
    request = urllib.request.Request(url, headers={"User-Agent": "AREA67-data-workflow/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, partial.open("wb") as out:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"HTTP {status} downloading {url}")
            expected_length = response.headers.get("Content-Length")
            received = 0
            prefix = b""
            while chunk := response.read(1024 * 1024):
                if len(prefix) < 4:
                    prefix += chunk[:4 - len(prefix)]
                out.write(chunk)
                received += len(chunk)
        if prefix not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            raise RuntimeError(f"Response is not a TIFF file (unexpected header) from {url}")
        if expected_length is not None and received != int(expected_length):
            raise RuntimeError(f"Incomplete response: expected {expected_length} bytes, received {received}")
        if partial.stat().st_size == 0:
            raise RuntimeError(f"Server returned an empty file for {url}")
        partial.replace(destination)
        return destination
    except KeyboardInterrupt:
        partial.unlink(missing_ok=True)
        raise
    except Exception as exc:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"Download failed for {url}: {exc}") from exc


def inspect_raster(path: Path) -> dict[str, Any]:
    """Read raster metadata and streaming statistics without altering the raster."""
    try:
        import numpy as np
        import rasterio
    except ImportError as exc:
        raise RuntimeError("Raster inspection requires numpy and rasterio from requirements.txt") from exc

    if not path.is_file():
        raise FileNotFoundError(f"Raster not found: {path}. Run the download command first.")

    try:
        with rasterio.open(path) as ds:
            valid_count = 0
            gdal_valid_count = 0
            nodata_masked_count = 0
            nonfinite_count = 0
            value_min = math.inf
            value_max = -math.inf
            value_sum = 0.0
            value_sum_sq = 0.0
            for _, window in ds.block_windows(1):
                block = ds.read(1, window=window)
                gdal_valid = ds.read_masks(1, window=window) > 0
                finite = np.isfinite(block)
                valid = gdal_valid & finite
                gdal_valid_count += int(gdal_valid.sum())
                nodata_masked_count += int((~gdal_valid).sum())
                nonfinite_count += int((~finite).sum())
                values = block[valid].astype("float64", copy=False)
                if values.size:
                    valid_count += int(values.size)
                    value_min = min(value_min, float(values.min()))
                    value_max = max(value_max, float(values.max()))
                    value_sum += float(values.sum(dtype="float64"))
                    value_sum_sq += float(np.square(values).sum(dtype="float64"))

            stats = None
            if valid_count:
                mean = value_sum / valid_count
                variance = max(0.0, value_sum_sq / valid_count - mean * mean)
                stats = {
                    "valid_pixel_count": valid_count,
                    "valid_coverage_pct": 100.0 * valid_count / (ds.width * ds.height),
                    "minimum": value_min,
                    "maximum": value_max,
                    "mean": mean,
                    "standard_deviation_population": math.sqrt(variance),
                }

            nodata_value = ds.nodata
            if isinstance(nodata_value, float) and math.isnan(nodata_value):
                nodata_value = "NaN"
            return {
                "path": path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else str(path),
                "gdal_valid_pixel_count": gdal_valid_count,
                "nodata_masked_pixel_count": nodata_masked_count,
                "nonfinite_pixel_count_band_1": nonfinite_count,
                "file_size_bytes": path.stat().st_size,
                "driver": ds.driver,
                "width_pixels": ds.width,
                "height_pixels": ds.height,
                "band_count": ds.count,
                "data_types": list(ds.dtypes),
                "nodata": nodata_value,
                "crs": ds.crs.to_string() if ds.crs else None,
                "transform": list(ds.transform)[:6],
                "bounds": list(ds.bounds),
                "pixel_size_x": ds.res[0],
                "pixel_size_y": ds.res[1],
                "statistics_band_1": stats,
            }
    except Exception as exc:
        if isinstance(exc, (FileNotFoundError, RuntimeError)):
            raise
        raise RuntimeError(f"Could not inspect raster {path}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    dl = sub.add_parser("download", help="Download selected catalog-listed assets")
    dl.add_argument("--assets", nargs="+", choices=ASSETS, required=True,
                    help="Explicit asset names; no asset is selected by default")
    dl.add_argument("--confirm-download", action="store_true",
                    help="Required acknowledgement before network download")
    ins = sub.add_parser("inspect", help="Inspect downloaded rasters and write a JSON report")
    ins.add_argument("--assets", nargs="+", choices=tuple(ASSETS), default=["elevation"])
    ins.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)

    try:
        if args.command == "download":
            if not args.confirm_download:
                parser.error("download requires --confirm-download after reviewing the listed assets")
            for name in args.assets:
                path = RAW_DIR / ASSETS[name]
                if path.exists():
                    print(f"Already present; leaving unchanged: {path}")
                    continue
                result = download_asset(name, path)
                print(f"Downloaded {name}: {result} ({result.stat().st_size:,} bytes)")
            return 0

        report = {
            "study_area": "NASA LOLA Site04 (Shackleton rim)",
            "status": "provisional study-area choice; not an officially approved team decision",
            "source_catalog": "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/",
            "assets": {},
        }
        for name in args.assets:
            report["assets"][name] = inspect_raster(RAW_DIR / ASSETS[name])
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        print(f"Inspection report written to {args.report}")
        return 0
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
