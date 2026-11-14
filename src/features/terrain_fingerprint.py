"""Reproducible terrain fingerprint extraction for AREA 67.

The raster pipeline intentionally accepts only pre-aligned, projected metre grids.
Reprojection, AOI approval, resampling and cross-planet datum decisions belong to
upstream data preparation and must be explicit rather than silently inferred here.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy import ndimage


RILEY_TRI_DEFINITION = (
    "Riley TRI: sqrt(sum((z_neighbor-z_center)^2) for the eight adjacent cells)"
)
FINGERPRINT_METRIC_COLUMNS = [
    "slope_median",
    "slope_p90",
    "slope_p95",
    "tri_median",
    "tri_p90",
    "local_relief_p95_p5",
    "local_relief_p90",
    "terrain_low_pct",
    "terrain_mid_pct",
    "terrain_high_pct",
    "largest_steep_patch_pct",
]


@dataclass(frozen=True)
class TerrainConfig:
    """Explicit analysis settings; no physical scale/window is silently chosen."""

    analysis_scale_m: float
    relief_window_m: float
    slope_low_max_deg: float = 10.0
    slope_mid_max_deg: float = 25.0
    steep_threshold_deg: float = 25.0
    connectivity: int = 8
    minimum_valid_coverage_pct: float = 80.0
    local_relief_min_valid_fraction: float = 0.8

    def validate(self) -> None:
        if not math.isfinite(self.analysis_scale_m) or self.analysis_scale_m <= 0:
            raise ValueError("analysis_scale_m must be a finite positive number")
        if not math.isfinite(self.relief_window_m) or self.relief_window_m <= 0:
            raise ValueError("relief_window_m must be a finite positive number")
        if not (0 <= self.slope_low_max_deg < self.slope_mid_max_deg <= 90):
            raise ValueError("Slope class thresholds must satisfy 0 <= low < mid <= 90 degrees")
        if not (0 <= self.steep_threshold_deg <= 90):
            raise ValueError("steep_threshold_deg must be between 0 and 90 degrees")
        if self.connectivity not in (4, 8):
            raise ValueError("connectivity must be 4 or 8")
        if not (0 <= self.minimum_valid_coverage_pct <= 100):
            raise ValueError("minimum_valid_coverage_pct must be between 0 and 100")
        if not (0 < self.local_relief_min_valid_fraction <= 1):
            raise ValueError("local_relief_min_valid_fraction must be in (0, 1]")


def _finite_2d(elevation: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    z = np.asarray(elevation, dtype=np.float64)
    if z.ndim != 2:
        raise ValueError("elevation must be a two-dimensional array")
    if min(z.shape) < 3:
        raise ValueError("elevation grid must be at least 3 by 3 cells")
    valid = np.isfinite(z)
    if not valid.any():
        raise ValueError("elevation grid contains no finite cells")
    return z, valid


def _slope_map(z: np.ndarray, valid: np.ndarray, pixel_width_m: float, pixel_height_m: float) -> np.ndarray:
    """Central-difference slope in degrees; never interpolate through NoData."""
    rows, cols = z.shape
    slope = np.full((rows, cols), np.nan, dtype=np.float64)
    center = valid[1:-1, 1:-1]
    complete = (
        center
        & valid[1:-1, :-2]
        & valid[1:-1, 2:]
        & valid[:-2, 1:-1]
        & valid[2:, 1:-1]
    )
    dz_dx = (z[1:-1, 2:] - z[1:-1, :-2]) / (2.0 * pixel_width_m)
    dz_dy = (z[2:, 1:-1] - z[:-2, 1:-1]) / (2.0 * pixel_height_m)
    inner = np.full(center.shape, np.nan, dtype=np.float64)
    inner[complete] = np.degrees(np.arctan(np.hypot(dz_dx[complete], dz_dy[complete])))
    slope[1:-1, 1:-1] = inner
    return slope


def _riley_tri_map(z: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Riley-style eight-neighbour TRI (vertical units), radius one cell."""
    tri = np.full(z.shape, np.nan, dtype=np.float64)
    center = z[1:-1, 1:-1]
    complete = valid[1:-1, 1:-1].copy()
    sum_sq = np.zeros(center.shape, dtype=np.float64)
    for row_offset in (-1, 0, 1):
        for col_offset in (-1, 0, 1):
            if row_offset == 0 and col_offset == 0:
                continue
            neighbour = z[1 + row_offset : z.shape[0] - 1 + row_offset,
                           1 + col_offset : z.shape[1] - 1 + col_offset]
            neighbour_valid = valid[1 + row_offset : z.shape[0] - 1 + row_offset,
                                    1 + col_offset : z.shape[1] - 1 + col_offset]
            complete &= neighbour_valid
            sum_sq += np.square(neighbour - center)
    inner = np.full(center.shape, np.nan, dtype=np.float64)
    inner[complete] = np.sqrt(sum_sq[complete])
    tri[1:-1, 1:-1] = inner
    return tri


def _window_cells(window_m: float, pixel_scale_m: float) -> tuple[int, float]:
    """Return an odd cell count and the centre-to-centre physical span.

    The requested physical window is converted to the nearest odd-sized window.
    The actual centre-to-centre span is recorded so rounding is transparent.
    """
    intervals = int(round(window_m / pixel_scale_m))
    if intervals < 2:
        raise ValueError("relief_window_m must span at least two pixel intervals")
    size = intervals + 1 if intervals % 2 == 0 else intervals
    if size % 2 == 0:
        size += 1
    if size < 3:
        size = 3
    return size, float((size - 1) * pixel_scale_m)


def _local_relief_map(
    z: np.ndarray,
    window_cells: int,
    minimum_valid_fraction: float,
) -> np.ndarray:
    """NaN-aware moving P95-P5; windows with insufficient support stay missing."""
    total = window_cells * window_cells
    minimum_count = max(3, int(math.ceil(total * minimum_valid_fraction)))

    def percentile_range(values: np.ndarray) -> float:
        finite = values[np.isfinite(values)]
        if finite.size < minimum_count:
            return np.nan
        p5, p95 = np.percentile(finite, [5, 95], method="linear")
        return float(p95 - p5)

    return ndimage.generic_filter(
        z,
        percentile_range,
        size=window_cells,
        mode="constant",
        cval=np.nan,
    ).astype(np.float64, copy=False)


def _summary(values: np.ndarray) -> dict[str, float | int]:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {"count": 0, "median": float("nan"), "p90": float("nan"), "p95": float("nan")}
    p50, p90, p95 = np.percentile(finite, [50, 90, 95], method="linear")
    return {
        "count": int(finite.size),
        "median": float(p50),
        "p90": float(p90),
        "p95": float(p95),
    }


def _largest_patch_pct(high_slope: np.ndarray, valid_slope: np.ndarray, connectivity: int) -> float:
    structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    labels, count = ndimage.label(high_slope & valid_slope, structure=structure)
    valid_count = int(valid_slope.sum())
    if valid_count == 0 or count == 0:
        return 0.0 if valid_count else float("nan")
    sizes = np.bincount(labels.ravel())
    largest = int(sizes[1:].max()) if sizes.size > 1 else 0
    return float(100.0 * largest / valid_count)


def calculate_terrain_fingerprint(
    elevation: np.ndarray,
    pixel_width_m: float,
    pixel_height_m: float,
    config: TerrainConfig,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Calculate the five feature groups from a pre-cropped, metric DEM array."""
    config.validate()
    if not math.isfinite(pixel_width_m) or not math.isfinite(pixel_height_m):
        raise ValueError("pixel dimensions must be finite")
    if pixel_width_m <= 0 or pixel_height_m <= 0:
        raise ValueError("pixel dimensions must be positive")
    tolerance = max(0.05, config.analysis_scale_m * 0.01)
    if abs(pixel_width_m - config.analysis_scale_m) > tolerance or abs(pixel_height_m - config.analysis_scale_m) > tolerance:
        raise ValueError(
            "DEM pixel dimensions do not match analysis_scale_m; explicitly prepare/resample all sites to the approved common scale first"
        )

    z, elevation_valid = _finite_2d(elevation)
    z = z.copy()
    z[~elevation_valid] = np.nan

    slope = _slope_map(z, elevation_valid, pixel_width_m, pixel_height_m)
    tri = _riley_tri_map(z, elevation_valid)
    relief_cells, relief_span_m = _window_cells(config.relief_window_m, config.analysis_scale_m)
    local_relief = _local_relief_map(z, relief_cells, config.local_relief_min_valid_fraction)

    slope_summary = _summary(slope)
    tri_summary = _summary(tri)
    relief_summary = _summary(local_relief)
    slope_valid = np.isfinite(slope)
    high = slope_valid & (slope >= config.steep_threshold_deg)
    valid_slope_count = int(slope_valid.sum())

    if valid_slope_count:
        low_pct = 100.0 * float((slope_valid & (slope < config.slope_low_max_deg)).sum()) / valid_slope_count
        mid_pct = 100.0 * float((slope_valid & (slope >= config.slope_low_max_deg) & (slope < config.slope_mid_max_deg)).sum()) / valid_slope_count
        high_pct = 100.0 * float((slope_valid & (slope >= config.slope_mid_max_deg)).sum()) / valid_slope_count
    else:
        low_pct = mid_pct = high_pct = float("nan")

    metrics: dict[str, Any] = {
        "analysis_scale_m": float(config.analysis_scale_m),
        "valid_cell_count": int(elevation_valid.sum()),
        "slope_valid_cell_count": slope_summary["count"],
        "tri_valid_cell_count": tri_summary["count"],
        "local_relief_valid_cell_count": relief_summary["count"],
        "slope_unit": "degrees",
        "slope_median": slope_summary["median"],
        "slope_p90": slope_summary["p90"],
        "slope_p95": slope_summary["p95"],
        "tri_definition": RILEY_TRI_DEFINITION,
        "tri_window_cells": 1,
        "tri_median": tri_summary["median"],
        "tri_p90": tri_summary["p90"],
        "relief_window_m": float(config.relief_window_m),
        "relief_window_cells": int(relief_cells),
        "relief_window_span_m": float(relief_span_m),
        "local_relief_p95_p5": relief_summary["median"],
        "local_relief_p90": relief_summary["p90"],
        "terrain_class_thresholds": (
            f"low < {config.slope_low_max_deg:g}; "
            f"mid >= {config.slope_low_max_deg:g} and < {config.slope_mid_max_deg:g}; "
            f"high >= {config.slope_mid_max_deg:g} degrees"
        ),
        "terrain_low_pct": float(low_pct),
        "terrain_mid_pct": float(mid_pct),
        "terrain_high_pct": float(high_pct),
        "steep_threshold_deg": float(config.steep_threshold_deg),
        "spatial_pattern_definition": (
            f"largest {config.connectivity}-connected patch with slope >= "
            f"{config.steep_threshold_deg:g} degrees / valid slope area"
        ),
        "largest_steep_patch_pct": _largest_patch_pct(high, slope_valid, config.connectivity),
        "connectivity": int(config.connectivity),
        "slope_distribution_sum_pct": float(low_pct + mid_pct + high_pct),
    }
    maps = {"slope": slope, "tri": tri, "local_relief": local_relief}
    return metrics, maps


def _read_geojson_geometries(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as stream:
        document = json.load(stream)
    kind = document.get("type")
    if kind == "FeatureCollection":
        geometries = [feature.get("geometry") for feature in document.get("features", [])]
    elif kind == "Feature":
        geometries = [document.get("geometry")]
    else:
        geometries = [document]
    geometries = [geometry for geometry in geometries if geometry]
    if not geometries:
        raise ValueError(f"AOI GeoJSON contains no geometries: {path}")
    return geometries


def _check_raster_grid(dataset: Any, config: TerrainConfig, elevation_unit: str) -> tuple[float, float]:
    if dataset.crs is None or not dataset.crs.is_projected:
        raise ValueError("DEM must be reprojected to a projected metric CRS before terrain derivatives are calculated")
    linear_units = str(dataset.crs.linear_units or "").lower()
    if "met" not in linear_units:
        raise ValueError(f"DEM CRS linear units must be metres; found {dataset.crs.linear_units!r}")
    transform = dataset.transform
    if abs(transform.b) > 1e-9 or abs(transform.d) > 1e-9:
        raise ValueError("rotated/sheared rasters must be warped to a north-up metric grid before analysis")
    pixel_width = abs(float(transform.a))
    pixel_height = abs(float(transform.e))
    if pixel_width <= 0 or pixel_height <= 0:
        raise ValueError("DEM affine transform has invalid pixel dimensions")
    if not (elevation_unit.lower() in {"m", "meter", "meters", "metre", "metres"}):
        raise ValueError("elevation_unit must explicitly be metres (m); convert units before analysis")
    tolerance = max(0.05, config.analysis_scale_m * 0.01)
    if abs(pixel_width - config.analysis_scale_m) > tolerance or abs(pixel_height - config.analysis_scale_m) > tolerance:
        raise ValueError(
            f"native grid is {pixel_width:g} x {pixel_height:g} m, not the declared "
            f"{config.analysis_scale_m:g} m analysis scale; prepare a common-scale raster explicitly"
        )
    return pixel_width, pixel_height


def analyze_geotiff(
    dem_path: str | Path,
    aoi_path: str | Path,
    site: Mapping[str, Any],
    config: TerrainConfig,
    write_maps_to: str | Path | None = None,
) -> dict[str, Any]:
    """Clip a GeoTIFF to a WGS84 GeoJSON AOI, validate its grid and extract metrics."""
    try:
        import rasterio
        from rasterio.features import geometry_mask
        from rasterio.warp import transform_geom
    except ImportError as exc:  # pragma: no cover - dependencies are project requirements
        raise RuntimeError("rasterio is required for GeoTIFF analysis") from exc

    dem_path = Path(dem_path)
    aoi_path = Path(aoi_path)
    site_id = str(site.get("site_id", "")).strip()
    source_id = str(site.get("source_id", "")).strip()
    planet = str(site.get("planet", "")).strip().title()
    if not site_id or not source_id or planet not in {"Earth", "Moon", "Mars"}:
        raise ValueError("Each site requires site_id, source_id, and planet in Earth/Moon/Mars")
    if not dem_path.is_file():
        raise FileNotFoundError(f"DEM not found: {dem_path}")
    if not aoi_path.is_file():
        raise FileNotFoundError(f"AOI GeoJSON not found: {aoi_path}")

    with rasterio.open(dem_path) as dataset:
        pixel_width, pixel_height = _check_raster_grid(dataset, config, str(site.get("elevation_unit", "")))
        geometries_wgs84 = _read_geojson_geometries(aoi_path)
        aoi_crs = str(site.get("aoi_crs", "EPSG:4326"))
        geometries = [transform_geom(aoi_crs, dataset.crs, geometry, precision=6) for geometry in geometries_wgs84]
        from rasterio.mask import mask as raster_mask
        clipped, clipped_transform = raster_mask(
            dataset,
            geometries,
            indexes=1,
            crop=True,
            filled=False,
            all_touched=False,
        )
        source_mask = np.ma.getmaskarray(clipped)
        z = np.asarray(np.ma.filled(clipped, np.nan), dtype=np.float64)
        inside_aoi = geometry_mask(
            geometries,
            out_shape=z.shape,
            transform=clipped_transform,
            invert=True,
            all_touched=False,
        )
        valid = inside_aoi & ~source_mask & np.isfinite(z)
        z[~valid] = np.nan
        aoi_cell_count = int(inside_aoi.sum())
        valid_cell_count = int(valid.sum())
        if aoi_cell_count == 0:
            raise ValueError(f"AOI has no pixel centres inside DEM: {site_id}")
        valid_coverage_pct = 100.0 * valid_cell_count / aoi_cell_count
        nodata_pct = 100.0 - valid_coverage_pct
        metrics, maps = calculate_terrain_fingerprint(z, pixel_width, pixel_height, config)
        required_metrics = (
            "slope_median", "slope_p90", "tri_median", "local_relief_p95_p5",
            "terrain_low_pct", "terrain_mid_pct", "terrain_high_pct",
            "largest_steep_patch_pct",
        )
        unavailable = [name for name in required_metrics if not np.isfinite(metrics[name])]
        if unavailable:
            raise ValueError(
                f"{site_id} does not have enough valid neighbourhood support for required features: "
                + ", ".join(unavailable)
            )

        flags: list[str] = []
        if valid_coverage_pct < config.minimum_valid_coverage_pct:
            flags.append(
                f"valid_coverage_below_{config.minimum_valid_coverage_pct:g}_pct"
            )
        if not site.get("quality_layer"):
            flags.append("no_per_pixel_quality_layer_reported")
        if not site.get("effective_resolution_note"):
            flags.append("effective_terrain_resolution_not_established")
        direct_support = site.get("direct_observation_coverage_pct")
        if direct_support is not None and not pd.isna(direct_support) and float(direct_support) < 20:
            flags.append("low_direct_observation_support_review_required")

        result: dict[str, Any] = {
            "site_id": site_id,
            "site_name": site.get("site_name"),
            "planet": planet,
            "source_id": source_id,
            "source_name": site.get("source_name"),
            "product_version": site.get("product_version"),
            "access_date": site.get("access_date"),
            "source_url": site.get("source_url"),
            "dem_path": str(dem_path),
            "aoi_path": str(aoi_path),
            "crs": dataset.crs.to_string(),
            "vertical_reference": site.get("vertical_reference"),
            "elevation_unit": "m",
            "pixel_width_m": pixel_width,
            "pixel_height_m": pixel_height,
            "analysis_scale_m": metrics["analysis_scale_m"],
            "aoi_cell_count": aoi_cell_count,
            "valid_cell_count": valid_cell_count,
            "nodata_pct": nodata_pct,
            "valid_coverage_pct": valid_coverage_pct,
            "direct_observation_coverage_pct": direct_support,
            "quality_layer": site.get("quality_layer"),
            "uncertainty_note": site.get("uncertainty_note"),
            "effective_resolution_note": site.get("effective_resolution_note"),
            "surface_type": site.get("surface_type"),
            **metrics,
            "quality_status": "WARN" if flags else "REVIEW",
            "quality_flags": ";".join(flags),
        }

        if write_maps_to is not None:
            output_dir = Path(write_maps_to) / site_id
            output_dir.mkdir(parents=True, exist_ok=True)
            profile = dataset.profile.copy()
            profile.update(
                driver="GTiff",
                height=z.shape[0],
                width=z.shape[1],
                count=1,
                dtype="float32",
                crs=dataset.crs,
                transform=clipped_transform,
                nodata=np.nan,
                compress="deflate",
                predictor=3,
            )
            for layer_name, array in maps.items():
                output_path = output_dir / f"{site_id}_{layer_name}.tif"
                with rasterio.open(output_path, "w", **profile) as output:
                    output.write(array.astype(np.float32), 1)
                    output.update_tags(
                        site_id=site_id,
                        source_id=source_id,
                        analysis_scale_m=str(config.analysis_scale_m),
                        method=(RILEY_TRI_DEFINITION if layer_name == "tri" else layer_name),
                        nodata_handling="NaN; no interpolation",
                    )
            result["derived_maps_dir"] = str(output_dir)
        return result


def analyze_run_config(config_path: str | Path, output_csv: str | Path, maps_dir: str | Path | None = None) -> pd.DataFrame:
    """Run all configured sites and write the canonical one-row-per-site CSV."""
    config_path = Path(config_path)
    with config_path.open("r", encoding="utf-8") as stream:
        document = json.load(stream)
    required = ("analysis_scale_m", "relief_window_m", "sites")
    missing = [key for key in required if key not in document or document[key] is None]
    if missing:
        raise ValueError(
            "Run configuration must explicitly set " + ", ".join(missing) +
            ". Do not guess the common analysis scale or local-relief window."
        )
    run_config = TerrainConfig(
        analysis_scale_m=float(document["analysis_scale_m"]),
        relief_window_m=float(document["relief_window_m"]),
        slope_low_max_deg=float(document.get("slope_low_max_deg", 10)),
        slope_mid_max_deg=float(document.get("slope_mid_max_deg", 25)),
        steep_threshold_deg=float(document.get("steep_threshold_deg", 25)),
        connectivity=int(document.get("connectivity", 8)),
        minimum_valid_coverage_pct=float(document.get("minimum_valid_coverage_pct", 80)),
        local_relief_min_valid_fraction=float(document.get("local_relief_min_valid_fraction", 0.8)),
    )
    run_config.validate()
    sites = document.get("sites")
    if not isinstance(sites, list) or not sites:
        raise ValueError("Run configuration must include at least one approved site")
    ids = [str(site.get("site_id", "")).strip() for site in sites]
    if any(not site_id for site_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("Every configured site must have a non-empty unique site_id")
    rows = []
    for site in sites:
        rows.append(
            analyze_geotiff(
                site["dem_path"],
                site["aoi_path"],
                site,
                run_config,
                write_maps_to=maps_dir,
            )
        )
    frame = pd.DataFrame(rows)
    from .validation import validate_fingerprint_rows
    validation_errors = validate_fingerprint_rows(frame)
    if validation_errors:
        raise ValueError("Generated fingerprints violate the integration contract: " + "; ".join(validation_errors))
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_csv, index=False, na_rep="")
    return frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="Approved JSON run configuration")
    parser.add_argument("--output", type=Path, default=Path("data/processed/terrain_fingerprints.csv"))
    parser.add_argument("--maps-dir", type=Path, default=None, help="Optional output directory for GeoTIFF feature maps")
    args = parser.parse_args()
    try:
        frame = analyze_run_config(args.config, args.output, args.maps_dir)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Terrain fingerprint run failed: {exc}\n")
    print(f"Wrote {len(frame)} site fingerprints to {args.output}")
    print(frame[["site_id", "planet", "valid_coverage_pct", "slope_median", "tri_median", "local_relief_p95_p5", "quality_status"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
