#!/usr/bin/env python3
"""Read-only evidence screen for Site01 LOLA + A306 SDEM + bounded Product 90 COGs.

The script does not reproject, resample, repair geometry, alter source rasters,
or create a final AOI. It samples original ROI polygons and a 1 km screening
square in native map coordinates after comparing nominal polar-stereographic
projection mathematics. The Site01 ROI shapefile's physical datum remains
unresolved; all ROI/SDEM overlay statistics are therefore diagnostic only.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import CRS
from rasterio.mask import mask as raster_mask
from shapely.geometry import mapping

DEFAULT_SDEM_ROOT = Path(
    "data/raw/moon/sdem_connecting_ridge/A3CLR22_6_Connecting_Ridge"
)
DEFAULT_ROI = Path("data/raw/moon/roi_shapes/Site01/Site01_ROIs.shp")
DEFAULT_LOLA_ROOT = Path("data/raw/moon/site01")
DEFAULT_OUTPUT = Path("data/metadata/site01_sdem_quality_screen_20261115")

SDEM_LAYERS = {
    "sdem_elevation": "A306_GLDELEV_005.tif",
    "sfs_data_mask": "A306_GLDMASK_005.tif",
    "best_input_resolution": "A306_GLDBRES_005.tif",
    "solar_bin_count": "A306_GLDSBCT_005.tif",
    "solar_bin_count_all": "A306_GLDSBCTALL_005.tif",
    "sdem_elevation_uncertainty": "A306_GLDISGM_005.tif",
    "sdem_minus_lola_difference": "A306_GLDDIFF_005.tif",
}
LOLA_LAYERS = {
    "lola_elevation": "Site01_final_adj_5mpp_surf.tif",
    "lola_direct_shot_count": "Site01_final_adj_5mpp_ldec.tif",
    "lola_slope": "Site01_final_adj_5mpp_slp.tif",
    "lola_z_rms_uncertainty": "Site01_final_adj_5mpp_toterr.tif",
    "lola_slope_rms_uncertainty": "Site01_final_adj_5mpp_slperr.tif",
}
PRODUCT90_COGS = {
    "lola_effective_resolution_20m": (
        "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
        "LDEM_80S_20MPP_ADJ_EFFRES.TIF"
    ),
    "lola_direct_shot_count_20m": (
        "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
        "LDEC_80S_20MPP_ADJ.TIF"
    ),
    "lola_height_error_20m": (
        "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
        "LDEM_80S_20MPP_ADJ_ERR.TIF"
    ),
}


def _safe_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def nominal_polar_signature(crs_like: Any) -> dict[str, Any]:
    """Extract projection mathematics without asserting the datum identity."""
    crs = CRS.from_user_input(crs_like)
    if not crs.is_projected:
        raise ValueError("CRS is not projected")
    axis_units = [str(axis.unit_name or "").casefold() for axis in crs.axis_info]
    if not axis_units or any("met" not in unit for unit in axis_units[:2]):
        raise ValueError(f"CRS axes are not metre-based: {axis_units}")

    proj_dict = crs.to_dict()
    projection = str(proj_dict.get("proj", "")).casefold()
    if projection not in {"stere", "sterea"}:
        method = (crs.coordinate_operation.method_name or "") if crs.coordinate_operation else ""
        if "polar stereographic" not in method.casefold():
            raise ValueError(f"CRS is not a recognized stereographic projection: {projection or method}")

    radius = _safe_float(proj_dict.get("R"))
    if radius is None:
        radius = _safe_float(crs.ellipsoid.semi_major_metre)
    flattening = _safe_float(crs.ellipsoid.inverse_flattening)
    if radius is None or abs(radius - 1_737_400.0) > 1.0:
        raise ValueError(f"CRS lunar sphere radius is not 1,737,400 m: {radius}")
    if flattening not in (None, 0.0):
        raise ValueError(f"CRS ellipsoid is not spherical (inverse flattening={flattening})")

    lat0 = _safe_float(proj_dict.get("lat_0"))
    lon0 = _safe_float(proj_dict.get("lon_0"))
    x0 = _safe_float(proj_dict.get("x_0", 0.0))
    y0 = _safe_float(proj_dict.get("y_0", 0.0))
    if lat0 is None or lon0 is None or x0 is None or y0 is None:
        raise ValueError(f"CRS is missing polar stereographic parameters: {proj_dict}")
    return {
        "projection": projection,
        "radius_m": radius,
        "latitude_of_origin_deg": lat0,
        "central_meridian_deg": lon0,
        "false_easting_m": x0,
        "false_northing_m": y0,
        "linear_units": axis_units[:2],
        "datum_name": crs.datum.name if crs.datum else None,
        "crs_wkt": crs.to_wkt(),
    }


def same_nominal_polar_math(left: Any, right: Any, tolerance: float = 1e-6) -> bool:
    """Compare sphere and projection parameters; intentionally ignore datum labels."""
    a = nominal_polar_signature(left)
    b = nominal_polar_signature(right)
    numeric_keys = (
        "radius_m",
        "latitude_of_origin_deg",
        "central_meridian_deg",
        "false_easting_m",
        "false_northing_m",
    )
    return (
        a["projection"] == b["projection"]
        and a["linear_units"] == b["linear_units"]
        and all(abs(a[key] - b[key]) <= tolerance for key in numeric_keys)
    )


def summarize_values(values: np.ndarray, masked_count: int = 0) -> dict[str, Any]:
    """Summarize a raster sample, retaining zeros separately from missing cells."""
    array = np.asarray(values, dtype=np.float64).ravel()
    finite = array[np.isfinite(array)]
    result: dict[str, Any] = {
        "sample_count_including_masked": int(array.size + masked_count),
        "masked_or_nonfinite_count": int(masked_count + array.size - finite.size),
        "valid_count": int(finite.size),
        "valid_pct": 0.0 if array.size + masked_count == 0 else 100.0 * finite.size / (array.size + masked_count),
    }
    if finite.size == 0:
        result.update({"min": None, "p10": None, "p25": None, "median": None,
                       "p75": None, "p90": None, "p95": None, "max": None,
                       "mean": None, "std_population": None, "zero_pct": None,
                       "positive_pct": None, "unique_value_count": 0})
        return result
    q = np.percentile(finite, [10, 25, 50, 75, 90, 95], method="linear")
    result.update({
        "min": float(np.min(finite)),
        "p10": float(q[0]),
        "p25": float(q[1]),
        "median": float(q[2]),
        "p75": float(q[3]),
        "p90": float(q[4]),
        "p95": float(q[5]),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "std_population": float(np.std(finite)),
        "zero_pct": 100.0 * float(np.count_nonzero(finite == 0)) / finite.size,
        "positive_pct": 100.0 * float(np.count_nonzero(finite > 0)) / finite.size,
        "unique_value_count": int(np.unique(finite).size),
    })
    return result


def raster_metadata(dataset: rasterio.io.DatasetReader) -> dict[str, Any]:
    crs = dataset.crs
    return {
        "width": int(dataset.width),
        "height": int(dataset.height),
        "band_count": int(dataset.count),
        "dtype": list(dataset.dtypes),
        "resolution_m": [float(value) for value in dataset.res],
        "bounds": [float(dataset.bounds.left), float(dataset.bounds.bottom),
                   float(dataset.bounds.right), float(dataset.bounds.top)],
        "transform": [float(value) for value in dataset.transform],
        "nodata": [None if value is None else (str(value) if not math.isfinite(value) else float(value))
                   for value in dataset.nodatavals],
        "units": list(dataset.units),
        "descriptions": list(dataset.descriptions),
        "crs_wkt": crs.to_wkt() if crs else None,
        "crs_datum_name": (CRS.from_user_input(crs).datum.name if crs else None),
    }


def _window_sample(dataset: rasterio.io.DatasetReader, bounds: tuple[float, float, float, float]) -> dict[str, Any]:
    from rasterio.windows import Window, from_bounds

    requested = from_bounds(*bounds, transform=dataset.transform)
    requested = requested.round_offsets().round_lengths()
    clipped = requested.intersection(Window(0, 0, dataset.width, dataset.height))
    if clipped.width <= 0 or clipped.height <= 0:
        return {"status": "no_overlap", "metadata": raster_metadata(dataset)}
    data = dataset.read(1, window=clipped, masked=True)
    mask = np.ma.getmaskarray(data)
    values = np.asarray(data.data, dtype=np.float64)
    return {
        "status": "sampled",
        "metadata": raster_metadata(dataset),
        "window_pixels": [int(clipped.width), int(clipped.height)],
        "sample_bounds": list(bounds),
        "statistics": summarize_values(values[~mask], int(mask.sum())),
    }


def _polygon_sample(dataset: rasterio.io.DatasetReader, geometry: Any) -> dict[str, Any]:
    if geometry is None or geometry.is_empty:
        return {"status": "empty_geometry"}
    if not geometry.is_valid:
        return {"status": "invalid_geometry_omitted"}
    try:
        clipped, _ = raster_mask(
            dataset,
            [mapping(geometry)],
            crop=True,
            all_touched=False,
            filled=False,
            indexes=1,
        )
    except ValueError as exc:
        if "do not overlap" in str(exc).casefold():
            return {"status": "no_overlap"}
        raise
    data = clipped[0] if clipped.ndim == 3 else clipped
    mask = np.ma.getmaskarray(data)
    values = np.asarray(data.data, dtype=np.float64)
    return {
        "status": "sampled",
        "raster_window_shape": [int(data.shape[1]), int(data.shape[0])],
        "statistics": summarize_values(values[~mask], int(mask.sum())),
    }


def build_screen_square(gdf: gpd.GeoDataFrame, indices: Iterable[int], side_m: float = 1000.0) -> tuple[float, float, float, float]:
    geometries = [gdf.geometry.iloc[index] for index in indices
                  if index < len(gdf) and gdf.geometry.iloc[index] is not None
                  and not gdf.geometry.iloc[index].is_empty
                  and gdf.geometry.iloc[index].is_valid]
    if not geometries:
        raise ValueError("No valid Site01 provider ROI geometries available for screening bounds")
    minx = min(geom.bounds[0] for geom in geometries)
    miny = min(geom.bounds[1] for geom in geometries)
    maxx = max(geom.bounds[2] for geom in geometries)
    maxy = max(geom.bounds[3] for geom in geometries)
    center_x = (minx + maxx) / 2.0
    center_y = (miny + maxy) / 2.0
    half = side_m / 2.0
    return (center_x - half, center_y - half, center_x + half, center_y + half)


def _unique_output_dir(path: Path) -> Path:
    candidate = path
    index = 2
    while candidate.exists():
        candidate = path.with_name(f"{path.name}_{index:02d}")
        index += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Site01 LOLA + A306 SDEM + Product 90 Effective Resolution Screen",
        "",
        f"Generated: {report['generated_utc']}",
        "",
        "**Status:** Read-only evidence screen. Not an AOI approval, final terrain fingerprint, or site ranking.",
        "",
        "## Coordinate and method safeguards",
        "",
        f"- Nominal polar projection mathematics match between Site01 raster and SDEM: **{report['coordinate_review']['site01_vs_sdem_nominal_math_match']}**.",
        f"- SDEM/ROI physical Moon-fixed frame independently proven: **{report['coordinate_review']['roi_body_fixed_frame_proven']}**.",
        "- ROI overlays use raw native X/Y map coordinates only; no reprojection, resampling, geometry repair, or raster writing was performed.",
        "- SDEM and ROI overlay statistics are diagnostic only because the original ROI shapefile datum remains unknown.",
        "- The one-kilometre square is a screening window derived from the valid Site01 provider polygons, not an approved study AOI.",
        "- Five-metre posting is not interpreted as effective terrain resolution.",
        "",
        "## Local layer coverage and distributions",
        "",
        "| Layer | Grid (m) | Sample area | Valid n | Masked / non-finite | Zero % | Positive % | P50 | P90 | P95 |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["local_samples"]:
        stats = row.get("statistics") or {}
        meta = row.get("metadata") or {}
        res = meta.get("resolution_m") or [None, None]
        grid = "x".join("n/a" if v is None else f"{v:g}" for v in res)
        fmt = lambda value: "n/a" if value is None else f"{value:.4g}"
        lines.append(
            f"| {row['layer']} | {grid} | {row['sample_area']} | "
            f"{stats.get('valid_count', 0)} | {stats.get('masked_or_nonfinite_count', 0)} | "
            f"{fmt(stats.get('zero_pct'))} | {fmt(stats.get('positive_pct'))} | "
            f"{fmt(stats.get('median'))} | {fmt(stats.get('p90'))} | {fmt(stats.get('p95'))} |"
        )
    lines += ["", "## Feature-level screening", ""]
    for layer in report["feature_samples"]:
        lines.append(f"### {layer['layer']}")
        lines.append("")
        lines.append("| Feature | Status | Valid n | P50 | P90 | P95 | Zero % | Positive % |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|---:|")
        for feature in layer["features"]:
            stats = feature.get("statistics") or {}
            fmt = lambda value: "n/a" if value is None else f"{value:.4g}"
            lines.append(
                f"| {feature['feature_index']} | {feature['status']} | {stats.get('valid_count', 0)} | "
                f"{fmt(stats.get('median'))} | {fmt(stats.get('p90'))} | {fmt(stats.get('p95'))} | "
                f"{fmt(stats.get('zero_pct'))} | {fmt(stats.get('positive_pct'))} |"
            )
        lines.append("")
    lines += ["## Product 90 bounded COG windows", ""]
    if report["product90_samples"]:
        lines += ["| Product | Status | Native resolution (m) | Valid n | P50 | P90 | P95 |", "|---|---|---:|---:|---:|---:|---:|"]
        for row in report["product90_samples"]:
            stats = row.get("statistics") or {}
            meta = row.get("metadata") or {}
            res = meta.get("resolution_m") or [None, None]
            fmt = lambda value: "n/a" if value is None else f"{value:.4g}"
            lines.append(
                f"| {row['layer']} | {row['status']} | {fmt(max(map(abs, res)) if all(v is not None for v in res) else None)} | "
                f"{stats.get('valid_count', 0)} | {fmt(stats.get('median'))} | {fmt(stats.get('p90'))} | {fmt(stats.get('p95'))} |"
            )
    else:
        lines.append("No Product 90 windows were read.")
    lines += ["", "## Warnings", ""]
    if report["warnings"]:
        lines.extend(f"- {warning}" for warning in report["warnings"])
    else:
        lines.append("- None.")
    lines += [
        "",
        "## Reproducibility and provenance",
        "",
        "- SDEM standard products: GLDMASK (point count / number of input images), GLDISGM (elevation uncertainty), GLDDIFF (difference to LOLA reference), GLDBRES (best input-image resolution), and GLDSBCT (solar bins per pixel). Values are reported as distributions, not converted to a binary quality score.",
        "- Product 90 EFFRES values are reported in metres as effective resolution; they are distinct from nominal 20 m posting and from LDEC spot counts.",
        "- Original data files remain unchanged. Output files are small JSON and Markdown summaries only.",
        "",
    ]
    return "\n".join(lines)


def run_screen(
    sdem_root: Path = DEFAULT_SDEM_ROOT,
    roi_path: Path = DEFAULT_ROI,
    lola_root: Path = DEFAULT_LOLA_ROOT,
    output_root: Path = DEFAULT_OUTPUT,
    include_remote: bool = True,
    timeout: int = 25,
) -> Path:
    missing = [str(path) for path in (roi_path,) if not path.is_file()]
    missing += [str(lola_root / filename) for filename in LOLA_LAYERS.values()
                if not (lola_root / filename).is_file()]
    if missing:
        raise FileNotFoundError("Required Site01 inputs are missing:\n" + "\n".join(missing))

    gdf = gpd.read_file(roi_path)
    if gdf.crs is None:
        raise ValueError("Site01 ROI shapefile has no declared CRS; refusing to guess")
    site01_elev_path = lola_root / LOLA_LAYERS["lola_elevation"]
    with rasterio.open(site01_elev_path) as site01_ds:
        site01_crs = site01_ds.crs
        if site01_crs is None:
            raise ValueError("Site01 LOLA elevation raster has no CRS")
        site01_signature = nominal_polar_signature(site01_crs)
        screen_bounds = build_screen_square(gdf, range(5), 1000.0)

    roi_sig = nominal_polar_signature(gdf.crs)
    roi_math_match = same_nominal_polar_math(gdf.crs, site01_crs)
    if not roi_math_match:
        raise ValueError("Site01 ROI and Site01 raster do not share the nominal polar projection math; no samples were taken")

    report: dict[str, Any] = {
        "purpose": "Read-only Site01 SDEM and effective-resolution evidence screen",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"roi": str(roi_path), "lola_root": str(lola_root), "sdem_root": str(sdem_root)},
        "screening_window_bounds_native_m": list(screen_bounds),
        "coordinate_review": {
            "roi_crs_metadata_equals_site01_raster": CRS.from_user_input(gdf.crs) == CRS.from_user_input(site01_crs),
            "roi_and_site01_raster_nominal_math_match": roi_math_match,
            "site01_raster_nominal_projection": site01_signature,
            "roi_nominal_projection": roi_sig,
            "roi_body_fixed_frame_proven": False,
            "site01_vs_sdem_nominal_math_match": None,
            "site01_sdem_crs_metadata_equal": None,
            "projection_note": "Comparison ignores datum labels and is only a nominal coordinate-plane check; the legacy Site01 ROI shapefile's physical frame remains unconfirmed.",
        },
        "source_data_modified": False,
        "reprojection_performed": False,
        "resampling_performed": False,
        "geometry_repair_performed": False,
        "remote_cog_full_download_performed": False,
        "local_samples": [],
        "feature_samples": [],
        "product90_samples": [],
        "warnings": [],
    }

    sdem_paths = {name: sdem_root / filename for name, filename in SDEM_LAYERS.items()}
    required_sdem_layers = {"sdem_elevation", "sfs_data_mask", "best_input_resolution",
                            "solar_bin_count", "solar_bin_count_all"}
    for name, path in sdem_paths.items():
        if not path.is_file():
            if name in required_sdem_layers:
                report["warnings"].append(f"Missing required local SDEM layer: {path}")
            continue
        with rasterio.open(path) as ds:
            if ds.crs is None:
                report["warnings"].append(f"SDEM layer has no CRS: {path}")
                continue
            try:
                sdem_sig = nominal_polar_signature(ds.crs)
                math_match = same_nominal_polar_math(site01_crs, ds.crs)
            except ValueError as exc:
                report["warnings"].append(f"Could not validate SDEM projection for {path}: {exc}")
                continue
            report["coordinate_review"]["site01_vs_sdem_nominal_math_match"] = math_match
            report["coordinate_review"]["site01_sdem_crs_metadata_equal"] = CRS.from_user_input(site01_crs) == CRS.from_user_input(ds.crs)
            if not math_match:
                report["warnings"].append(f"SDEM layer not sampled because nominal projection math differs: {path}")
                continue
            screen_sample = _window_sample(ds, screen_bounds)
            if screen_sample.get("status") == "sampled":
                report["local_samples"].append({
                    "layer": name,
                    "sample_area": "1 km screening square",
                    **screen_sample,
                })
            else:
                report["warnings"].append(f"Screening square does not overlap SDEM layer: {path}")
            features = []
            for feature_index in range(min(5, len(gdf))):
                geom = gdf.geometry.iloc[feature_index]
                sample = _polygon_sample(ds, geom)
                features.append({"feature_index": feature_index, **sample})
            report["feature_samples"].append({"layer": name, "features": features})

    for name, filename in LOLA_LAYERS.items():
        path = lola_root / filename
        with rasterio.open(path) as ds:
            sample = _window_sample(ds, screen_bounds)
            if sample.get("status") == "sampled":
                report["local_samples"].append({
                    "layer": name,
                    "sample_area": "1 km screening square",
                    **sample,
                })

    if include_remote:
        for name, url in PRODUCT90_COGS.items():
            try:
                from src.data.remote_cog_inspection import probe_http_range
                probe = probe_http_range(url, probe_bytes=16_384, timeout=timeout)
                with rasterio.Env(
                    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                    CPL_VSIL_CURL_USE_HEAD="YES",
                    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff,.TIF,.TIFF",
                    VSI_CACHE="FALSE",
                    GDAL_HTTP_TIMEOUT=str(max(1, timeout)),
                ):
                    with rasterio.open("/vsicurl/" + url) as ds:
                        if ds.crs is None or not same_nominal_polar_math(site01_crs, ds.crs):
                            raise ValueError("Product 90 native map projection does not match Site01 nominal projection math")
                        sample = _window_sample(ds, screen_bounds)
                        sample["layer"] = name
                        sample["url"] = url
                        sample["range_probe"] = probe
                        if sample.get("status") == "sampled":
                            sample["note"] = "Bounded native-grid sample only; the complete COG was not downloaded."
                        report["product90_samples"].append(sample)
            except Exception as exc:
                report["warnings"].append(f"Product 90 bounded COG sample failed for {name}: {type(exc).__name__}: {exc}")
                report["product90_samples"].append({"layer": name, "status": "unavailable", "url": url, "error": f"{type(exc).__name__}: {exc}"})

    output_dir = _unique_output_dir(output_root)
    report_path = output_dir / "site01_sdem_quality_screen.json"
    markdown_path = output_dir / "site01_sdem_quality_screen.md"
    report["output_directory"] = str(output_dir)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    print(f"Wrote: {markdown_path}")
    print(f"Wrote: {report_path}")
    print(f"Site01 1 km screening square (native metres): {screen_bounds}")
    print(f"Site01 / ROI projection math match: {roi_math_match}")
    print(f"Site01 / SDEM nominal math match: {report['coordinate_review']['site01_vs_sdem_nominal_math_match']}")
    print(f"Local layers sampled: {len(report['local_samples'])}")
    print(f"Product 90 bounded windows: {sum(x.get('status') == 'sampled' for x in report['product90_samples'])}/{len(report['product90_samples'])}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    print("Read-only screen complete. Source rasters and geometries were not modified.")
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdem-root", type=Path, default=DEFAULT_SDEM_ROOT)
    parser.add_argument("--roi", type=Path, default=DEFAULT_ROI)
    parser.add_argument("--lola-root", type=Path, default=DEFAULT_LOLA_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-remote", action="store_true", help="Skip Product 90 HTTP range COG samples")
    parser.add_argument("--timeout", type=int, default=25)
    args = parser.parse_args(argv)
    try:
        run_screen(
            sdem_root=args.sdem_root,
            roi_path=args.roi,
            lola_root=args.lola_root,
            output_root=args.output,
            include_remote=not args.no_remote,
            timeout=args.timeout,
        )
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        parser.exit(2, f"Site01 SDEM screen failed safely: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
