"""Configurable read-only QA for an Earth DEM and optional quality rasters."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import rasterio

try:  # Supports both ``python -m src.data.earth_dem_qa`` and direct script use.
    from .raster_inventory import inventory_raster
except ImportError:  # pragma: no cover - exercised by the documented CLI form
    from raster_inventory import inventory_raster


def _grid_signature(ds: rasterio.io.DatasetReader) -> tuple[Any, ...]:
    return ds.width, ds.height, ds.crs.to_wkt() if ds.crs else None, tuple(ds.transform)[:6]


def build_qa_report(
    dem_path: str | Path,
    quality_layers: dict[str, str | Path] | None = None,
    *,
    checksum: bool = True,
    elevation_range: tuple[float, float] | None = None,
) -> dict[str, Any]:
    """Inventory a primary DEM and check optional companion layer alignment."""
    quality_layers = quality_layers or {}
    dem = inventory_raster(dem_path, checksum=checksum, elevation_range=elevation_range)
    warnings: list[str] = []
    if dem["crs"] is None:
        warnings.append("DEM has no declared CRS")
    if dem["band_count"] != 1:
        warnings.append(f"DEM has {dem['band_count']} bands; confirm the intended elevation band")
    if not any(band["statistics"] for band in dem["bands"]):
        warnings.append("DEM has no finite, GDAL-valid values")

    companions: list[dict[str, Any]] = []
    with rasterio.open(dem_path) as reference:
        reference_grid = _grid_signature(reference)
    for name, path in quality_layers.items():
        companion = inventory_raster(path, checksum=checksum)
        with rasterio.open(path) as dataset:
            aligned = _grid_signature(dataset) == reference_grid
        companions.append({"name": name, "inventory": companion, "grid_aligned_with_dem": aligned})
        if not aligned:
            warnings.append(f"Quality layer {name!r} does not exactly match the DEM grid")

    return {
        "schema_version": 1,
        "dem": dem,
        "quality_layers": companions,
        "elevation_range_screen_applied": elevation_range is not None,
        "warnings": warnings,
        "status": "review_required" if warnings else "checks_passed",
        "limitations": [
            "Raster metadata does not prove effective terrain resolution or measurement accuracy.",
            "Vertical datum and elevation units must be verified from authoritative product metadata; they are not inferred from horizontal CRS.",
            "An absent warning does not certify scientific suitability or cross-site comparability.",
        ],
    }


def markdown_report(report: dict[str, Any]) -> str:
    dem = report["dem"]
    band = dem["bands"][0] if dem["bands"] else {}
    stats = band.get("statistics") or {}
    lines = [
        "# Earth DEM QA report",
        "",
        f"**Status:** {report['status']}",
        "",
        "## Primary DEM",
        "",
        f"- File: `{dem['path']}`",
        f"- SHA-256: `{dem['sha256'] or 'not calculated'}`",
        f"- Dimensions/bands: {dem['width']} × {dem['height']} / {dem['band_count']}",
        f"- Data type(s): {', '.join(dem['data_types'])}",
        f"- CRS: {dem['crs'] or 'not declared'}",
        f"- Pixel spacing: {dem['pixel_size_x']} × {dem['pixel_size_y']} CRS units",
        f"- Band unit tag: {band.get('unit') or 'not declared in raster'}",
        f"- NoData: {dem['nodata']}",
        f"- Valid coverage: {stats.get('valid_coverage_pct', 'not available')}%",
        f"- Elevation range: {stats.get('minimum', 'not available')} to {stats.get('maximum', 'not available')}",
        "",
        "## Companion quality rasters",
        "",
    ]
    if report["quality_layers"]:
        lines.extend(f"- `{layer['name']}`: exact grid match = {layer['grid_aligned_with_dem']}" for layer in report["quality_layers"])
    else:
        lines.append("- None supplied.")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report["warnings"])
    if not report["warnings"]:
        lines.append("- None from the configured structural checks.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def _parse_quality(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise argparse.ArgumentTypeError("quality layers must use NAME=PATH")
        name, path = value.split("=", 1)
        if not name.strip() or not path.strip() or name in parsed:
            raise argparse.ArgumentTypeError("quality layer names must be non-empty and unique")
        parsed[name] = path
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dem", type=Path, help="Primary DEM raster")
    parser.add_argument("--quality", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--minimum", type=float, help="Optional review-screen minimum elevation in declared vertical units")
    parser.add_argument("--maximum", type=float, help="Optional review-screen maximum elevation in declared vertical units")
    parser.add_argument("--json", type=Path, help="Optional JSON output path; omitted means stdout only")
    parser.add_argument("--markdown", type=Path, help="Optional Markdown output path")
    parser.add_argument("--no-checksum", action="store_true", help="Skip streaming SHA-256 calculation")
    args = parser.parse_args(argv)
    if (args.minimum is None) != (args.maximum is None):
        parser.error("--minimum and --maximum must be supplied together")
    elevation_range = (args.minimum, args.maximum) if args.minimum is not None else None
    try:
        report = build_qa_report(
            args.dem,
            _parse_quality(args.quality),
            checksum=not args.no_checksum,
            elevation_range=elevation_range,
        )
        rendered = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(rendered, encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(report), encoding="utf-8")
        if not args.json and not args.markdown:
            print(rendered, end="")
        return 1 if report["status"] == "review_required" else 0
    except (FileNotFoundError, ValueError, OSError, rasterio.errors.RasterioError) as exc:
        print(f"QA FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
