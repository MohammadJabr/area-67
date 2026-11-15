#!/usr/bin/env python3
"""Read-only screening of selected NASA LOLA provider ROI candidates.

This is a diagnostic candidate-screening utility, NOT an AOI approval,
terrain fingerprint, site ranking, or permanent-base suitability assessment.

It reads native elevation, LDEC, slope, Z-uncertainty, and slope-uncertainty
rasters and valid provider ROI polygons. It does not reproject, resample,
repair geometries, or write to source files.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import CRS
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from shapely.geometry import mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Candidate list from the prior ROI quality audit and visual review.
# Site04 Feature 2 is retained as a secondary comparison to Feature 3.
CANDIDATES = [
    {"site": "Site07", "feature": 1, "role": "primary_candidate", "reason": "Largest current ROI sample (612 pixel centers)."},
    {"site": "Site01", "feature": 4, "role": "primary_candidate", "reason": "Balanced sample size, direct support, and uncertainty indicators."},
    {"site": "Site01", "feature": 2, "role": "primary_candidate", "reason": "Highest positive LDEC support among currently valid candidates."},
    {"site": "Site11", "feature": 2, "role": "primary_candidate", "reason": "Lowest reported median Z RMS among currently valid candidates."},
    {"site": "Site01", "feature": 3, "role": "primary_candidate", "reason": "Large ROI sample for comparison."},
    {"site": "Site04", "feature": 3, "role": "primary_candidate", "reason": "Lowest reported median slope RMS among currently valid candidates."},
    {"site": "Site04", "feature": 2, "role": "secondary_candidate", "reason": "Secondary Site04 alternative; similar small sample size."},
]

EXPECTED_PIXEL_CENTERS = {
    ("Site07", 1): 612,
    ("Site01", 4): 362,
    ("Site01", 2): 135,
    ("Site11", 2): 155,
    ("Site01", 3): 484,
    ("Site04", 3): 101,
    ("Site04", 2): 102,
}

ASSETS = {
    "elevation": ("surf", "m"),
    "counts": ("ldec", "LOLA shot count per cell"),
    "slope": ("slp", "degrees"),
    "z_uncertainty": ("toterr", "m RMS"),
    "slope_uncertainty": ("slperr", "degrees RMS"),
}


def unique_output_dir(base: Path) -> Path:
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = base.with_name(f"{base.name}_{suffix:02d}")
        suffix += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def _polar_stereographic_signature(value: Any) -> tuple[Any, ...] | None:
    """Return comparable projection parameters without claiming datum equality.

    Polar stereographic WKT can encode the pole using either latitude of origin
    (lat_0) or standard parallel (lat_ts). At the pole these are equivalent
    projection definitions. This signature deliberately excludes datum names.
    """
    crs = CRS.from_user_input(value)
    params = crs.to_dict()
    if params.get("proj") != "stere":
        return None

    latitude = params.get("lat_0", params.get("lat_ts"))
    if latitude is None:
        return None

    radius = params.get("R")
    if radius is None:
        semi_major = crs.ellipsoid.semi_major_metre
        semi_minor = crs.ellipsoid.semi_minor_metre
        if not math.isclose(semi_major, semi_minor, rel_tol=0, abs_tol=1e-6):
            return None
        radius = semi_major

    units = params.get("units")
    if units is None and crs.axis_info:
        units = crs.axis_info[0].unit_name

    return (
        "stere",
        round(float(latitude), 10),
        round(float(params.get("lon_0", 0.0)), 10),
        round(float(params.get("x_0", 0.0)), 6),
        round(float(params.get("y_0", 0.0)), 6),
        round(float(radius), 6),
        round(float(params.get("k_0", params.get("k", 1.0))), 12),
        str(units).lower() if units is not None else None,
    )


def compare_roi_raster_crs(roi_crs: Any, raster_crs: Any) -> dict[str, Any]:
    """Check exact CRS equality or matching nominal polar-stereographic math.

    A nominal projection match permits diagnostic raw-coordinate screening only.
    It does not establish the physical Moon-fixed ME/PA frame.
    """
    if roi_crs is None or raster_crs is None:
        raise ValueError("Both ROI and raster CRS metadata are required.")

    roi = CRS.from_user_input(roi_crs)
    raster = CRS.from_user_input(raster_crs)

    def is_metric_projected(crs: CRS) -> bool:
        return (
            crs.is_projected
            and bool(crs.axis_info)
            and all(
                math.isclose(axis.unit_conversion_factor, 1.0, rel_tol=0, abs_tol=1e-12)
                for axis in crs.axis_info[:2]
            )
        )

    if not is_metric_projected(roi) or not is_metric_projected(raster):
        raise ValueError("ROI and raster CRS must both be projected in metres.")

    exact = roi.equals(raster, ignore_axis_order=True)
    roi_signature = _polar_stereographic_signature(roi)
    raster_signature = _polar_stereographic_signature(raster)
    nominal_match = roi_signature is not None and roi_signature == raster_signature

    if not exact and not nominal_match:
        raise ValueError(
            "ROI CRS is not equal to raster CRS and nominal polar-stereographic "
            "projection parameters do not match; refusing raw-coordinate sampling."
        )

    return {
        "crs_objects_equal": bool(exact),
        "nominal_polar_stereographic_parameters_equal": bool(nominal_match),
        "coordinate_handling": (
            "Exact CRS match; native coordinates used without transformation."
            if exact
            else "Nominal polar-stereographic parameters match; raw coordinates used without transformation."
        ),
        "physical_moon_fixed_frame_resolved": False,
        "warning": (
            None if exact else
            "CRS objects/WKT differ. Matching projection parameters do not resolve "
            "the physical Moon-fixed ME/PA reference frame."
        ),
    }


def roi_window(
    bounds: tuple[float, float, float, float],
    src: rasterio.io.DatasetReader,
) -> Window:
    transform = src.transform
    if (
        not math.isclose(transform.b, 0.0, abs_tol=1e-12)
        or not math.isclose(transform.d, 0.0, abs_tol=1e-12)
        or transform.a <= 0
        or transform.e >= 0
    ):
        raise ValueError("ROI screening requires a north-up, non-rotated raster grid.")

    raw = from_bounds(*bounds, transform=transform)
    col0 = max(0, int(math.floor(raw.col_off)))
    row0 = max(0, int(math.floor(raw.row_off)))
    col1 = min(src.width, int(math.ceil(raw.col_off + raw.width)))
    row1 = min(src.height, int(math.ceil(raw.row_off + raw.height)))
    if col1 <= col0 or row1 <= row0:
        raise ValueError("ROI bounds do not intersect the raster grid.")
    return Window(col0, row0, col1 - col0, row1 - row0)


def numeric_stats(values: np.ndarray, unit: str) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"valid_n": 0, "unit": unit}
    p = np.percentile(arr, [10, 25, 50, 75, 90])
    return {
        "valid_n": int(arr.size),
        "unit": unit,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std_population": float(np.std(arr)),
        "p10": float(p[0]),
        "p25": float(p[1]),
        "median_p50": float(p[2]),
        "p75": float(p[3]),
        "p90": float(p[4]),
        "p90_minus_p10": float(p[4] - p[0]),
    }


def shape_metrics(geom) -> dict[str, Any]:
    area = float(geom.area)
    perimeter = float(geom.length)
    compactness = (4.0 * math.pi * area / (perimeter * perimeter)) if perimeter > 0 else None
    rect = geom.minimum_rotated_rectangle
    coords = list(rect.exterior.coords) if hasattr(rect, "exterior") else []
    sides = []
    for a, b in zip(coords[:-1], coords[1:]):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length > 0:
            sides.append(length)
    aspect = None
    if len(sides) >= 2:
        sides_sorted = sorted(sides)
        short_side = sides_sorted[0]
        long_side = max(sides_sorted)
        if short_side > 0:
            aspect = float(long_side / short_side)
    return {
        "nominal_projected_area_m2": area,
        "perimeter_m": perimeter,
        "compactness_4piA_over_P2": float(compactness) if compactness is not None else None,
        "minimum_rotated_rectangle_aspect_ratio": aspect,
        "geometry_type": geom.geom_type,
        "geometry_valid": bool(geom.is_valid),
    }


def source_paths(site: str) -> tuple[Path, dict[str, Path], Path]:
    stem = f"{site}_final_adj_5mpp_"
    raster_dir = PROJECT_ROOT / "data" / "raw" / "moon" / site.lower()
    assets = {name: raster_dir / f"{stem}{suffix}.tif" for name, (suffix, _) in ASSETS.items()}
    roi = PROJECT_ROOT / "data" / "raw" / "moon" / "roi_shapes" / site / f"{site}_ROIs.shp"
    return raster_dir, assets, roi


def read_candidate(
    site: str,
    feature_index: int,
    gdf: gpd.GeoDataFrame,
    paths: dict[str, Path],
) -> dict[str, Any]:
    if feature_index < 0 or feature_index >= len(gdf):
        raise IndexError(f"{site} Feature {feature_index}: index not found in ROI shapefile.")
    if gdf.crs is None:
        raise ValueError(f"{site}: ROI shapefile has no CRS metadata.")

    geom = gdf.geometry.iloc[feature_index]
    if geom is None or geom.is_empty or not geom.is_valid:
        raise ValueError(f"{site} Feature {feature_index}: invalid, empty, or missing geometry; no repair attempted.")

    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing {name} raster: {path}")

    datasets: dict[str, rasterio.io.DatasetReader] = {}
    try:
        for name, path in paths.items():
            datasets[name] = rasterio.open(path)

        base = datasets["elevation"]
        crs_check = compare_roi_raster_crs(gdf.crs, base.crs)
        for name, ds in datasets.items():
            if ds.width != base.width or ds.height != base.height or ds.transform != base.transform or ds.crs != base.crs:
                raise ValueError(f"{site}: {name} grid/CRS does not exactly match elevation; stopping rather than aligning layers.")

        left, bottom, right, top = base.bounds
        minx, miny, maxx, maxy = geom.bounds
        if minx < left or miny < bottom or maxx > right or maxy > top:
            raise ValueError(f"{site} Feature {feature_index}: geometry extends outside its native elevation raster.")

        window = roi_window(geom.bounds, base)
        inside = geometry_mask(
            [mapping(geom)],
            out_shape=(int(window.height), int(window.width)),
            transform=base.window_transform(window),
            invert=True,
            all_touched=False,
        )
        roi_pixel_centers = int(np.count_nonzero(inside))
        if roi_pixel_centers == 0:
            raise ValueError(f"{site} Feature {feature_index}: no pixel centers fall inside the ROI.")

        layer_values: dict[str, np.ndarray] = {}
        layer_coverage: dict[str, dict[str, Any]] = {}
        for name, ds in datasets.items():
            band = ds.read(1, window=window, masked=True)
            data = np.asarray(band.data, dtype=np.float64)
            nodata_mask = np.ma.getmaskarray(band)
            valid = inside & (~nodata_mask) & np.isfinite(data)
            values = data[valid]
            layer_values[name] = values
            layer_coverage[name] = {
                "valid_n": int(values.size),
                "valid_pct_of_roi_pixel_centers": float(100.0 * values.size / roi_pixel_centers),
                "masked_or_nonfinite_n": int(roi_pixel_centers - values.size),
            }

        count_vals = layer_values["counts"]
        positive_n = int(np.count_nonzero(count_vals > 0))
        zero_n = int(np.count_nonzero(count_vals == 0))
        negative_n = int(np.count_nonzero(count_vals < 0))
        counts_valid_n = int(count_vals.size)
        counts_missing_n = roi_pixel_centers - counts_valid_n

        elevation_stats = numeric_stats(layer_values["elevation"], ASSETS["elevation"][1])
        if "p90_minus_p10" in elevation_stats:
            elevation_stats["interpretation_note"] = (
                "Within-ROI elevation distribution spread (P90-P10); not a moving-window local-relief metric."
            )

        return {
            "site": site,
            "feature_index": int(feature_index),
            "pixel_center_sample_n": roi_pixel_centers,
            "shape": shape_metrics(geom),
            "crs_screening": crs_check,
            "layer_coverage": layer_coverage,
            "lola_direct_support": {
                "positive_count_n": positive_n,
                "zero_count_n": zero_n,
                "negative_count_n": negative_n,
                "masked_or_nonfinite_n": counts_missing_n,
                "positive_pct_of_valid_LDEC_cells": float(100.0 * positive_n / counts_valid_n) if counts_valid_n else None,
                "zero_pct_of_valid_LDEC_cells": float(100.0 * zero_n / counts_valid_n) if counts_valid_n else None,
                "positive_pct_of_all_ROI_pixel_centers": float(100.0 * positive_n / roi_pixel_centers),
                "zero_pct_of_all_ROI_pixel_centers": float(100.0 * zero_n / roi_pixel_centers),
                "LDEC_valid_pct_of_ROI_pixel_centers": float(100.0 * counts_valid_n / roi_pixel_centers),
                "positive_count_value_stats": numeric_stats(count_vals[count_vals > 0], ASSETS["counts"][1]),
            },
            "elevation": elevation_stats,
            "slope": numeric_stats(layer_values["slope"], ASSETS["slope"][1]),
            "z_uncertainty": numeric_stats(layer_values["z_uncertainty"], ASSETS["z_uncertainty"][1]),
            "slope_uncertainty": numeric_stats(layer_values["slope_uncertainty"], ASSETS["slope_uncertainty"][1]),
            "processing": {
                "pixel_selection": "Native raster pixel centers inside polygon (all_touched=False).",
                "pixel_weighting": "Unweighted pixel-center samples; no area weighting.",
                "reprojection": False,
                "resampling": False,
                "geometry_repair": False,
                "source_data_modified": False,
            },
        }
    finally:
        for ds in datasets.values():
            ds.close()


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, (float, np.floating)):
        if not math.isfinite(float(value)):
            return "—"
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_report(results: list[dict[str, Any]], output_dir: Path) -> str:
    rows = []
    for r in results:
        direct = r["lola_direct_support"]
        rows.append(
            "| {site} F{feature} | {role} | {n} | {area} | {direct}% | {zero}% | {s50}° | {s90}° | {sr50}° | {sr90}° | {z50} m | {z90} m | {relief} m | {shape} |".format(
                site=r["site"], feature=r["feature_index"], role=r["role"],
                n=r["pixel_center_sample_n"], area=fmt(r["shape"]["nominal_projected_area_m2"], 1),
                direct=fmt(direct["positive_pct_of_valid_LDEC_cells"], 2),
                zero=fmt(direct["zero_pct_of_valid_LDEC_cells"], 2),
                s50=fmt(r["slope"].get("median_p50")), s90=fmt(r["slope"].get("p90")),
                sr50=fmt(r["slope_uncertainty"].get("median_p50")), sr90=fmt(r["slope_uncertainty"].get("p90")),
                z50=fmt(r["z_uncertainty"].get("median_p50")), z90=fmt(r["z_uncertainty"].get("p90")),
                relief=fmt(r["elevation"].get("p90_minus_p10")),
                shape=fmt(r["shape"]["minimum_rotated_rectangle_aspect_ratio"], 2),
            )
        )
    table = "\n".join(rows)
    return f"""# LOLA ROI candidate screening

**Purpose:** Diagnostic candidate screening from native LOLA layers. This is not an AOI approval, final terrain fingerprint, site ranking, or base-site suitability result.

**Output directory:** {output_dir}

## Candidate summary

| Candidate | Role | ROI centers | Area (m²) | LDEC positive % | LDEC zero % | Slope P50 ° | Slope P90 ° | Slope RMS P50 ° | Slope RMS P90 ° | Z RMS P50 m | Z RMS P90 m | Elev. P90-P10 m | Aspect ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

## Interpretation and limitations

- Elevation P90-P10 is the within-ROI elevation distribution spread. It is not a neighborhood/moving-window local-relief measure. A true local-relief metric needs an agreed physical window and analysis scale.
- Slope statistics come from the provider slope raster. Z RMS and slope RMS statistics come from the corresponding uncertainty rasters; they are not independent validation of elevation or slope accuracy.
- LDEC positive counts are direct shot support; zero-count cells are counted separately and are not treated as NoData. Masked/non-finite cells are reported separately.
- Area and shape metrics are computed from the provider polygon coordinates in their nominal metre-based projected grid. They are geometry descriptors, not an assertion that the lunar datum is fully resolved.
- Each pixel center is sampled once, without pixel-area weighting. The nominal raster posting is 5 m and is not equivalent to effective terrain resolution.
- Candidate statistics are not combined into a score or automatic ranking. Cross-site comparisons remain provisional while the Moon-fixed reference frame (ME/PA), vertical reference, processing comparability, and the team-approved common analysis scale remain unresolved.
- The script performs no reprojection, resampling, geometry repair, or source-file modification.

## Candidate-specific results

See candidate_screening.json for the complete statistics and coverage counts, and candidate_screening.csv for the summary table.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="data/metadata/lola_candidate_screening_20261115",
        help="Base output directory. If it exists, a numbered new directory is used.",
    )
    args = parser.parse_args()

    out_dir = unique_output_dir(PROJECT_ROOT / args.output_dir)
    results: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        site = candidate["site"]
        feature = candidate["feature"]
        _, paths, roi_path = source_paths(site)
        if not roi_path.is_file():
            raise FileNotFoundError(f"Missing ROI shapefile: {roi_path}")
        gdf = gpd.read_file(roi_path).reset_index(drop=True)
        if gdf.crs is None:
            raise ValueError(f"{site}: ROI shapefile has no CRS metadata.")
        result = read_candidate(site, feature, gdf, paths)
        result["role"] = candidate["role"]
        result["screening_reason"] = candidate["reason"]
        expected_n = EXPECTED_PIXEL_CENTERS.get((site, feature))
        result["prior_roi_quality_audit_pixel_centers"] = expected_n
        result["pixel_center_count_matches_prior_audit"] = (
            result["pixel_center_sample_n"] == expected_n if expected_n is not None else None
        )
        if expected_n is not None and result["pixel_center_sample_n"] != expected_n:
            print(
                f"WARNING: {site} Feature {feature}: current pixel-center count "
                f"{result['pixel_center_sample_n']} differs from prior audit {expected_n}."
            )
        results.append(result)
        print(
            f"{site} Feature {feature}: centers={result['pixel_center_sample_n']}, "
            f"LDEC+={result['lola_direct_support']['positive_pct_of_valid_LDEC_cells']:.2f}%, "
            f"Slope P50={result['slope'].get('median_p50', float('nan')):.3f} deg, "
            f"Z RMS P50={result['z_uncertainty'].get('median_p50', float('nan')):.3f} m"
        )

    report = {
        "purpose": "Read-only LOLA provider ROI candidate screening",
        "is_AOI_approval": False,
        "is_final_terrain_fingerprint": False,
        "is_site_ranking": False,
        "source_data_modified": False,
        "reprojection_performed": False,
        "resampling_performed": False,
        "geometry_repair_performed": False,
        "common_analysis_scale_approved": False,
        "moon_fixed_reference_frame_resolved": False,
        "local_relief_status": "Deferred until a team-approved physical window and analysis scale are specified.",
        "pixel_selection": "Native raster pixel centers inside each provider polygon; all_touched=False.",
        "candidates": results,
    }
    json_path = out_dir / "candidate_screening.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    csv_path = out_dir / "candidate_screening.csv"
    fieldnames = [
        "site", "feature", "role", "pixel_center_sample_n", "area_m2", "perimeter_m",
        "compactness", "aspect_ratio", "LDEC_valid_pct", "LDEC_positive_pct_valid",
        "LDEC_zero_pct_valid", "slope_p50_deg", "slope_p75_deg", "slope_p90_deg",
        "z_rms_p50_m", "z_rms_p75_m", "z_rms_p90_m",
        "slope_rms_p50_deg", "slope_rms_p90_deg",
        "elevation_p10_m", "elevation_p50_m", "elevation_p90_m", "elevation_p90_minus_p10_m",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "site": r["site"], "feature": r["feature_index"], "role": r["role"],
                "pixel_center_sample_n": r["pixel_center_sample_n"],
                "area_m2": r["shape"]["nominal_projected_area_m2"],
                "perimeter_m": r["shape"]["perimeter_m"],
                "compactness": r["shape"]["compactness_4piA_over_P2"],
                "aspect_ratio": r["shape"]["minimum_rotated_rectangle_aspect_ratio"],
                "LDEC_valid_pct": r["lola_direct_support"]["LDEC_valid_pct_of_ROI_pixel_centers"],
                "LDEC_positive_pct_valid": r["lola_direct_support"]["positive_pct_of_valid_LDEC_cells"],
                "LDEC_zero_pct_valid": r["lola_direct_support"]["zero_pct_of_valid_LDEC_cells"],
                "slope_p50_deg": r["slope"].get("median_p50"),
                "slope_p75_deg": r["slope"].get("p75"),
                "slope_p90_deg": r["slope"].get("p90"),
                "z_rms_p50_m": r["z_uncertainty"].get("median_p50"),
                "z_rms_p75_m": r["z_uncertainty"].get("p75"),
                "z_rms_p90_m": r["z_uncertainty"].get("p90"),
                "slope_rms_p50_deg": r["slope_uncertainty"].get("median_p50"),
                "slope_rms_p90_deg": r["slope_uncertainty"].get("p90"),
                "elevation_p10_m": r["elevation"].get("p10"),
                "elevation_p50_m": r["elevation"].get("median_p50"),
                "elevation_p90_m": r["elevation"].get("p90"),
                "elevation_p90_minus_p10_m": r["elevation"].get("p90_minus_p10"),
            })

    md_path = out_dir / "candidate_screening.md"
    md_path.write_text(markdown_report(results, out_dir), encoding="utf-8")

    print("\nScreening complete. Source files were not modified.")
    print(f"Output directory: {out_dir.relative_to(PROJECT_ROOT)}")
    print(f"Markdown report:  {md_path.relative_to(PROJECT_ROOT)}")
    print(f"CSV summary:      {csv_path.relative_to(PROJECT_ROOT)}")
    print(f"JSON details:     {json_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
