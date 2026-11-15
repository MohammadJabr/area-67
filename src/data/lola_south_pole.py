"""Download and inspect approved-list NASA PGDA LOLA south-pole site rasters.

This supplements the original Site04 workflow with the other PGDA sites that
have a published ROI archive. Downloads are explicit, size-limited, and never
overwrite existing local files. No optional clone products are downloaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

import rasterio

try:
    from .lola_site04 import ASSETS, inspect_raster
    from .lola_site04_qa import run as run_qa
except ImportError:  # direct script execution from the repository root
    from lola_site04 import ASSETS, inspect_raster
    from lola_site04_qa import run as run_qa

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"
# These five sites have explicit ROI shapefile archives on the PGDA product page.
SITES = {
    "Site01": {"name": "Connecting ridge", "directory": "site01"},
    "Site04": {"name": "Shackleton rim", "directory": "site04"},
    "Site06": {"name": "Nobile rim 1", "directory": "site06"},
    "Site07": {"name": "Peak near Shackleton", "directory": "site07"},
    "Site11": {"name": "de Gerlache rim", "directory": "site11"},
}
RAW_ROOT = REPO_ROOT / "data/raw/moon"
INSPECTION_ROOT = REPO_ROOT / "data/metadata/lola_south_pole"


def asset_filename(site_id: str, asset_name: str) -> str:
    if site_id not in SITES:
        raise ValueError(f"Unknown site {site_id!r}; choose from {', '.join(SITES)}")
    if asset_name not in ASSETS:
        raise ValueError(f"Unknown asset {asset_name!r}; choose from {', '.join(ASSETS)}")
    suffix = ASSETS[asset_name].removeprefix("Site04")
    return f"{site_id}{suffix}"


def asset_url(site_id: str, asset_name: str) -> str:
    filename = asset_filename(site_id, asset_name)
    return f"{BASE_URL}/{site_id}/{filename}"


def download_site_asset(
    site_id: str,
    asset_name: str,
    destination: str | Path,
    *,
    timeout: int = 60,
    max_bytes: int = 100 * 1024 * 1024,
) -> dict[str, Any]:
    """Stream a single catalog-listed GeoTIFF to disk without overwriting."""
    url = asset_url(site_id, asset_name)
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing raster: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if partial.exists():
        raise FileExistsError(f"Refusing to overwrite existing partial raster: {partial}")

    request = urllib.request.Request(url, headers={"User-Agent": "AREA67-lola-data/1.0"})
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
                    f"Raster is {int(declared_length):,} bytes, above limit {max_bytes:,}"
                )
            with partial.open("xb") as output:
                partial_created = True
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > max_bytes:
                        raise RuntimeError(
                            f"Download exceeded configured limit {max_bytes:,} bytes"
                        )
                    if len(prefix) < 4:
                        prefix += chunk[:4 - len(prefix)]
                    digest.update(chunk)
                    output.write(chunk)
        if prefix not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            raise RuntimeError(f"Response is not a TIFF/BigTIFF file: {url}")
        if declared_length is not None and received != int(declared_length):
            raise RuntimeError(
                f"Incomplete download: expected {declared_length}, received {received}"
            )
        with rasterio.open(partial) as dataset:
            if dataset.count != 1:
                raise RuntimeError(f"Expected one DEM band, received {dataset.count}")
            if dataset.crs is None:
                raise RuntimeError("Downloaded raster has no declared CRS")
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
            "site_name": SITES[site_id]["name"],
            "asset": asset_name,
            "source_id": Path(url).name,
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
        raise RuntimeError(f"LOLA acquisition failed for {site_id}/{asset_name}: {exc}") from exc


def site_asset_paths(site_id: str, asset_names: list[str]) -> dict[str, Path]:
    if site_id not in SITES:
        raise ValueError(f"Unknown site {site_id!r}; choose from {', '.join(SITES)}")
    site_dir = RAW_ROOT / SITES[site_id]["directory"]
    return {
        asset_name: site_dir / asset_filename(site_id, asset_name)
        for asset_name in asset_names
    }


def download_requested_assets(
    site_ids: list[str],
    asset_names: list[str],
    *,
    max_bytes: int,
) -> list[tuple[str, str]]:
    """Attempt every selected site/layer and preserve successful local rasters.

    A provider error for one asset must not prevent other requested assets
    from downloading. Existing files are skipped and never overwritten.
    The returned (site_id, asset_name) pairs identify any failed downloads.
    """
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")

    failures: list[tuple[str, str]] = []
    for site_id in site_ids:
        paths = site_asset_paths(site_id, asset_names)
        for asset_name, destination in paths.items():
            if destination.exists():
                print(f"Already present; leaving unchanged: {destination}")
                continue
            try:
                result = download_site_asset(
                    site_id,
                    asset_name,
                    destination,
                    max_bytes=max_bytes,
                )
                print(json.dumps(result, indent=2))
            except Exception as exc:
                failures.append((site_id, asset_name))
                print(
                    f"ERROR downloading {site_id}/{asset_name}: "
                    f"{type(exc).__name__}: {exc}"
                )

    if failures:
        failed_items = ", ".join(f"{site}/{asset}" for site, asset in failures)
        print(
            "Raster batch completed with failures for: "
            + failed_items
            + ". Successful files were preserved."
        )
    else:
        print("All requested LOLA raster assets are available locally.")
    return failures


def inspect_site(site_id: str, asset_names: list[str]) -> dict[str, Any]:
    paths = site_asset_paths(site_id, asset_names)
    report = {
        "site_id": site_id,
        "site_name": SITES[site_id]["name"],
        "status": "provisional NASA south-pole target; not an AREA 67 team-approved target",
        "source_catalog": "https://pgda.gsfc.nasa.gov/products/78",
        "assets": {},
    }
    for name, path in paths.items():
        report["assets"][name] = inspect_raster(path)
    return report


def run_site_qa(site_id: str) -> dict[str, Any]:
    """Run the existing five-layer QA on one additional PGDA site."""
    paths = site_asset_paths(site_id, list(ASSETS))
    report = run_qa(paths)
    report["study_area"] = f"NASA LOLA {site_id} ({SITES[site_id]['name']})"
    report["status_note"] = (
        "Provisional NASA south-pole target; QA is structural and descriptive, "
        "not an AREA 67 target or AOI approval."
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    download = sub.add_parser("download", help="Download selected NASA PGDA site rasters")
    download.add_argument("--sites", nargs="+", choices=tuple(SITES), required=True)
    download.add_argument("--assets", nargs="+", choices=tuple(ASSETS), required=True)
    download.add_argument("--confirm-download", action="store_true")
    download.add_argument("--max-file-mb", type=float, default=100.0)

    inspect = sub.add_parser("inspect", help="Inspect selected downloaded site rasters")
    inspect.add_argument("--sites", nargs="+", choices=tuple(SITES), required=True)
    inspect.add_argument("--assets", nargs="+", choices=tuple(ASSETS), required=True)

    qa = sub.add_parser("qa", help="Run exact-grid and LDEC/uncertainty QA")
    qa.add_argument("--sites", nargs="+", choices=tuple(SITES), required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "download":
            if not args.confirm_download:
                parser.error("download requires --confirm-download after reviewing selected assets")
            if args.max_file_mb <= 0:
                parser.error("--max-file-mb must be positive")
            failures = download_requested_assets(
                args.sites,
                args.assets,
                max_bytes=int(args.max_file_mb * 1024 * 1024),
            )
            if failures:
                return 1

        elif args.command == "inspect":
            for site_id in args.sites:
                report = inspect_site(site_id, args.assets)
                report_path = INSPECTION_ROOT / f"{site_id}_inspection.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    json.dumps(report, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                )
                print(json.dumps(report, indent=2))
                print(f"Inspection report: {report_path}")

        else:
            for site_id in args.sites:
                report = run_site_qa(site_id)
                report_path = INSPECTION_ROOT / f"{site_id}_qa.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    json.dumps(report, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                )
                print(
                    f"{site_id}: exact_grid_alignment="
                    f"{report['grid_qa']['exact_metadata_grid_alignment']}; "
                    f"positive_LDEC_pct="
                    f"{report['layers']['counts']['direct_observation_support']['positive_count_pixel_pct_of_valid']:.4f}"
                )
                print(f"QA report: {report_path}")
        return 0
    except (
        FileExistsError, FileNotFoundError, RuntimeError, ValueError, OSError,
        rasterio.errors.RasterioError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
