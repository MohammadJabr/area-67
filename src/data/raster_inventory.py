"""Read-only inventory helpers for geospatial raster inputs."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import rasterio
from pyproj import CRS as PyprojCRS
from rasterio.warp import transform_bounds


REPO_ROOT = Path(__file__).resolve().parents[2]


def _portable_path(path: str | Path) -> str:
    """Return repository-relative paths for artifacts created inside this checkout.

    External files retain the caller-supplied path because they cannot be made
    portable without an explicit shared data-root mapping.
    """
    supplied = Path(path)
    resolved = supplied.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(supplied)


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a streaming SHA-256 digest without loading a file into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _nodata_json(value: Any) -> Any:
    if isinstance(value, (float, np.floating)) and math.isnan(float(value)):
        return "NaN"
    if isinstance(value, np.generic):
        return value.item()
    return value


def _band_inventory(ds: rasterio.io.DatasetReader, band: int, elevation_range: tuple[float, float] | None) -> dict[str, Any]:
    valid_count = 0
    gdal_valid_count = 0
    nonfinite_count = 0
    nan_count = 0
    positive_infinity_count = 0
    negative_infinity_count = 0
    minimum = math.inf
    maximum = -math.inf
    total = 0.0
    total_sq = 0.0
    outside_range_count = 0
    for _, window in ds.block_windows(band):
        block = ds.read(band, window=window)
        gdal_valid = ds.read_masks(band, window=window) > 0
        finite = np.isfinite(block)
        valid = gdal_valid & finite
        values = block[valid].astype(np.float64, copy=False)
        gdal_valid_count += int(gdal_valid.sum())
        nonfinite_count += int((~finite).sum())
        nan_count += int(np.isnan(block).sum())
        positive_infinity_count += int(np.isposinf(block).sum())
        negative_infinity_count += int(np.isneginf(block).sum())
        if not values.size:
            continue
        valid_count += int(values.size)
        minimum = min(minimum, float(values.min()))
        maximum = max(maximum, float(values.max()))
        total += float(values.sum(dtype=np.float64))
        total_sq += float(np.square(values).sum(dtype=np.float64))
        if elevation_range is not None:
            outside_range_count += int(np.count_nonzero((values < elevation_range[0]) | (values > elevation_range[1])))

    statistics = None
    if valid_count:
        mean = total / valid_count
        variance = max(0.0, total_sq / valid_count - mean * mean)
        statistics = {
            "valid_pixel_count": valid_count,
            "valid_coverage_pct": 100.0 * valid_count / (ds.width * ds.height),
            "minimum": minimum,
            "maximum": maximum,
            "mean": mean,
            "standard_deviation_population": math.sqrt(variance),
        }
    band_report: dict[str, Any] = {
        "band": band,
        "unit": ds.units[band - 1] if ds.units else None,
        "gdal_valid_pixel_count": gdal_valid_count,
        "nodata_masked_pixel_count": ds.width * ds.height - gdal_valid_count,
        "nonfinite_pixel_count": nonfinite_count,
        "nan_pixel_count": nan_count,
        "positive_infinity_pixel_count": positive_infinity_count,
        "negative_infinity_pixel_count": negative_infinity_count,
        "mask_flags": [flag.name for flag in ds.mask_flag_enums[band - 1]],
        "statistics": statistics,
    }
    if elevation_range is not None:
        band_report["configured_range_screen"] = {
            "minimum": elevation_range[0],
            "maximum": elevation_range[1],
            "outside_pixel_count": outside_range_count,
            "interpretation": "User-configured review flag; not a universal physical validity threshold.",
        }
    return band_report


def inventory_raster(
    path: str | Path,
    *,
    checksum: bool = True,
    elevation_range: tuple[float, float] | None = None,
) -> dict[str, Any]:
    """Inventory raster metadata and streaming statistics; never writes to the input."""
    raster_path = Path(path)
    if not raster_path.is_file():
        raise FileNotFoundError(f"Raster does not exist: {raster_path}")
    if elevation_range is not None and elevation_range[0] > elevation_range[1]:
        raise ValueError("elevation_range minimum must not exceed maximum")

    with rasterio.open(raster_path) as ds:
        parsed_crs = PyprojCRS.from_user_input(ds.crs) if ds.crs else None
        is_lunar_crs = bool(
            parsed_crs
            and parsed_crs.ellipsoid
            and parsed_crs.ellipsoid.semi_major_metre < 100_000
        )
        wgs84_bounds = None
        wgs84_bounds_note = None
        if ds.crs and not is_lunar_crs:
            try:
                wgs84_bounds = list(transform_bounds(ds.crs, "EPSG:4326", *ds.bounds, densify_pts=21))
            except Exception as exc:
                wgs84_bounds_note = f"Transform to WGS84 failed: {exc}"
        elif is_lunar_crs:
            wgs84_bounds_note = "Not transformed: source ellipsoid is lunar; WGS84 Earth coordinates are inapplicable."
        namespaces = ds.tag_namespaces()
        metadata_tags = {"default": ds.tags()}
        for namespace in namespaces:
            metadata_tags[namespace] = ds.tags(ns=namespace)
        band_metadata_tags = []
        for index in range(1, ds.count + 1):
            band_namespaces = ds.tag_namespaces(index)
            tags = {"default": ds.tags(index)}
            for namespace in band_namespaces:
                tags[namespace] = ds.tags(index, ns=namespace)
            band_metadata_tags.append(tags)
        crs_units = None
        if parsed_crs and parsed_crs.axis_info:
            crs_units = parsed_crs.axis_info[0].unit_name
        report = {
            "path": _portable_path(raster_path),
            "file_size_bytes": raster_path.stat().st_size,
            "sha256": sha256_file(raster_path) if checksum else None,
            "driver": ds.driver,
            "width": ds.width,
            "height": ds.height,
            "band_count": ds.count,
            "data_types": list(ds.dtypes),
            "nodata": _nodata_json(ds.nodata),
            "crs": ds.crs.to_string() if ds.crs else None,
            "crs_wkt": ds.crs.to_wkt() if ds.crs else None,
            "transform": list(ds.transform)[:6],
            "bounds": list(ds.bounds),
            "bounds_wgs84_wsen": wgs84_bounds,
            "bounds_wgs84_note": wgs84_bounds_note,
            "pixel_size_x": float(ds.res[0]),
            "pixel_size_y": float(ds.res[1]),
            "pixel_spacing_units": crs_units,
            "is_north_up_non_rotated": bool(ds.transform.b == 0 and ds.transform.d == 0 and ds.transform.a > 0 and ds.transform.e < 0),
            "is_rotated_or_sheared": bool(ds.transform.b != 0 or ds.transform.d != 0),
            "area_or_point": ds.tags().get("AREA_OR_POINT"),
            "metadata_namespaces": namespaces,
            "dataset_metadata_tags": metadata_tags,
            "band_metadata_tags": band_metadata_tags,
            "bands": [
                _band_inventory(ds, index, elevation_range)
                for index in range(1, ds.count + 1)
            ],
        }
    return report


def inventory_many(
    paths: Iterable[str | Path],
    *,
    checksum: bool = True,
) -> dict[str, Any]:
    """Inventory explicit paths and report exact grid compatibility against the first."""
    entries = [inventory_raster(path, checksum=checksum) for path in paths]
    if not entries:
        raise ValueError("Provide at least one raster path")
    reference = entries[0]
    reference_grid = (reference["width"], reference["height"], reference["crs_wkt"], reference["transform"])
    for entry in entries:
        current_grid = (entry["width"], entry["height"], entry["crs_wkt"], entry["transform"])
        entry["grid_matches_first_raster"] = current_grid == reference_grid
    return {"raster_count": len(entries), "grid_reference": reference["path"], "rasters": entries}


def write_json(report: dict[str, Any], path: str | Path) -> None:
    """Write strict JSON when a caller explicitly supplies an output path."""
    Path(path).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
