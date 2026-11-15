"""Create a read-only inventory and structural preflight report for acquired GIS rasters.

This report is deliberately conservative: PASS is structural only and never means
that an AOI, vertical datum, analysis scale, or scientific comparison is approved.
"""
from __future__ import annotations

import argparse
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
    lines.extend(["", "## Interpretation", "", "- Earth source rasters in EPSG:4326 are inventory inputs, not analysis-ready metric grids.",
                  "- Missing vertical-reference evidence remains unresolved; it is never inferred from horizontal CRS.",
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
            preflight = preflight_raster(path)
            status = preflight.get("status", "FAIL")
            counts[status] = counts.get(status, 0) + 1
            entries.append({"path": path.relative_to(ROOT).as_posix(), "inventory": inventory, "preflight": preflight})
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
