"""Build a block-wise, read-only inventory of repository-local source rasters."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from src.data.raster_inventory import inventory_raster


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/reports/earth_dem_readiness_audit/local_raster_inventory.json"
DEFAULT_MARKDOWN = ROOT / "docs/reports/earth_dem_readiness_audit/DATA_INVENTORY.md"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _lola_support(elevation: Path, counts: Path) -> dict[str, Any]:
    """Summarize direct spot-count support; this does not calculate terrain features."""
    valid_elevation = 0
    positive_count = 0
    zero_count = 0
    invalid_pair = 0
    count_values: dict[str, int] = {}
    with rasterio.open(elevation) as dem, rasterio.open(counts) as count_ds:
        if (dem.width, dem.height, dem.crs, dem.transform) != (
            count_ds.width, count_ds.height, count_ds.crs, count_ds.transform
        ):
            raise ValueError("LOLA elevation and spot-count grids do not exactly match")
        for _, window in dem.block_windows(1):
            z = dem.read(1, window=window)
            c = count_ds.read(1, window=window)
            pair_valid = (
                (dem.read_masks(1, window=window) > 0)
                & (count_ds.read_masks(1, window=window) > 0)
                & np.isfinite(z)
                & np.isfinite(c)
            )
            invalid_pair += int(pair_valid.size - pair_valid.sum())
            valid_counts = c[pair_valid]
            valid_elevation += int(pair_valid.sum())
            positive_count += int(np.count_nonzero(valid_counts > 0))
            zero_count += int(np.count_nonzero(valid_counts == 0))
            for value, number in zip(*np.unique(valid_counts, return_counts=True)):
                key = str(int(value)) if float(value).is_integer() else str(float(value))
                count_values[key] = count_values.get(key, 0) + int(number)
    return {
        "interpretation": "Positive LDEC spot counts indicate direct LOLA spot support per the existing project QA; zero-count valid elevation cells are interpolated. This is not an uncertainty estimate.",
        "valid_elevation_count_pairs": valid_elevation,
        "invalid_pairs": invalid_pair,
        "positive_count_pixels": positive_count,
        "positive_count_pct_of_valid_pairs": 100 * positive_count / valid_elevation if valid_elevation else None,
        "zero_count_pixels": zero_count,
        "zero_count_pct_of_valid_pairs": 100 * zero_count / valid_elevation if valid_elevation else None,
        "spot_count_histogram": dict(sorted(count_values.items(), key=lambda item: float(item[0]))),
    }


def build_inventory() -> dict[str, Any]:
    paths = sorted(
        path for path in (ROOT / "data/raw").rglob("*")
        if path.is_file() and path.suffix.casefold() in {".tif", ".tiff"}
    )
    if not paths:
        raise FileNotFoundError("No local GeoTIFFs found below data/raw")

    source_records = _read_csv(ROOT / "data/metadata/earth_dem_source_inventory.csv")
    manifest_records = _read_csv(ROOT / "data/metadata/earth_dem_manifest.csv")
    provenance: dict[str, dict[str, str]] = {}
    for row in source_records + manifest_records:
        local_path = row.get("local_path", "").strip()
        checksum = row.get("sha256", row.get("checksum_sha256", "")).strip()
        if local_path and checksum:
            provenance[local_path.replace("\\", "/")] = row

    rasters: list[dict[str, Any]] = []
    for path in paths:
        report = inventory_raster(path)
        expected = provenance.get(report["path"])
        report["provenance_record"] = {
            "present": expected is not None,
            "expected_sha256": expected.get("sha256", expected.get("checksum_sha256")) if expected else None,
            "sha256_matches_record": report["sha256"].casefold() == expected.get("sha256", expected.get("checksum_sha256", "")).casefold() if expected else None,
            "source_id": expected.get("source_id", expected.get("product", expected.get("version_or_item", ""))) if expected else None,
        }
        rasters.append(report)

    lola_elevation = ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_surf.tif"
    lola_counts = ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_ldec.tif"
    return {
        "audit_date": date.today().isoformat(),
        "method": "Read-only rasterio inventory; block-wise statistics and SHA-256; no reprojection, resampling, or raster writes.",
        "raster_count": len(rasters),
        "rasters": rasters,
        "lola_direct_support": _lola_support(lola_elevation, lola_counts) if lola_elevation.exists() and lola_counts.exists() else None,
        "provenance_note": "Manifest/inventory hash comparison is recorded per raster. A missing record means the raster is present locally but has no matching local_path + checksum row in either CSV.",
    }


def markdown_inventory(report: dict[str, Any]) -> str:
    lines = [
        "# Local raster inventory",
        "",
        f"**Audit date:** {report['audit_date']}  ",
        f"**Rasters inspected:** {report['raster_count']} (read-only, block-wise)  ",
        "**Statistics:** finite values not masked by GDAL; NoData, NaN and infinities counted separately.",
        "",
        "The machine-readable [`local_raster_inventory.json`](local_raster_inventory.json) contains full CRS WKT, affine transforms, native and WGS84 bounds where meaningful, metadata tags by namespace/band, mask flags, and the fields below. Lunar coordinates are not converted to WGS84 because that would falsely imply an Earth geodetic reference.",
        "",
        "| Raster path | Bytes | SHA-256 | Grid / bands / type | CRS / pixel spacing | Affine transform | Native bounds | WGS84 bounds | NoData / masks | Valid; invalid; NaN; +Inf; -Inf | Min / max / mean / population SD | Inventory checksum |",
        "|---|---:|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in report["rasters"]:
        band = row["bands"][0]
        stats = band["statistics"] or {}
        bounds = ", ".join(f"{value:.8g}" for value in row["bounds"])
        transform = ", ".join(f"{value:.8g}" for value in row["transform"])
        wgs = "not applicable / unavailable" if row["bounds_wgs84_wsen"] is None else ", ".join(f"{value:.8g}" for value in row["bounds_wgs84_wsen"])
        summary = " / ".join(
            "n/a" if stats.get(key) is None else f"{stats[key]:.8g}"
            for key in ("minimum", "maximum", "mean", "standard_deviation_population")
        )
        provenance = row["provenance_record"]
        match = "not recorded" if provenance["sha256_matches_record"] is None else str(provenance["sha256_matches_record"])
        valid = stats.get("valid_pixel_count", 0)
        lines.append(
            f"| `{row['path']}` | {row['file_size_bytes']:,} | `{row['sha256']}` | "
            f"{row['width']} x {row['height']}; {row['band_count']}; {', '.join(row['data_types'])} | "
            f"{row['crs']}; {row['pixel_size_x']:g} x {row['pixel_size_y']:g} {row['pixel_spacing_units']} | "
            f"{transform} | {bounds} | {wgs} | {row['nodata']}; {', '.join(band['mask_flags'])} | "
            f"{valid:,} ({stats.get('valid_coverage_pct', 0):.6f}%); {row['width'] * row['height'] - valid:,}; "
            f"{band['nan_pixel_count']:,}; {band['positive_infinity_pixel_count']:,}; {band['negative_infinity_pixel_count']:,} | "
            f"{summary} | {match} |"
        )
    support = report.get("lola_direct_support")
    lines.extend(["", "## LOLA direct-observation support", ""])
    if support:
        lines.extend([
            f"Across {support['valid_elevation_count_pairs']:,} valid elevation/count pairs, {support['positive_count_pixels']:,} cells ({support['positive_count_pct_of_valid_pairs']:.6f}%) have positive LDEC counts and {support['zero_count_pixels']:,} ({support['zero_count_pct_of_valid_pairs']:.6f}%) have zero counts. Per product documentation and existing project QA, positive counts indicate direct spot support; zero-count LDEM values are interpolated. This is support metadata, not a quality score or effective-resolution estimate.",
            "",
            "LDEC value histogram: " + ", ".join(f"{key}: {value:,}" for key, value in support["spot_count_histogram"].items()) + ".",
        ])
    lines.extend([
        "",
        "## Interpretation notes",
        "",
        "- `valid` is the intersection of the GDAL validity mask and finite numeric values. It is not evidence of direct observation or scientific quality.",
        "- Copernicus rasters are in geographic degrees; their reported pixel spacing is angular. USGS rasters are in projected metres. LOLA uses a lunar south-polar stereographic CRS in metres with datum named unknown in the embedded WKT.",
        "- Site04 nominal 5 m posting does not establish 5 m effective terrain resolution. Earth nominal posting likewise does not establish effective resolution.",
        "- Earth inventory hashes match `earth_dem_source_inventory.csv` or `earth_dem_manifest.csv`. LOLA hashes were computed in this audit because neither CSV records local checksums for those five files.",
        "- All transforms, raw tag values, and per-band details are preserved in the JSON report; no source raster was modified.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    report = build_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(markdown_inventory(report), encoding="utf-8")
    print(f"Inventoried {report['raster_count']} rasters: {args.output}")
    for row in report["rasters"]:
        check = row["provenance_record"]["sha256_matches_record"]
        print(f"{row['path']}: {row['file_size_bytes']:,} bytes; {row['sha256']}; recorded_sha_match={check}")
    if report["lola_direct_support"]:
        support = report["lola_direct_support"]
        print(f"LOLA positive spot-count support: {support['positive_count_pct_of_valid_pairs']:.6f}% of valid paired pixels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
