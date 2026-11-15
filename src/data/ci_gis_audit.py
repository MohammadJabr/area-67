"""Create a read-only inventory and structural preflight report for acquired GIS rasters.

This report is deliberately conservative: PASS is structural only and never means
that an AOI, vertical datum, analysis scale, or scientific comparison is approved.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.data.raster_inventory import inventory_raster
from src.data.raster_preflight import preflight_raster

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW = ROOT / "data" / "raw"
DEFAULT_OUTPUT = ROOT / "data" / "metadata" / "ci_gis_audit"


def _read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _source_documentation(path: Path) -> dict[str, Any]:
    """Return product-level metadata for a known source raster, without changing it."""
    try:
        relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return {}

    if relative.startswith("data/raw/earth/"):
        source_id = path.stem
        for row in _read_manifest(ROOT / "data" / "metadata" / "earth_dem_manifest.csv"):
            if row.get("source_id") != source_id:
                continue
            unit_text = (row.get("elevation_unit") or "").strip()
            datum_text = (row.get("vertical_datum") or "").strip()
            return {
                "source_product": row.get("source_name"),
                "source_url": row.get("source_url"),
                "data_kind": "elevation",
                "value_unit": unit_text.split(" (", 1)[0] or None,
                "vertical_reference": datum_text.split(" (", 1)[0] or None,
                "vertical_reference_applicable": True,
                "horizontal_crs": row.get("crs") or None,
                "effective_resolution_note": row.get("effective_resolution_note"),
                "quality_layers": row.get("quality_layers"),
                "uncertainty_note": row.get("uncertainty_note"),
            }

    if relative.startswith("data/raw/moon/"):
        for row in _read_manifest(ROOT / "data" / "metadata" / "lunar_5mpp_manifest.csv"):
            if row.get("relative_path") != relative:
                continue
            applicable = (row.get("vertical_reference_applicable") or "").strip().lower() == "true"
            vertical_status = (row.get("vertical_reference_status") or "").strip()
            return {
                "source_product": row.get("source_product"),
                "source_url": row.get("source_url"),
                "data_kind": row.get("data_kind"),
                "value_unit": row.get("value_unit"),
                "vertical_reference": row.get("vertical_reference") or None,
                "vertical_reference_applicable": applicable,
                "coordinate_reference_frame": row.get("coordinate_reference_frame") or None,
                "coordinate_reference_frame_source": row.get("frame_source_url") or None,
                "vertical_reference_status": vertical_status,
                "pixel_posting_m": row.get("pixel_posting_m"),
                "source_notes": row.get("notes"),
            }
    return {}


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AREA 67 — CI GIS acquisition audit",
        "",
        f"- Generated (UTC): {report['generated_at_utc']}",
        f"- Raster files inspected: {report['raster_count']}",
        f"- Structural PASS: {report['status_counts'].get('PASS', 0)}",
        f"- Structural REVIEW: {report['status_counts'].get('REVIEW', 0)}",
        f"- Structural FAIL: {report['status_counts'].get('FAIL', 0)}",
        "",
        "> Structural inspection only. No AOI, vertical transformation, common grid,",
        "> effective resolution, or scientific suitability is approved by this report.",
        "",
        "| Raster | Size | CRS | Pixel spacing | Valid coverage | Preflight |",
        "|---|---:|---|---|---:|---|",
    ]
    for item in report["rasters"]:
        inv = item.get("inventory") or {}
        bands = inv.get("bands") or []
        stats = (bands[0].get("statistics") or {}) if bands else {}
        spacing = f"{inv.get('pixel_size_x')} × {inv.get('pixel_size_y')} {inv.get('pixel_spacing_units') or ''}".strip()
        coverage = stats.get("valid_coverage_pct")
        lines.append(
            f"| {Path(item['path']).name} | {inv.get('file_size_bytes', '—')} | "
            f"{inv.get('crs') or 'missing'} | {spacing} | "
            f"{f'{coverage:.3f}%' if isinstance(coverage, (int, float)) else '—'} | "
            f"{(item.get('preflight') or {}).get('status', 'FAIL')} |"
        )
    if report["errors"]:
        lines.extend(["", "## Inspection errors", ""])
        lines.extend(f"- `{error['path']}`: {error['error']}" for error in report["errors"])
    if not report["rasters"]:
        lines.extend(["", "## No raster files found", "", "No .tif/.tiff files were present under the selected raw-data root."])
    documented = [item for item in report["rasters"] if item.get("source_documentation")]
    if documented:
        lines.extend(["", "## Product documentation metadata", "",
                      "| Raster | Data kind | Value unit | Horizontal CRS | Coordinate frame | Vertical reference | Source |",
                      "|---|---|---|---|---|---|"])
        for item in documented:
            doc = item["source_documentation"]
            vertical = doc.get("vertical_reference") or (
                "not stated" if doc.get("vertical_reference_applicable") else "not applicable"
            )
            source_url = doc.get("source_url") or doc.get("coordinate_reference_frame_source") or ""
            source_link = f"[product documentation]({source_url})" if source_url else "—"
            lines.append(
                f"| {Path(item['path']).name} | {doc.get('data_kind') or '—'} | "
                f"{doc.get('value_unit') or '—'} | {doc.get('horizontal_crs') or '—'} | "
                f"{doc.get('coordinate_reference_frame') or '—'} | {vertical} | {source_link} |"
            )
    lines.extend(["", "## Interpretation", "", "- Earth source rasters in EPSG:4326 are inventory inputs, not analysis-ready metric grids.",
                  "- Product-level metadata is shown separately from embedded raster tags; it is not inferred from the horizontal CRS.",
                  "- Where product documentation does not state a vertical reference (including the lunar surface-height reference), it remains unresolved.",
                  "- NASA PGDA Product 78 documents the GeoTIFF layers as MOON_ME/DE421 but explicitly excludes ROI shapefiles from that frame statement.",
                  "- Quality companion presence/alignment must be assessed separately where such layers exist.",
                  "- This audit does not clip, reproject, resample, mosaic, repair, or modify any source raster.", ""])
    return "\n".join(lines)


def _json_safe(value: Any) -> Any:
    """Convert non-finite numeric metadata to JSON null without losing its meaning."""
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def build_report(raw_root: Path) -> dict[str, Any]:
    raster_paths = sorted(
        path for path in raw_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".tif", ".tiff"}
        and not path.name.endswith(".part")
    ) if raw_root.exists() else []
    entries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    counts = {"PASS": 0, "REVIEW": 0, "FAIL": 0}
    for path in raster_paths:
        try:
            inventory = inventory_raster(path, checksum=True)
            source_doc = _source_documentation(path)
            preflight_kwargs: dict[str, Any] = {}
            if source_doc:
                preflight_kwargs = {
                    "data_kind": source_doc.get("data_kind", "elevation"),
                    "value_unit": source_doc.get("value_unit"),
                    "vertical_reference": source_doc.get("vertical_reference"),
                    "vertical_reference_applicable": source_doc.get("vertical_reference_applicable", True),
                    "coordinate_reference_frame": source_doc.get("coordinate_reference_frame"),
                    "coordinate_reference_frame_source": source_doc.get("coordinate_reference_frame_source"),
                }
                if source_doc.get("data_kind") == "elevation":
                    preflight_kwargs["elevation_unit"] = source_doc.get("value_unit")
            preflight = preflight_raster(path, **preflight_kwargs)
            status = preflight.get("status", "FAIL")
            counts[status] = counts.get(status, 0) + 1
            entries.append({
                "path": path.relative_to(ROOT).as_posix(),
                "inventory": inventory,
                "source_documentation": source_doc or None,
                "preflight": preflight,
            })
        except Exception as exc:  # keep auditing other files if one raster is corrupt
            errors.append({"path": path.relative_to(ROOT).as_posix(), "error": f"{type(exc).__name__}: {exc}"})
            counts["FAIL"] += 1
    return _json_safe({
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_root": raw_root.relative_to(ROOT).as_posix() if raw_root.is_relative_to(ROOT) else str(raw_root),
        "raster_count": len(entries),
        "status_counts": counts,
        "rasters": entries,
        "errors": errors,
        "scientific_approval": False,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_report(args.raw_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "gis_acquisition_audit.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (args.output_dir / "gis_acquisition_audit.md").write_text(_markdown(report), encoding="utf-8")
    print(_markdown(report))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
