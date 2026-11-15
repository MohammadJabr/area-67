"""Preview Shapely make_valid results for invalid provider ROI polygons.

The utility never edits or replaces source geometries. It produces in-memory
repair candidates solely to quantify geometry-repair sensitivity and compare
candidate raster statistics with the valid source features.
"""
from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import rasterio

try:
    from .lola_roi_quality import (
        ASSET_NAMES,
        REPO_ROOT,
        inspect_feature,
        json_value,
        same_crs,
        site_asset_paths,
    )
except ImportError:
    from lola_roi_quality import (
        ASSET_NAMES,
        REPO_ROOT,
        inspect_feature,
        json_value,
        same_crs,
        site_asset_paths,
    )

try:
    from shapely import make_valid
    from shapely.ops import unary_union
    from shapely.validation import explain_validity
except ImportError as exc:  # pragma: no cover - dependency is required by project
    raise RuntimeError(
        "Invalid ROI repair preview requires Shapely with make_valid support (Shapely >= 2.0)."
    ) from exc


DEFAULT_ROI_ROOT = REPO_ROOT / "data/raw/moon/roi_shapes"


def _polygon_parts(geometry: Any) -> list[Any]:
    """Extract polygon leaves from Polygon, MultiPolygon or GeometryCollection."""
    if geometry is None or geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    parts: list[Any] = []
    if hasattr(geometry, "geoms"):
        for child in geometry.geoms:
            parts.extend(_polygon_parts(child))
    return parts


def _leaf_geometry_types(geometry: Any) -> list[str]:
    """Return non-container leaf geometry types, retaining their multiplicity."""
    if geometry is None or geometry.is_empty:
        return []
    if geometry.geom_type in {"GeometryCollection", "MultiPolygon", "MultiLineString", "MultiPoint"}:
        result: list[str] = []
        for child in geometry.geoms:
            result.extend(_leaf_geometry_types(child))
        return result
    return [str(geometry.geom_type)]


def _vertex_count(geometry: Any) -> int:
    if geometry is None or geometry.is_empty:
        return 0
    if geometry.geom_type == "Polygon":
        count = len(geometry.exterior.coords)
        count += sum(len(ring.coords) for ring in geometry.interiors)
        return count
    if hasattr(geometry, "geoms"):
        return sum(_vertex_count(child) for child in geometry.geoms)
    if hasattr(geometry, "coords"):
        return len(geometry.coords)
    return 0


def _geometry_metadata(geometry: Any) -> dict[str, Any]:
    if geometry is None:
        return {"geometry_type": None, "is_empty": True}
    if geometry.is_empty:
        return {"geometry_type": str(geometry.geom_type), "is_empty": True}
    return {
        "geometry_type": str(geometry.geom_type),
        "is_empty": False,
        "is_valid": bool(geometry.is_valid),
        "area_crs_units_squared": float(geometry.area),
        "bounds_crs_units": [float(value) for value in geometry.bounds],
        "vertex_count_including_ring_closure": _vertex_count(geometry),
    }


def make_valid_preview(geometry: Any) -> tuple[dict[str, Any], Any | None]:
    """Create a polygon-only in-memory candidate and describe discarded dimensions."""
    if geometry is None or geometry.is_empty:
        return (
            {
                "status": "not_possible",
                "reason": "Source geometry is null or empty.",
            },
            None,
        )

    if geometry.is_valid:
        return (
            {
                "status": "not_needed",
                "reason": "Source geometry is already valid.",
                "output_geometry_type": str(geometry.geom_type),
            },
            geometry,
        )

    validity_reason = str(explain_validity(geometry))
    try:
        repaired = make_valid(geometry)
    except Exception as exc:
        return (
            {
                "status": "failed",
                "validity_reason": validity_reason,
                "error": f"{type(exc).__name__}: {exc}",
            },
            None,
        )

    polygons = _polygon_parts(repaired)
    leaf_types = _leaf_geometry_types(repaired)
    non_polygon_types = [kind for kind in leaf_types if kind not in {"Polygon"}]
    if not polygons:
        return (
            {
                "status": "no_polygonal_output",
                "validity_reason": validity_reason,
                "output_geometry_type": str(repaired.geom_type),
                "output_component_types": leaf_types,
                "polygon_component_count": 0,
                "non_polygon_component_types": non_polygon_types,
            },
            None,
        )

    try:
        candidate = unary_union(polygons)
    except Exception as exc:
        return (
            {
                "status": "union_failed",
                "validity_reason": validity_reason,
                "output_geometry_type": str(repaired.geom_type),
                "output_component_types": leaf_types,
                "polygon_component_count": len(polygons),
                "non_polygon_component_types": non_polygon_types,
                "error": f"{type(exc).__name__}: {exc}",
            },
            None,
        )

    if candidate.is_empty or not candidate.is_valid:
        return (
            {
                "status": "candidate_invalid",
                "validity_reason": validity_reason,
                "output_geometry_type": str(repaired.geom_type),
                "output_component_types": leaf_types,
                "polygon_component_count": len(polygons),
                "non_polygon_component_types": non_polygon_types,
                "candidate": _geometry_metadata(candidate),
            },
            None,
        )

    info = {
        "status": "preview_available",
        "method": "shapely.make_valid followed by unary_union of polygonal components only",
        "validity_reason": validity_reason,
        "make_valid_output_geometry_type": str(repaired.geom_type),
        "make_valid_output_component_types": leaf_types,
        "polygon_component_count_before_union": len(polygons),
        "non_polygon_component_types_excluded_from_raster_preview": non_polygon_types,
        "candidate_geometry": _geometry_metadata(candidate),
        "interpretation": (
            "Candidate exists only in memory. It is not an approved or authoritative "
            "replacement for the provider geometry."
        ),
    }
    return info, candidate


def build_repair_preview_report(
    site_id: str,
    roi_directory: str | Path,
    *,
    raster_paths: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    """Report source validity and in-memory make_valid candidate raster statistics."""
    if not site_id:
        raise ValueError("site_id must be non-empty")

    roi_directory = Path(roi_directory)
    if not roi_directory.is_dir():
        raise FileNotFoundError(f"ROI directory not found: {roi_directory}")

    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError("Repair preview requires geopandas") from exc

    shapefiles = sorted(roi_directory.rglob("*.shp"))
    if not shapefiles:
        raise FileNotFoundError(f"No shapefiles found under ROI directory: {roi_directory}")

    paths = raster_paths or site_asset_paths(site_id, list(ASSET_NAMES))
    report: dict[str, Any] = {
        "schema_version": 1,
        "site_id": site_id,
        "status": "review_required",
        "purpose": "geometry repair sensitivity preview; not a replacement geometry or AOI decision",
        "repair_method": "Shapely make_valid in memory; polygonal components unioned for raster-statistics preview",
        "source_modification": "none",
        "raster_assets": {},
        "shapefiles": [],
        "limitations": [
            "The original provider geometry is never modified, repaired in place, or written.",
            "Statistics for invalid source features are preview-only statistics on an in-memory make_valid candidate.",
            "Non-polygonal make_valid outputs are listed and excluded from polygon raster statistics.",
            "make_valid resolves topological validity, not scientific intent or the provider's intended polygon boundary.",
            "A candidate geometry must be reviewed against the provider's intended region and source processing method before any use.",
            "Matching the local pixel lattice does not establish the physical lunar datum/frame (ME or PA).",
            "Provider-defined ROIs are not automatically AREA 67-approved study AOIs.",
        ],
    }

    with ExitStack() as stack:
        datasets = {
            name: stack.enter_context(rasterio.open(paths[name]))
            for name in ASSET_NAMES
        }
        reference = datasets["elevation"]
        for name, dataset in datasets.items():
            if dataset.count != 1:
                raise ValueError(f"{name} raster must contain exactly one band.")
            if dataset.crs != reference.crs:
                raise ValueError(f"{name} CRS does not match the elevation raster CRS.")
            if (
                dataset.width != reference.width
                or dataset.height != reference.height
                or dataset.transform != reference.transform
            ):
                raise ValueError(f"{name} grid does not exactly match the elevation raster grid.")
            report["raster_assets"][name] = {
                "path": str(paths[name]),
                "width": int(dataset.width),
                "height": int(dataset.height),
                "transform": list(dataset.transform)[:6],
                "crs": dataset.crs.to_string() if dataset.crs else None,
            }

        for shapefile_path in shapefiles:
            relative_name = shapefile_path.relative_to(roi_directory).as_posix()
            frame = gpd.read_file(shapefile_path)
            if frame.crs is None:
                raise ValueError(f"{relative_name}: CRS missing; no CRS will be guessed.")
            if not same_crs(frame.crs, reference.crs):
                raise ValueError(
                    f"{relative_name}: shapefile CRS is not nominally compatible with raster CRS; "
                    "no reprojection attempted."
                )

            feature_rows = []
            for feature_index, row in frame.iterrows():
                geometry = row.geometry
                properties = {
                    str(column): json_value(row[column])
                    for column in frame.columns
                    if column != frame.geometry.name
                }
                item: dict[str, Any] = {
                    "feature_index": int(feature_index),
                    "properties": properties,
                    "source_geometry": _geometry_metadata(geometry),
                    "source_validity_reason": (
                        "Valid Geometry"
                        if geometry is not None and geometry.is_valid
                        else (str(explain_validity(geometry)) if geometry is not None else "Null geometry")
                    ),
                }

                if geometry is None or geometry.is_empty:
                    item["status"] = "not_processable"
                    item["warnings"] = ["Source geometry is null or empty."]
                elif geometry.is_valid:
                    item["status"] = "valid_source_geometry"
                    item["source_statistics"] = inspect_feature(
                        geometry, properties, int(feature_index), relative_name, datasets
                    )
                else:
                    repair_info, candidate = make_valid_preview(geometry)
                    item["make_valid_preview"] = repair_info
                    if candidate is None:
                        item["status"] = "repair_preview_unavailable"
                    else:
                        item["status"] = "repair_preview_only"
                        component_previews = []
                        for component_index, component in enumerate(_polygon_parts(candidate)):
                            component_stats = inspect_feature(
                                component,
                                properties,
                                int(feature_index),
                                relative_name,
                                datasets,
                            )
                            component_stats["preview_only"] = True
                            component_stats["component_index"] = component_index
                            component_stats["warning"] = (
                                "These statistics describe one polygon component of the "
                                "in-memory make_valid candidate, not the original invalid provider polygon."
                            )
                            component_previews.append(
                                {
                                    "component_index": component_index,
                                    "geometry": _geometry_metadata(component),
                                    "statistics": component_stats,
                                }
                            )
                        item["repair_preview_component_statistics"] = component_previews
                        item["repair_preview_statistics"] = inspect_feature(
                            candidate,
                            properties,
                            int(feature_index),
                            relative_name,
                            datasets,
                        )
                        item["repair_preview_statistics"]["preview_only"] = True
                        item["repair_preview_statistics"]["warning"] = (
                            "These statistics describe the union of polygonal components "
                            "from the in-memory make_valid candidate, not the original invalid provider polygon."
                        )
                feature_rows.append(item)

            report["shapefiles"].append(
                {
                    "shapefile": relative_name,
                    "feature_count": int(len(frame)),
                    "crs": frame.crs.to_string(),
                    "features": feature_rows,
                }
            )

    total_features = sum(item["feature_count"] for item in report["shapefiles"])
    invalid_features = [
        feature
        for shapefile in report["shapefiles"]
        for feature in shapefile["features"]
        if not feature["source_geometry"].get("is_valid", False)
    ]
    report["summary"] = {
        "feature_count": total_features,
        "invalid_source_feature_count": len(invalid_features),
        "repair_preview_available_count": sum(
            feature.get("make_valid_preview", {}).get("status") == "preview_available"
            for feature in invalid_features
        ),
        "repair_preview_unavailable_count": sum(
            feature.get("status") == "repair_preview_unavailable"
            for feature in invalid_features
        ),
        "valid_source_feature_count": total_features - len(invalid_features),
    }
    report["status"] = (
        "review_required" if invalid_features else "inventory_complete"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="Site04")
    parser.add_argument("--roi-directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    roi_directory = args.roi_directory or (DEFAULT_ROI_ROOT / args.site)
    try:
        if args.output.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing report: {args.output}"
            )
        report = build_repair_preview_report(args.site, roi_directory)
        payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Repair preview: {args.output}")
        print(json.dumps(report["summary"], indent=2))
        for shapefile in report["shapefiles"]:
            for feature in shapefile["features"]:
                if not feature["source_geometry"].get("is_valid", False):
                    preview = feature.get("make_valid_preview", {})
                    stats = feature.get("repair_preview_statistics", {})
                    print(
                        f"Feature {feature['feature_index']}: "
                        f"{feature.get('source_validity_reason')} | "
                        f"{preview.get('status')} | "
                        f"candidate pixels={stats.get('roi_pixel_center_count', 'n/a')}"
                    )
        return 0
    except (
        FileNotFoundError,
        FileExistsError,
        ValueError,
        OSError,
        RuntimeError,
        rasterio.errors.RasterioError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
