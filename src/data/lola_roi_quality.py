"""Summarize NASA LOLA support and uncertainty inside provider ROI polygons.

This is a quality/provenance audit, not a terrain fingerprint, site ranking,
or AREA 67 AOI approval. It performs no reprojection, geometry repair,
resampling, or writing of derived rasters.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.errors import WindowError
from rasterio.features import geometry_mask, geometry_window

try:
    from .lola_south_pole import SITES, site_asset_paths
except ImportError:
    from lola_south_pole import SITES, site_asset_paths

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data/metadata/lola_roi_quality"
ASSET_NAMES = ("elevation", "counts", "slope", "z_uncertainty", "slope_uncertainty")


def json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _axis_signature(crs: Any) -> tuple[tuple[str, float], ...]:
    return tuple(
        (str(axis.direction).casefold(), float(axis.unit_conversion_factor))
        for axis in crs.axis_info
    )


def _projection_parameter_signature(crs: Any) -> tuple[str, tuple[tuple[str, float], ...]]:
    operation = crs.coordinate_operation
    parameters = tuple(
        sorted(
            (
                str(parameter.name).casefold(),
                float(parameter.value) * float(parameter.unit_conversion_factor),
            )
            for parameter in operation.params
        )
    )
    return str(operation.method_name).casefold(), parameters


def _equivalent_custom_projected_crs(left: Any, right: Any) -> bool:
    """Compare projection mathematics while ignoring non-semantic WKT labels.

    This narrow fallback is intended for custom lunar CRS WKT where providers
    serialize the same sphere/projection with different placeholder names.
    It requires identical geodetic body dimensions, prime meridian, projection
    method and normalized parameters, and coordinate-axis directions/units.
    """
    if not (left.is_projected and right.is_projected):
        return False

    left_geodetic = left.geodetic_crs
    right_geodetic = right.geodetic_crs
    if left_geodetic is None or right_geodetic is None:
        return False

    left_ellipsoid = left_geodetic.ellipsoid
    right_ellipsoid = right_geodetic.ellipsoid
    for left_value, right_value in (
        (left_ellipsoid.semi_major_metre, right_ellipsoid.semi_major_metre),
        (left_ellipsoid.semi_minor_metre, right_ellipsoid.semi_minor_metre),
    ):
        if not math.isclose(
            float(left_value), float(right_value), rel_tol=1e-12, abs_tol=1e-9
        ):
            return False

    left_prime_meridian = (
        float(left_geodetic.prime_meridian.longitude)
        * float(left_geodetic.prime_meridian.unit_conversion_factor)
    )
    right_prime_meridian = (
        float(right_geodetic.prime_meridian.longitude)
        * float(right_geodetic.prime_meridian.unit_conversion_factor)
    )
    if not math.isclose(
        left_prime_meridian, right_prime_meridian, rel_tol=1e-12, abs_tol=1e-12
    ):
        return False

    if _axis_signature(left_geodetic) != _axis_signature(right_geodetic):
        return False
    if _axis_signature(left) != _axis_signature(right):
        return False

    try:
        left_method, left_parameters = _projection_parameter_signature(left)
        right_method, right_parameters = _projection_parameter_signature(right)
    except (AttributeError, TypeError, ValueError):
        return False

    if left_method != right_method or len(left_parameters) != len(right_parameters):
        return False
    for (left_name, left_value), (right_name, right_value) in zip(
        left_parameters, right_parameters
    ):
        if left_name != right_name or not math.isclose(
            left_value, right_value, rel_tol=1e-12, abs_tol=1e-12
        ):
            return False
    return True


def same_crs(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    try:
        from pyproj import CRS

        left_crs = CRS.from_user_input(left)
        right_crs = CRS.from_user_input(right)
        if left_crs.equals(right_crs, ignore_axis_order=True):
            return True
        return _equivalent_custom_projected_crs(left_crs, right_crs)
    except Exception:
        return False


def values_in_roi(dataset: rasterio.io.DatasetReader, window: Any, in_roi: np.ndarray) -> np.ndarray:
    masked = dataset.read(1, window=window, masked=True)
    values = np.asarray(masked.data, dtype=np.float64)
    valid = in_roi & ~np.ma.getmaskarray(masked) & np.isfinite(values)
    return values[valid]


def summarize(values: np.ndarray, prefix: str) -> dict[str, Any]:
    if values.size == 0:
        return {
            f"{prefix}_valid_pixel_count": 0,
            f"{prefix}_minimum": None,
            f"{prefix}_median": None,
            f"{prefix}_p90": None,
            f"{prefix}_p95": None,
            f"{prefix}_maximum": None,
        }
    return {
        f"{prefix}_valid_pixel_count": int(values.size),
        f"{prefix}_minimum": float(np.min(values)),
        f"{prefix}_median": float(np.median(values)),
        f"{prefix}_p90": float(np.percentile(values, 90)),
        f"{prefix}_p95": float(np.percentile(values, 95)),
        f"{prefix}_maximum": float(np.max(values)),
    }


def inspect_feature(
    geometry: Any,
    properties: dict[str, Any],
    feature_index: int,
    source_name: str,
    datasets: dict[str, rasterio.io.DatasetReader],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source_shapefile": source_name,
        "feature_index": int(feature_index),
        "properties": {str(key): json_value(value) for key, value in properties.items()},
        "status": "review_required",
        "warnings": [],
    }
    if geometry is None or geometry.is_empty:
        result["warnings"].append("Feature geometry is null or empty; no raster statistics calculated.")
        return result
    if not geometry.is_valid:
        result["warnings"].append("Feature geometry is invalid; no automatic repair was attempted.")
        return result
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        result["warnings"].append(
            f"Unsupported geometry type {geometry.geom_type!r}; only Polygon and MultiPolygon are summarized."
        )
        return result

    reference = datasets["elevation"]
    try:
        window = geometry_window(reference, [geometry], pad_x=0, pad_y=0)
    except WindowError:
        result["warnings"].append("ROI does not overlap the elevation raster footprint.")
        return result

    height, width = int(window.height), int(window.width)
    if height <= 0 or width <= 0:
        result["warnings"].append("ROI intersects no raster pixel window.")
        return result

    inside = geometry_mask(
        [geometry],
        out_shape=(height, width),
        transform=reference.window_transform(window),
        all_touched=False,
        invert=True,
    )
    roi_pixels = int(inside.sum())
    if roi_pixels == 0:
        result["warnings"].append("ROI contains no raster pixel centers at the native grid.")
        return result

    arrays = {name: values_in_roi(ds, window, inside) for name, ds in datasets.items()}
    elevation_valid = arrays["elevation"]
    counts = arrays["counts"]
    positive = int(np.count_nonzero(counts > 0))
    zero = int(np.count_nonzero(counts == 0))
    negative = int(np.count_nonzero(counts < 0))
    counts_valid = int(counts.size)

    result.update(
        {
            "status": "inventory_complete",
            "raster_crs": reference.crs.to_string() if reference.crs else None,
            "pixel_inclusion_rule": "pixel center inside polygon; all_touched=false",
            "roi_pixel_center_count": roi_pixels,
            "elevation_valid_coverage_pct": 100.0 * elevation_valid.size / roi_pixels,
            "counts_valid_coverage_pct": 100.0 * counts_valid / roi_pixels,
            "counts_positive_direct_support_pct": 100.0 * positive / counts_valid if counts_valid else None,
            "counts_zero_interpolated_pct": 100.0 * zero / counts_valid if counts_valid else None,
            "counts_negative_value_count": negative,
            "counts_invalid_or_missing_pixel_count": roi_pixels - counts_valid,
            "direct_support_denominator": "valid finite LDEC pixels within ROI pixel centers",
            "quality_interpretation": (
                "Positive LDEC values indicate one or more LOLA shots. Zero-count pixels are "
                "not NoData; their LDEM heights are interpolated."
            ),
        }
    )
    for name in ("elevation", "slope", "z_uncertainty", "slope_uncertainty"):
        result.update(summarize(arrays[name], name))

    if negative:
        result["warnings"].append("LDEC contains negative values inside this ROI.")
    for name in ("z_uncertainty", "slope_uncertainty"):
        if arrays[name].size and np.any(arrays[name] < 0):
            result["warnings"].append(f"{name} contains negative values inside this ROI.")
    if not counts_valid:
        result["warnings"].append("No valid LDEC count cells are available within this ROI.")
    if result["warnings"]:
        result["status"] = "review_required"
    return result


def build_roi_quality_report(
    site_id: str,
    roi_directory: str | Path,
    *,
    raster_paths: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    if site_id not in SITES:
        raise ValueError(f"Unknown site {site_id!r}; choose from {', '.join(SITES)}")
    roi_directory = Path(roi_directory)
    if not roi_directory.is_dir():
        raise FileNotFoundError(f"ROI directory not found: {roi_directory}")

    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError("ROI quality audit requires geopandas from requirements.txt") from exc

    shapefiles = sorted(roi_directory.rglob("*.shp"))
    report: dict[str, Any] = {
        "site_id": site_id,
        "site_name": SITES[site_id]["name"],
        "status": "review_required",
        "source_catalog": "https://pgda.gsfc.nasa.gov/products/78",
        "roi_directory": str(roi_directory),
        "raster_assets": {},
        "shapefiles": [],
        "warnings": [],
        "limitations": [
            "Provider-defined ROI polygons are not automatically AREA 67-approved study AOIs.",
            "This is a raster support and uncertainty inventory, not a terrain fingerprint or site ranking.",
            "NoData, interpolated LDEM values, and zero LDEC counts are distinct states.",
            "Raster posting is not effective resolution or a per-pixel accuracy guarantee.",
            "No reprojection, resampling, geometry repair, or vertical-reference transformation is performed.",
            "Statistics use native raster pixel centers within each polygon; no pixel-area weighting is applied.",
        ],
    }
    if not shapefiles:
        report["warnings"].append("No shapefiles were found in the extracted ROI directory.")
        return report

    paths = raster_paths or site_asset_paths(site_id, list(ASSET_NAMES))
    with ExitStack() as stack:
        datasets = {name: stack.enter_context(rasterio.open(paths[name])) for name in ASSET_NAMES}
        reference = datasets["elevation"]
        for name, ds in datasets.items():
            if ds.count != 1:
                raise ValueError(f"{name} raster must contain exactly one band.")
            if ds.crs != reference.crs:
                raise ValueError(f"{name} CRS does not match the elevation raster CRS.")
            if (
                ds.width != reference.width
                or ds.height != reference.height
                or ds.transform != reference.transform
            ):
                raise ValueError(f"{name} grid does not exactly match the elevation raster grid.")
            report["raster_assets"][name] = {
                "path": str(paths[name]),
                "crs": ds.crs.to_string() if ds.crs else None,
                "width": int(ds.width),
                "height": int(ds.height),
                "transform": list(ds.transform)[:6],
                "nodata": json_value(ds.nodata),
            }

        for shp_path in shapefiles:
            relative_name = shp_path.relative_to(roi_directory).as_posix()
            try:
                frame = gpd.read_file(shp_path)
            except Exception as exc:
                report["warnings"].append(
                    f"{relative_name}: could not read shapefile: {type(exc).__name__}: {exc}"
                )
                continue
            if frame.crs is None:
                report["warnings"].append(f"{relative_name}: CRS missing; no CRS will be guessed.")
                continue
            if not same_crs(frame.crs, reference.crs):
                report["warnings"].append(
                    f"{relative_name}: shapefile CRS differs from raster CRS; no reprojection attempted."
                )
                continue

            features = []
            for feature_index, row in frame.iterrows():
                properties = {
                    str(column): row[column]
                    for column in frame.columns
                    if column != frame.geometry.name
                }
                features.append(
                    inspect_feature(
                        row.geometry, properties, int(feature_index), relative_name, datasets
                    )
                )
            report["shapefiles"].append(
                {
                    "shapefile": relative_name,
                    "feature_count": int(len(frame)),
                    "crs": frame.crs.to_string(),
                    "geometry_types": sorted(
                        str(value) for value in frame.geometry.geom_type.dropna().unique()
                    ),
                    "fields": [
                        str(column) for column in frame.columns if column != frame.geometry.name
                    ],
                    "features": features,
                }
            )

    report["feature_count"] = sum(
        len(item["features"]) for item in report["shapefiles"]
    )
    if not report["shapefiles"]:
        report["warnings"].append(
            "No readable shapefile had a declared CRS matching the raster CRS."
        )
    any_feature_review = any(
        feature["status"] == "review_required"
        for shp in report["shapefiles"]
        for feature in shp["features"]
    )
    report["status"] = (
        "review_required" if report["warnings"] or any_feature_review else "inventory_complete"
    )
    return report


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"LOLA ROI support and uncertainty audit — {report['site_id']}",
        "",
        f"Status: {report['status']}",
        "",
        "This polygon-level data-support audit is not an AOI approval, terrain fingerprint, or site ranking.",
        "",
        "| ROI shapefile | Feature | Status | ROI pixel centers | Elevation valid % | Positive LDEC support % | Zero-count/interpolated % | Z RMS median (m) | Slope RMS median (degrees) |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for shp in report["shapefiles"]:
        for feature in shp["features"]:
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                    shp["shapefile"],
                    feature["feature_index"],
                    feature["status"],
                    feature.get("roi_pixel_center_count", ""),
                    feature.get("elevation_valid_coverage_pct", ""),
                    feature.get("counts_positive_direct_support_pct", ""),
                    feature.get("counts_zero_interpolated_pct", ""),
                    feature.get("z_uncertainty_median", ""),
                    feature.get("slope_uncertainty_median", ""),
                )
            )
    lines.extend(["", "Warnings", ""])
    lines.extend(f"- {warning}" for warning in report["warnings"])
    for shp in report["shapefiles"]:
        for feature in shp["features"]:
            lines.extend(
                f"- {shp['shapefile']} feature {feature['feature_index']}: {warning}"
                for warning in feature["warnings"]
            )
    if not report["warnings"] and all(
        not feature["warnings"]
        for shp in report["shapefiles"]
        for feature in shp["features"]
    ):
        lines.append("- None from the configured checks.")
    lines.extend(["", "Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", nargs="+", choices=tuple(SITES), required=True)
    parser.add_argument("--roi-root", type=Path, default=REPO_ROOT / "data/raw/moon/roi_shapes")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        for site_id in args.sites:
            report = build_roi_quality_report(site_id, args.roi_root / site_id)
            args.output_root.mkdir(parents=True, exist_ok=True)
            json_path = args.output_root / f"{site_id}_roi_quality.json"
            markdown_path = args.output_root / f"{site_id}_roi_quality.md"
            json_path.write_text(
                json.dumps(report, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
            markdown_path.write_text(markdown_report(report), encoding="utf-8")
            print(
                f"{site_id}: {report['status']} — "
                f"{report.get('feature_count', 0)} ROI features"
            )
            print(f"JSON: {json_path}")
            print(f"Markdown: {markdown_path}")
        return 0
    except (
        FileNotFoundError, ValueError, OSError, RuntimeError,
        rasterio.errors.RasterioError, WindowError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
