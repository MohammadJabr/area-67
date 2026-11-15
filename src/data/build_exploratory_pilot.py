"""Rebuild the AREA 67 exploratory real-raster pilot using canonical feature and matching code.

All footprints remain exploratory reference-centred windows. This script does not
approve geomorphic AOIs, resolve the physical ROI shapefile frame, or certify safety.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from rasterio.windows import from_bounds

from src.features.terrain_fingerprint import TerrainConfig, calculate_terrain_fingerprint
from src.matching.pipeline import rank_terrain_fingerprints
from src.matching.sensitivity import run_matching_robustness


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def centered_bounds(x: float, y: float, side_m: float) -> tuple[float, float, float, float]:
    if not math.isfinite(side_m) or side_m <= 0:
        raise ValueError("side_m must be finite and positive")
    half = side_m / 2.0
    return x - half, y - half, x + half, y + half


def safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(safe(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _masked_values(array: np.ma.MaskedArray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(array.data, dtype=np.float64)
    valid = ~np.ma.getmaskarray(array) & np.isfinite(values)
    return values, valid


def summarize_count_layer(array: np.ma.MaskedArray) -> dict[str, float | int | None]:
    """Keep positive LDEC support, zero-count cells, and NoData separate."""
    values, valid = _masked_values(array)
    total = int(values.size)
    valid_count = int(valid.sum())
    positive = int(np.count_nonzero((values > 0) & valid))
    zero = int(np.count_nonzero((values == 0) & valid))
    missing = total - valid_count
    return {
        "native_quality_total_cells": total,
        "native_quality_valid_cells": valid_count,
        "native_quality_nodata_cells": missing,
        "ldec_positive_cells": positive,
        "ldec_zero_cells": zero,
        "ldec_valid_coverage_pct": 100.0 * valid_count / total if total else 0.0,
        "direct_observation_coverage_pct": 100.0 * positive / valid_count if valid_count else None,
        "ldec_zero_count_pct": 100.0 * zero / valid_count if valid_count else None,
        "ldec_nodata_pct": 100.0 * missing / total if total else 0.0,
    }


def summarize_uncertainty_layer(
    array: np.ma.MaskedArray, prefix: str, unit_suffix: str
) -> dict[str, float | int | None]:
    values, valid = _masked_values(array)
    sample = values[valid]
    if not sample.size:
        return {
            f"{prefix}_valid_native_cells": 0,
            f"{prefix}_median_{unit_suffix}": None,
            f"{prefix}_p90_{unit_suffix}": None,
        }
    p50, p90 = np.percentile(sample, [50, 90], method="linear")
    return {
        f"{prefix}_valid_native_cells": int(sample.size),
        f"{prefix}_median_{unit_suffix}": float(p50),
        f"{prefix}_p90_{unit_suffix}": float(p90),
    }


def read_native_window(
    raster_path: Path,
    bounds: tuple[float, float, float, float],
    *,
    reference_profile: Mapping[str, Any],
    expected_shape: tuple[int, int],
) -> np.ma.MaskedArray:
    with rasterio.open(raster_path) as dataset:
        if dataset.width != reference_profile["width"] or dataset.height != reference_profile["height"]:
            raise ValueError(f"Grid dimensions differ for support layer: {raster_path}")
        if dataset.transform != reference_profile["transform"] or dataset.crs != reference_profile["crs"]:
            raise ValueError(f"Grid transform/CRS differs for support layer: {raster_path}")
        window = from_bounds(*bounds, transform=dataset.transform).round_offsets().round_lengths()
        actual_bounds = dataset.window_bounds(window)
        if not np.allclose(actual_bounds, bounds, rtol=0.0, atol=1e-6):
            raise ValueError(
                f"Support window is not aligned to the native grid: requested={bounds}, "
                f"actual={actual_bounds}, raster={raster_path}"
            )
        data = dataset.read(1, window=window, masked=True)
        if data.shape != expected_shape:
            raise ValueError(f"Unexpected native support shape {data.shape}; expected {expected_shape}")
        return data


def analysis_transform(
    bounds: tuple[float, float, float, float], width: int, height: int
):
    left, bottom, right, top = bounds
    xres = (right - left) / width
    yres = (top - bottom) / height
    if xres <= 0 or not math.isclose(xres, yres, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"Analysis grid must be square and positive: {bounds}, {width}x{height}")
    return from_origin(left, top, xres, yres), xres, yres


def resample_elevation(
    source_path: Path,
    bounds: tuple[float, float, float, float],
    target_crs: Any,
    width: int,
    height: int,
) -> tuple[np.ndarray, Any, CRS, dict[str, Any]]:
    """Bilinearly prepare one source raster on the declared projected metre grid."""
    transform, pixel_width, pixel_height = analysis_transform(bounds, width, height)
    target_crs = CRS.from_user_input(target_crs)
    if not target_crs.is_projected or "met" not in str(target_crs.linear_units or "").lower():
        raise ValueError(f"Analysis CRS must be projected in metres: {target_crs}")
    destination = np.full((height, width), np.nan, dtype=np.float32)
    with rasterio.open(source_path) as source:
        if source.crs is None:
            raise ValueError(f"Source raster has no CRS: {source_path}")
        if abs(source.transform.b) > 1e-9 or abs(source.transform.d) > 1e-9:
            raise ValueError(f"Rotated/sheared source grid requires explicit handling: {source_path}")
        reproject(
            source=rasterio.band(source, 1),
            destination=destination,
            src_transform=source.transform,
            src_crs=source.crs,
            src_nodata=source.nodata,
            dst_transform=transform,
            dst_crs=target_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
            init_dest_nodata=True,
            num_threads=2,
        )
        metadata = {
            "source_crs": source.crs.to_string(),
            "source_transform": [float(x) for x in source.transform[:6]],
            "source_width": source.width,
            "source_height": source.height,
            "source_resolution": [float(source.res[0]), float(source.res[1])],
            "source_nodata": source.nodata,
            "source_mask_flags": [str(x) for x in source.mask_flag_enums[0]],
            "source_dtype": source.dtypes[0],
            "source_bounds": [float(x) for x in source.bounds],
            "analysis_crs": target_crs.to_string(),
            "analysis_transform": [float(x) for x in transform[:6]],
            "analysis_bounds": [float(x) for x in bounds],
            "analysis_shape": [height, width],
            "analysis_pixel_size_m": [pixel_width, pixel_height],
            "resampling": "GDAL/Rasterio bilinear elevation resampling",
            "coordinate_operation": (
                "Preserve source CRS and resample to local metric grid."
                if source.crs == target_crs
                else "Reproject source grid to declared local metric CRS."
            ),
        }
    if not np.isfinite(destination).any():
        raise ValueError(f"No valid elevation cells after resampling: {source_path}")
    return destination, transform, target_crs, metadata


def calculate_record(
    site: Mapping[str, Any],
    elevation: np.ndarray,
    transform: Any,
    processing_crs: Any,
    terrain_config: TerrainConfig,
    source_path: Path,
    source_root: Path,
    source_sha256: str,
    quality: Mapping[str, Any] | None,
    grid_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    px, py = abs(float(transform.a)), abs(float(transform.e))
    metrics, _ = calculate_terrain_fingerprint(
        elevation, pixel_width_m=px, pixel_height_m=py, config=terrain_config
    )
    valid = int(np.isfinite(elevation).sum())
    total = int(elevation.size)
    valid_pct = 100.0 * valid / total
    row: dict[str, Any] = {
        "site_id": str(site["site_id"]),
        "site_name": str(site["site_name"]),
        "planet": str(site["planet"]),
        "source_id": str(site["source_id"]),
        "source_name": str(site["source_name"]),
        "source_url": str(site.get("source_url") or ""),
        "product_version": str(site.get("product_version") or ""),
        "access_date": str(site.get("access_date") or ""),
        "license": str(site.get("license") or ""),
        "crs": processing_crs.to_wkt() if hasattr(processing_crs, "to_wkt") else str(processing_crs),
        "analysis_crs": processing_crs.to_string() if hasattr(processing_crs, "to_string") else str(processing_crs),
        "vertical_reference": str(site.get("vertical_reference") or "Not supplied"),
        "coordinate_frame": str(site.get("coordinate_frame") or "Not supplied"),
        "elevation_unit": str(site.get("elevation_unit") or "m"),
        "slope_unit": "degrees",
        "analysis_scale_status": "PROVISIONAL_30M_PILOT_ASSUMPTION",
        "aoi_status": str(site.get("aoi_status") or "PROVISIONAL_REFERENCE_WINDOW_NOT_APPROVED_AOI"),
        "aoi_approval": "NOT_APPROVED",
        "aoi_note": str(site.get("aoi_note") or ""),
        "scientific_status": "EXPLORATORY_NOT_APPROVED",
        "source_raster_path": source_path.relative_to(source_root).as_posix(),
        "source_checksum_sha256": source_sha256,
        "source_quality_note": str(site.get("source_quality_note") or ""),
        "effective_resolution_note": str(site.get("effective_resolution_note") or ""),
        "window_width_m": float(elevation.shape[1] * px),
        "window_height_m": float(elevation.shape[0] * py),
        "pixel_width_m": px,
        "pixel_height_m": py,
        "grid_shape": f"{elevation.shape[0]}x{elevation.shape[1]}",
        "area_km2": float(elevation.shape[0] * py * elevation.shape[1] * px / 1_000_000.0),
        "nodata_pct": 100.0 - valid_pct,
        "valid_coverage_pct": valid_pct,
        "valid_cell_count": valid,
        "processing_method": (
            "Prepared the declared common local metric grid, then used the canonical "
            "src.features.terrain_fingerprint.calculate_terrain_fingerprint function."
        ),
        "analysis_grid_metadata": dict(grid_metadata),
        **metrics,
    }
    if "latitude" in site:
        row["latitude"] = float(site["latitude"])
        row["longitude"] = float(site["longitude"])
    if quality:
        row.update(dict(quality))
    if site.get("provider_roi_union_overlap_pct") is not None:
        row["provider_roi_union_overlap_pct"] = float(site["provider_roi_union_overlap_pct"])
        row["provider_roi_overlap_note"] = str(site.get("provider_roi_overlap_note") or "")
    return row


def write_sample_grid(
    path: Path, elevation: np.ndarray, transform: Any, crs: Any, site_id: str, scale: float
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": int(elevation.shape[0]),
        "width": int(elevation.shape[1]),
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": np.nan,
        "compress": "deflate",
        "predictor": 3,
    }
    with rasterio.open(path, "w", **profile) as output:
        output.write(elevation.astype(np.float32), 1)
        output.update_tags(site_id=site_id, status="EXPLORATORY_NOT_APPROVED", analysis_scale_m=str(scale))
    return sha256_file(path)


def earth_window_feature(site: Mapping[str, Any], bounds: tuple[float, float, float, float]) -> dict[str, Any]:
    left, bottom, right, top = bounds
    crs = CRS.from_user_input(site["analysis_crs"])
    to_wgs84 = Transformer.from_crs(crs, CRS.from_epsg(4326), always_xy=True)
    corners = [(left, top), (right, top), (right, bottom), (left, bottom), (left, top)]
    ring = [[float(to_wgs84.transform(x, y)[0]), float(to_wgs84.transform(x, y)[1])] for x, y in corners]
    return {
        "type": "Feature",
        "id": str(site["site_id"]),
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {
            "site_name": str(site["site_name"]),
            "status": str(site.get("aoi_status", "PROVISIONAL_REFERENCE_WINDOW_NOT_APPROVED_AOI")),
            "approval": "NOT_APPROVED",
            "area_km2": (right - left) * (top - bottom) / 1_000_000.0,
            "analysis_crs": crs.to_string(),
            "anchor_source": str(site.get("anchor_source") or ""),
            "note": str(site.get("aoi_note") or ""),
        },
    }


def matching(
    records: Mapping[str, Mapping[str, Any]], config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    m = config["matching"]
    target_id = str(config["target"]["site_id"])
    candidates = {str(site["site_id"]): dict(records[str(site["site_id"])]) for site in config["earth_candidates"]}
    result = rank_terrain_fingerprints(
        dict(records[target_id]),
        candidates,
        m["weights"],
        m["tolerances"],
        mission_profile=m["mission_profile"],
        min_feature_group_completeness=float(m["min_feature_group_completeness"]),
        min_data_completeness=float(m["min_data_completeness"]),
        scale_relative_tolerance=float(m["scale_relative_tolerance"]),
        distribution_sum_tolerance_pp=float(m["distribution_sum_tolerance_pp"]),
    )
    if not result["ranking"]:
        raise RuntimeError(f"Canonical matcher rejected all candidates: {result['rejected_candidates']}")
    robustness = run_matching_robustness(
        result,
        m["weights"],
        relative_change=float(m["weight_sensitivity_relative_change"]),
        top_k=(1, 2),
        min_completeness=float(m["min_feature_group_completeness"]),
    )
    return result, robustness


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty CSV: {path}")
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: (
                    json.dumps(safe(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                    if isinstance(value, (dict, list, tuple))
                    else safe(value)
                )
                for key, value in row.items()
            })


def ranking_csv_rows(
    result: Mapping[str, Any],
    robustness: Mapping[str, Any],
    records: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    m = config["matching"]
    sensitivity = robustness["weight_sensitivity"]
    top_counts = sensitivity["top_k_counts"]
    top1 = top_counts.get(1, top_counts.get("1", {}))
    top2 = top_counts.get(2, top_counts.get("2", {}))
    baseline = robustness["slope_only_baseline"]["ranking"]
    baseline_rank = {item["site_id"]: int(item["rank"]) for item in baseline}
    output = []
    for item in result["ranking"]:
        site_id = item["site_id"]
        contributions = item["group_contributions"]
        stability = (
            f"Top-1 in {top1[site_id]}/{sensitivity['scenario_count']}; "
            f"Top-2 in {top2[site_id]}/{sensitivity['scenario_count']} "
            "one-at-a-time weight perturbation scenarios (descriptive, not probability)"
        )
        row = {
            "target_site_id": result["target_site_id"],
            "candidate_site_id": site_id,
            "mission_profile": result["mission_profile"],
            "rank": int(item["rank"]),
            "similarity_score": float(item["similarity_score"]),
            "weighted_distance": float(item["similarity_distance"]),
            "data_completeness": float(item["data_completeness"]),
            "feature_group_completeness": float(item["feature_group_completeness"]),
            "valid_raster_coverage_completeness": float(item["valid_raster_coverage_completeness"]),
            "target_valid_coverage_pct": float(item["target_valid_coverage_pct"]),
            "candidate_valid_coverage_pct": float(item["candidate_valid_coverage_pct"]),
            "target_direct_observation_coverage_pct": item["target_direct_observation_coverage_pct"],
            "candidate_direct_observation_coverage_pct": item["candidate_direct_observation_coverage_pct"],
            "target_analysis_scale_m": float(item["target_analysis_scale_m"]),
            "candidate_analysis_scale_m": float(item["candidate_analysis_scale_m"]),
            "slope_only_rank": baseline_rank.get(site_id),
            "rank_change_vs_slope_only": int(item["rank"]) - baseline_rank[site_id],
            "missing_groups": json.dumps(item["missing_groups"]),
            "method_warnings": json.dumps(item["method_warnings"]),
            "normalization_method": item["normalization_method"],
            "mission_weights": json.dumps(m["weights"], sort_keys=True),
            "feature_tolerances": json.dumps(m["tolerances"], sort_keys=True),
            "ranking_stability_note": stability,
            "ranking_note": (
                "EXPLORATORY ONLY: canonical feature/matching functions on real rasters in provisional "
                "reference-centred windows; not approved AOIs, site certification, or rover-safety evidence."
            ),
            "scientific_status": "EXPLORATORY_NOT_APPROVED",
            "group_distances": item["group_distances"],
            "group_contributions": contributions,
            "candidate_aoi_status": records[site_id].get("aoi_status"),
            "candidate_aoi_approval": records[site_id].get("aoi_approval"),
            "candidate_source_checksum_sha256": records[site_id].get("source_checksum_sha256"),
        }
        for group, value in contributions.items():
            row[f"{group}_contribution"] = float(value["distance_share"])
            row[f"{group}_weighted_squared_contribution"] = float(value["weighted_squared_contribution"])
            row[f"{group}_distance"] = float(value["group_distance"])
        output.append(row)
    return output


def relief_window_sensitivity(
    arrays: Mapping[str, tuple[np.ndarray, Any, Any]],
    records: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
    base_terrain_config: TerrainConfig,
) -> dict[str, Any]:
    ids = [str(config["target"]["site_id"])] + [
        str(site["site_id"]) for site in config["earth_candidates"]
    ]
    scenarios = []
    for requested in config["matching"]["relief_window_sensitivity_m"]:
        scenario_config = replace(base_terrain_config, relief_window_m=float(requested))
        scenario_records: dict[str, dict[str, Any]] = {}
        actual_cells = actual_span = None
        for site_id in ids:
            elevation, transform, _ = arrays[site_id]
            metrics, _ = calculate_terrain_fingerprint(
                elevation,
                pixel_width_m=abs(float(transform.a)),
                pixel_height_m=abs(float(transform.e)),
                config=scenario_config,
            )
            scenario_records[site_id] = {**dict(records[site_id]), **metrics}
            actual_cells = int(metrics["relief_window_cells"])
            actual_span = float(metrics["relief_window_span_m"])
        result, _ = matching(scenario_records, config)
        scenarios.append({
            "requested_window_m": float(requested),
            "cells": actual_cells,
            "actual_centre_to_centre_span_m": actual_span,
            "ranking": [
                {
                    "site_id": item["site_id"],
                    "rank": int(item["rank"]),
                    "weighted_distance": float(item["similarity_distance"]),
                    "similarity_score": float(item["similarity_score"]),
                    "local_relief_median": float(scenario_records[item["site_id"]]["local_relief_p95_p5"]),
                }
                for item in result["ranking"]
            ],
            "rejected_candidates": result["rejected_candidates"],
        })
    return {
        "status": "EXPLORATORY_NOT_APPROVED",
        "method": (
            "Recompute canonical Terrain Fingerprint and matching functions on the same prepared 30m grids, "
            "changing only requested Local Relief window. This is not analysis-scale sensitivity or AOI approval."
        ),
        "scenarios": scenarios,
    }


def build_report(
    rows: list[dict[str, Any]], rankings: list[dict[str, Any]], config: Mapping[str, Any]
) -> str:
    by_id = {row["site_id"]: row for row in rows}
    target = by_id[config["target"]["site_id"]]
    lines = [
        "# AREA 67 — Reproducible exploratory real-data pilot",
        "",
        "**Status: EXPLORATORY / NOT APPROVED FOR SCIENTIFIC SITE CERTIFICATION**",
        "",
        "Metrics are generated by the repository's canonical terrain fingerprint and matching functions from real NASA LOLA and Copernicus GLO-30 rasters.",
        "",
        "## Scope and limitations",
        "",
        "- Target: NASA PGDA Site01 990m x 990m context window. Recorded coordinate-plane overlap with the union of valid provider Site01 polygons is 3.8657%; this is not the provider ROI or an approved geomorphic AOI.",
        "- Earth windows: Haughton crater-centre reference, Yungay hyper-arid-core reference, and Mauna Kea volcano reference. All are provisional reference-centred samples.",
        "- Askja is held out because the selected reference window is dominated by near-flat/equal-elevation samples; this is not a conclusion about all Askja terrain.",
        "- Lunar surface elevation is bilinearly resampled from the source 5m LOLA grid to the common 30m local metric grid. Exact transforms and checksums are stored in run_manifest.json.",
        "- LDEC and RMS summaries use native 5m layers inside the exact same 990m analysis footprint (198 x 198 native cells); direct support and NoData remain separate.",
        "- Earth GLO-30 DSM tiles are bilinearly resampled to local UTM 30m grids. Effective terrain resolution and per-pixel quality companions were not established.",
        "- No absolute Moon-to-Earth elevation comparison, vertical offset, ROI geometry repair, or unverified Moon-frame transformation is applied.",
        "",
        "## Terrain fingerprints",
        "",
        "| Site | Slope P50 | Slope P90 | TRI P50 | TRI P90 | Local relief summary | Valid coverage |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['site_name']} | {float(row['slope_median']):.2f}° | {float(row['slope_p90']):.2f}° | "
            f"{float(row['tri_median']):.2f}m | {float(row['tri_p90']):.2f}m | "
            f"{float(row['local_relief_p95_p5']):.2f}m | {float(row['valid_coverage_pct']):.2f}% |"
        )
    lines += [
        "",
        "## Canonical matcher output (exploratory)",
        "",
        "| Rank | Candidate | Similarity index | Weighted distance |",
        "|---:|---|---:|---:|",
    ]
    for row in rankings:
        lines.append(
            f"| {row['rank']} | {row['candidate_site_id']} | {float(row['similarity_score']):.2f}/100 | {float(row['weighted_distance']):.4f} |"
        )
    lines += [
        "",
        "The similarity index is a monotonic relative ranking index under the configured features, tolerances, weights, windows, and source footprints. It is not a probability, safety rating, or physical-equivalence percentage.",
        "",
        "## Site01 native LOLA support",
        "",
        f"- Positive LDEC direct-shot support in the exact 990m footprint: **{float(target['direct_observation_coverage_pct']):.3f}%**.",
        f"- Zero-count/interpolated share among valid native LDEC cells: **{float(target['ldec_zero_count_pct']):.3f}%**.",
        f"- Median Z RMS in the same footprint: **{float(target['z_rms_median_m']):.4f}m**.",
        f"- Median slope RMS in the same footprint: **{float(target['slope_rms_median_deg']):.4f}°**.",
        "",
        "## Approval gates still open",
        "",
        "The team must approve geomorphic AOIs and physical frame/scale/quality decisions. Hiba must review canonical feature extraction and scale sensitivity; Omar must review canonical matching and sensitivity. The app and Passport must retain the exploratory warning until those gates are closed.",
        "",
    ]
    return "\n".join(lines)


def build_pilot(raw_root: Path, output_dir: Path, metadata_dir: Path, config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("status") != "EXPLORATORY_NOT_APPROVED":
        raise ValueError("Pilot config must explicitly remain EXPLORATORY_NOT_APPROVED.")
    grid = config["grid"]
    width, height = int(grid["width_pixels"]), int(grid["height_pixels"])
    scale = float(grid["analysis_scale_m"])
    if not math.isclose(width * scale, float(grid["width_m"])) or not math.isclose(height * scale, float(grid["height_m"])):
        raise ValueError("Configured grid dimensions do not match pixel count x analysis scale.")
    terrain_config = TerrainConfig(**config["terrain"])
    terrain_config.validate()

    run_dir = output_dir / "pilot_2026-11-15"
    grids_dir = run_dir / "sample_grids"
    grids_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict[str, Any]] = {}
    arrays: dict[str, tuple[np.ndarray, Any, Any]] = {}
    rows: list[dict[str, Any]] = []
    earth_features: list[dict[str, Any]] = []
    window_manifest: dict[str, Any] = {"status": "EXPLORATORY_NOT_APPROVED", "earth": []}
    input_hashes: dict[str, str] = {}
    grid_manifest: dict[str, Any] = {}

    # Moon: derive an exact 990m window from the centre of the earlier 1km context square.
    moon = config["target"]
    context = tuple(float(x) for x in moon["context_bounds_native_m"])
    cx = (context[0] + context[2]) / 2.0
    cy = (context[1] + context[3]) / 2.0
    moon_bounds = centered_bounds(cx, cy, float(grid["width_m"]))
    moon_elevation_path = raw_root / moon["source_elevation"]
    with rasterio.open(moon_elevation_path) as source:
        if source.crs is None:
            raise ValueError("Site01 LOLA source raster has no CRS.")
        moon_crs = source.crs
    moon_z, moon_transform, moon_analysis_crs, moon_grid_meta = resample_elevation(
        moon_elevation_path, moon_bounds, moon_crs, width, height
    )
    moon_sha = sha256_file(moon_elevation_path)
    input_hashes[moon["source_elevation"]] = moon_sha

    expected_native_side = int(round(float(grid["width_m"]) / 5.0))
    expected_native_shape = (expected_native_side, expected_native_side)
    with rasterio.open(moon_elevation_path) as reference:
        reference_profile = {
            "width": reference.width,
            "height": reference.height,
            "transform": reference.transform,
            "crs": reference.crs,
        }
    quality_paths = {
        "ldec": raw_root / moon["source_ldec"],
        "total_error": raw_root / moon["source_total_error"],
        "slope_error": raw_root / moon["source_slope_error"],
    }
    quality: dict[str, Any] = {}
    for name, path in quality_paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Required Site01 quality layer missing: {path}")
        layer = read_native_window(
            path, moon_bounds,
            reference_profile=reference_profile,
            expected_shape=expected_native_shape,
        )
        rel_path = path.relative_to(raw_root).as_posix()
        input_hashes[rel_path] = sha256_file(path)
        if name == "ldec":
            quality.update(summarize_count_layer(layer))
        elif name == "total_error":
            quality.update(summarize_uncertainty_layer(layer, "z_rms", "m"))
        else:
            quality.update(summarize_uncertainty_layer(layer, "slope_rms", "deg"))
    quality.update({
        "native_quality_pixel_size_m": 5.0,
        "native_quality_window_shape": [expected_native_side, expected_native_side],
        "native_quality_window_bounds_m": list(moon_bounds),
        "native_quality_window_area_km2": float(grid["width_m"]) * float(grid["height_m"]) / 1_000_000.0,
    })
    moon["source_quality_note"] = (
        "LDEC direct support, zero-count/interpolated share, Z RMS and slope RMS are read from native 5m "
        "companion layers inside the exact same 990m footprint as the 30m analysis grid. These metrics "
        "are separate from NoData on the 30m elevation grid. The context window overlaps 3.8657% of "
        "the valid provider Site01 ROI union in the recorded coordinate-plane diagnostic."
    )
    moon["effective_resolution_note"] = (
        "Product 90 bounded Site01 inspection: EFFRES P50 15.78m, P90 24.08m. Native 5m posting is not "
        "5m effective terrain resolution; the exploratory analysis grid is 30m."
    )
    moon_row = calculate_record(
        moon, moon_z, moon_transform, moon_analysis_crs, terrain_config,
        moon_elevation_path, raw_root, moon_sha, quality, moon_grid_meta,
    )
    records[moon["site_id"]] = moon_row
    rows.append(moon_row)
    arrays[moon["site_id"]] = (moon_z, moon_transform, moon_analysis_crs)
    moon_grid_path = grids_dir / f"{moon['site_id']}_30m.tif"
    moon_grid_sha = write_sample_grid(
        moon_grid_path, moon_z, moon_transform, moon_analysis_crs, moon["site_id"], scale
    )
    grid_manifest[moon["site_id"]] = {
        **moon_grid_meta,
        "source_raster": moon["source_elevation"],
        "source_checksum_sha256": moon_sha,
        "output_grid": moon_grid_path.relative_to(output_dir).as_posix(),
        "output_grid_checksum_sha256": moon_grid_sha,
        "native_quality_checksums": {
            Path(path).relative_to(raw_root).as_posix(): input_hashes[Path(path).relative_to(raw_root).as_posix()]
            for path in quality_paths.values()
        },
    }
    window_manifest["moon"] = {
        "site_id": moon["site_id"],
        "context_bounds_native_m": list(context),
        "analysis_bounds_native_m": list(moon_bounds),
        "analysis_grid_shape": [height, width],
        "analysis_resolution_m": scale,
        "crs_wkt": moon_analysis_crs.to_wkt(),
        "coordinate_frame_note": moon["coordinate_frame"],
        "aoi_approval": "NOT_APPROVED",
        "provider_roi_union_overlap_pct": moon.get("provider_roi_union_overlap_pct"),
        "aoi_note": moon["aoi_note"],
    }

    # Earth: anchor coordinates are transformed into explicitly declared local UTM metric CRSs.
    for site in config["earth_candidates"]:
        utm = CRS.from_user_input(site["analysis_crs"])
        transformer = Transformer.from_crs(CRS.from_epsg(4326), utm, always_xy=True)
        x, y = transformer.transform(float(site["longitude"]), float(site["latitude"]))
        bounds = centered_bounds(x, y, float(grid["width_m"]))
        source_path = raw_root / site["source_elevation"]
        elevation, transform, analysis_crs, grid_meta = resample_elevation(
            source_path, bounds, utm, width, height
        )
        checksum = sha256_file(source_path)
        input_hashes[site["source_elevation"]] = checksum
        site["source_quality_note"] = (
            "Copernicus GLO-30 DSM. No direct instrument-shot layer or per-pixel quality companion "
            "was retrieved. Effective terrain resolution is not independently established."
        )
        site["effective_resolution_note"] = (
            "Nominal GLO-30 posting is approximately 1 arc-second; effective terrain resolution is "
            "not independently established for this mirrored tile."
        )
        row = calculate_record(
            site, elevation, transform, analysis_crs, terrain_config,
            source_path, raw_root, checksum, None, grid_meta,
        )
        records[site["site_id"]] = row
        rows.append(row)
        arrays[site["site_id"]] = (elevation, transform, analysis_crs)
        sample_path = grids_dir / f"{site['site_id']}_30m.tif"
        sample_sha = write_sample_grid(sample_path, elevation, transform, analysis_crs, site["site_id"], scale)
        grid_manifest[site["site_id"]] = {
            **grid_meta,
            "source_raster": site["source_elevation"],
            "source_checksum_sha256": checksum,
            "output_grid": sample_path.relative_to(output_dir).as_posix(),
            "output_grid_checksum_sha256": sample_sha,
        }
        earth_features.append(earth_window_feature(site, bounds))
        window_manifest["earth"].append({
            "site_id": site["site_id"],
            "anchor_latitude": float(site["latitude"]),
            "anchor_longitude": float(site["longitude"]),
            "anchor_source": site["anchor_source"],
            "analysis_crs": utm.to_string(),
            "analysis_bounds_projected_m": list(bounds),
            "analysis_grid_shape": [height, width],
            "analysis_resolution_m": scale,
            "aoi_approval": "NOT_APPROVED",
            "aoi_note": site["aoi_note"],
        })

    result, robustness = matching(records, config)
    ranking_rows = ranking_csv_rows(result, robustness, records, config)
    relief_sensitivity = relief_window_sensitivity(arrays, records, config, terrain_config)

    write_csv(output_dir / "terrain_fingerprints.csv", rows)
    write_csv(output_dir / "candidate_rankings.csv", ranking_rows)
    robustness_document = {
        "status": "EXPLORATORY_NOT_APPROVED",
        "target_site_id": moon["site_id"],
        "mission_profile": config["matching"]["mission_profile"],
        "mission_weights": config["matching"]["weights"],
        "feature_tolerances": config["matching"]["tolerances"],
        "completeness_policy": {
            "min_feature_group_completeness": config["matching"]["min_feature_group_completeness"],
            "min_data_completeness": config["matching"]["min_data_completeness"],
        },
        "analysis_configuration": config["terrain"],
        "canonical_matching_result": result,
        "slope_only_baseline": robustness["slope_only_baseline"],
        "weight_sensitivity": robustness["weight_sensitivity"],
        "relief_window_sensitivity": relief_sensitivity,
        "rejected_candidates": result["rejected_candidates"],
        "held_out_candidates": config.get("held_out_candidates", []),
        "source_checksums": input_hashes,
        "source_grid_processing": grid_manifest,
        "limitations": [
            "All footprints are exploratory reference-centred windows, not approved geomorphic AOIs.",
            "The 990m Site01 context window overlaps only about 3.87% of the valid provider ROI union in the recorded coordinate-plane diagnostic.",
            "The provider ROI shapefile physical frame is not independently proven by matching projection mathematics.",
            "Site01 elevation is bilinearly resampled from 5m to 30m; LDEC and RMS are summarized from native 5m layers in the same exact footprint.",
            "Earth Copernicus GLO-30 DSMs are bilinearly resampled to local UTM 30m grids; effective terrain resolution and per-pixel quality were not established.",
            "Analysis scale, Local Relief window, valid-neighbour fraction, slope classes, weights and tolerances are provisional team assumptions.",
            "The similarity score is a relative ranking index, not a probability, safety rating, or site certification.",
        ],
    }
    write_json(output_dir / "ranking_robustness.json", robustness_document)
    write_json(run_dir / "pilot_sampling_windows.json", window_manifest)
    write_json(run_dir / "exploratory_run_config.json", config)
    write_json(run_dir / "earth_sampling_windows.geojson", {
        "type": "FeatureCollection",
        "name": "AREA 67 exploratory Earth reference windows",
        "features": earth_features,
    })
    (run_dir / "EXPLORATORY_PILOT_REPORT.md").write_text(
        build_report(rows, ranking_rows, config), encoding="utf-8"
    )

    manifest = {
        "status": "EXPLORATORY_NOT_APPROVED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": config_path.as_posix(),
        "config_sha256": sha256_file(config_path),
        "raw_root": raw_root.as_posix(),
        "analysis_scale_m": scale,
        "window_shape": [height, width],
        "input_sha256": input_hashes,
        "processing_grids": grid_manifest,
        "outputs": {},
    }
    outputs = [
        output_dir / "terrain_fingerprints.csv",
        output_dir / "candidate_rankings.csv",
        output_dir / "ranking_robustness.json",
        run_dir / "pilot_sampling_windows.json",
        run_dir / "exploratory_run_config.json",
        run_dir / "earth_sampling_windows.geojson",
        run_dir / "EXPLORATORY_PILOT_REPORT.md",
        *sorted(grids_dir.glob("*.tif")),
    ]
    for path in outputs:
        manifest["outputs"][path.relative_to(output_dir).as_posix()] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    write_json(run_dir / "run_manifest.json", manifest)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    write_json(metadata_dir / "run_manifest.json", manifest)

    return {
        "fingerprints_csv": (output_dir / "terrain_fingerprints.csv").as_posix(),
        "rankings_csv": (output_dir / "candidate_rankings.csv").as_posix(),
        "robustness_json": (output_dir / "ranking_robustness.json").as_posix(),
        "target_site_id": moon["site_id"],
        "candidate_count": len(config["earth_candidates"]),
        "ranking": ranking_rows,
        "rejected_candidates": result["rejected_candidates"],
        "direct_observation_coverage_pct": moon_row["direct_observation_coverage_pct"],
        "ldec_zero_count_pct": moon_row["ldec_zero_count_pct"],
        "run_manifest": (run_dir / "run_manifest.json").as_posix(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rebuild the exploratory Site01-to-Earth pilot using canonical AREA 67 feature/matching code."
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--metadata-dir", type=Path, default=Path("data/metadata/pilot_2026-11-15"))
    parser.add_argument("--config", type=Path, default=Path("config/exploratory_pilot_2026-11-15.json"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = build_pilot(args.raw_root, args.output_dir, args.metadata_dir, args.config)
    print(json.dumps(safe(summary), indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
