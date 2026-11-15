"""Read-only structural preflight checks for elevation rasters.

This utility reports input readiness evidence only. It does not infer scientific
quality, vertical datums, effective resolution, or approval.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pyproj import CRS
from pyproj.exceptions import CRSError


_STATUS_ORDER = {"PASS": 0, "REVIEW": 1, "FAIL": 2}


def _check(name: str, status: str, value: Any, note: str) -> dict[str, Any]:
    return {"name": name, "status": status, "value": value, "note": note}


def preflight_raster(
    path: str | Path,
    *,
    elevation_unit: str | None = None,
    vertical_reference: str | None = None,
    require_projected_metre_grid: bool = False,
    quality_paths: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    """Inspect raster structure and explicit metadata without modifying input.

    ``elevation_unit`` and ``vertical_reference`` should be sourced from product
    documentation where raster tags do not declare them. They are never inferred
    from the horizontal CRS. Set ``require_projected_metre_grid`` when checking
    against Hiba's structural grid requirement.
    """
    raster_path = Path(path)
    checks: list[dict[str, Any]] = []
    if not raster_path.is_file():
        checks.append(_check("readability", "FAIL", str(raster_path), "File does not exist."))
        return {"path": str(raster_path), "status": "FAIL", "scientific_approval": False, "checks": checks}

    try:
        with rasterio.open(raster_path) as ds:
            crs = CRS.from_user_input(ds.crs) if ds.crs else None
            transform = ds.transform
            rotated = transform.b != 0 or transform.d != 0
            x_size, y_size = float(abs(transform.a)), float(abs(transform.e))
            horizontal_units = [axis.unit_name for axis in crs.axis_info] if crs else []
            projected_metres = bool(
                crs and crs.is_projected and horizontal_units
                and all(unit.lower() in {"metre", "meter"} for unit in horizontal_units[:2])
            )
            valid_count = 0
            total_count = ds.width * ds.height
            for _, window in ds.block_windows(1):
                mask = ds.read_masks(1, window=window) > 0
                values = ds.read(1, window=window)
                valid_count += int((mask & np.isfinite(values)).sum())
            coverage = 100.0 * valid_count / total_count if total_count else 0.0
            band_unit = ds.units[0] if ds.units else None
            effective_elevation_unit = elevation_unit or band_unit
            metadata = ds.tags()
            vertical_evidence = vertical_reference or metadata.get("VERTICAL_DATUM") or metadata.get("VERTICAL_REFERENCE")
            orientation_ok = transform.a > 0 and transform.e < 0

            checks.append(_check("readability", "PASS", "readable", "Raster opened with rasterio."))
            checks.append(_check("crs", "PASS" if crs else "FAIL", crs.to_string() if crs else None,
                                 "CRS is declared." if crs else "No CRS is declared."))
            if crs:
                grid_status = "PASS" if projected_metres else ("FAIL" if require_projected_metre_grid else "REVIEW")
                checks.append(_check("horizontal_grid", grid_status,
                                     {"is_projected": crs.is_projected, "axis_units": horizontal_units},
                                     "Projected metre grid verified." if projected_metres else
                                     "Hiba requires projected metres; source grid needs an explicit approved preparation decision."))
            checks.append(_check("transform_rotation", "FAIL" if rotated else "PASS",
                                 {"b": transform.b, "d": transform.d},
                                 "Rotated/sheared transform is not supported." if rotated else "No rotation or shear."))
            checks.append(_check("pixel_spacing", "PASS" if x_size > 0 and y_size > 0 else "FAIL",
                                 {"x": x_size, "y": y_size, "units": horizontal_units[0] if horizontal_units else None},
                                 "Positive pixel spacing recorded; scale suitability is not inferred."))
            checks.append(_check("orientation", "PASS" if orientation_ok else "FAIL",
                                 {"north_up": orientation_ok, "a": transform.a, "e": transform.e},
                                 "North-up row/column signs verified." if orientation_ok else "Grid signs violate the expected north-up orientation."))
            checks.append(_check("mask_support", "PASS" if valid_count else "FAIL",
                                 {"valid_pixels": valid_count, "total_pixels": total_count, "valid_coverage_pct": coverage,
                                  "invalid_pixels": total_count - valid_count,
                                  "nodata": ds.nodata, "mask_flags": [x.name for x in ds.mask_flag_enums[0]]},
                                 "Mask and finite-value support counted block-wise; coverage does not prove accuracy."))
            checks.append(_check("band_count", "PASS" if ds.count == 1 else "REVIEW", ds.count,
                                 "Single elevation band." if ds.count == 1 else "Confirm intended elevation band."))
            checks.append(_check("elevation_unit", "PASS" if effective_elevation_unit else "REVIEW",
                                 effective_elevation_unit, "Explicit/tagged elevation unit recorded." if effective_elevation_unit else
                                 "Elevation unit missing; verify product documentation."))
            checks.append(_check("vertical_reference", "PASS" if vertical_evidence else "REVIEW",
                                 vertical_evidence, "Explicit vertical reference recorded." if vertical_evidence else
                                 "Vertical reference missing; do not infer it from horizontal CRS."))
            checks.append(_check("metadata", "PASS", {"dataset_tags": metadata, "band_units": list(ds.units or ())},
                                 "Available raster tags and band units captured."))
            info = {
                "driver": ds.driver, "width": ds.width, "height": ds.height, "band_count": ds.count,
                "dtype": list(ds.dtypes), "crs": crs.to_string() if crs else None,
                "transform": list(transform)[:6], "bounds": list(ds.bounds),
                "pixel_spacing": {"x": x_size, "y": y_size, "units": horizontal_units[0] if horizontal_units else None},
                "nodata": ds.nodata, "band_units": list(ds.units or ()),
                "elevation_unit_evidence": effective_elevation_unit,
                "vertical_reference_evidence": vertical_evidence,
            }
            reference_grid = (ds.width, ds.height, ds.crs.to_wkt() if ds.crs else None, tuple(transform)[:6])
    except (OSError, rasterio.errors.RasterioError, ValueError, CRSError) as exc:
        checks.append(_check("readability", "FAIL", None, f"Raster could not be inspected: {exc}"))
        return {"path": str(raster_path), "status": "FAIL", "scientific_approval": False, "checks": checks}

    quality_results = []
    for name, companion_path in (quality_paths or {}).items():
        item = {"name": name, "path": str(companion_path)}
        try:
            with rasterio.open(companion_path) as quality:
                signature = (quality.width, quality.height, quality.crs.to_wkt() if quality.crs else None,
                             tuple(quality.transform)[:6])
                aligned = signature == reference_grid
                item.update({"status": "PASS" if aligned else "REVIEW", "grid_aligned": aligned,
                             "width": quality.width, "height": quality.height,
                             "crs": quality.crs.to_string() if quality.crs else None})
        except (OSError, rasterio.errors.RasterioError) as exc:
            item.update({"status": "FAIL", "grid_aligned": False, "error": str(exc)})
        quality_results.append(item)
    statuses = [item["status"] for item in checks] + [item["status"] for item in quality_results]
    overall = max(statuses, key=lambda status: _STATUS_ORDER[status], default="REVIEW")
    return {"path": str(raster_path), "status": overall, "scientific_approval": False,
            "raster": info, "checks": checks, "quality_layers": quality_results,
            "limitations": ["Structural preflight only; not scientific approval.",
                            "Vertical reference, unit, effective resolution and accuracy require authoritative evidence.",
                            "No raster values are changed; no reprojection, resampling, clipping or mosaicking is performed."]}
