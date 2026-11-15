"""Quality assurance for the five NASA GSFC PGDA LOLA Site04 rasters."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

try:
    from src.data.lola_site04 import ASSETS, RAW_DIR, REPO_ROOT
except ImportError:  # direct script execution from the repository root
    from lola_site04 import ASSETS, RAW_DIR, REPO_ROOT


JSON_PATH = REPO_ROOT / "data" / "metadata" / "site04_qa.json"
MARKDOWN_PATH = REPO_ROOT / "data" / "metadata" / "site04_qa.md"
PGDA_CATALOG = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/"
PAPER_DOI = "https://doi.org/10.1016/j.pss.2020.105119"
ASSET_MEANINGS = {
    "elevation": {
        "product": "LDEM surface-interpolated elevation",
        "unit": "m (surface height Z, per PGDA catalog)",
        "meaning": "Surface height; empty observation bins are filled by interpolation.",
    },
    "counts": {
        "product": "LDEC",
        "unit": "LOLA spot count per pixel (dimensionless count)",
        "meaning": "Number of LOLA spots in each pixel. Positive counts indicate direct spot support; zero means no spot was binned there and the LDEM is interpolated there.",
    },
    "slope": {
        "product": "Slope map",
        "unit": "degrees",
        "meaning": "Slope associated with the Site04 topographic product. The catalog does not specify the exact numerical slope operator/window; treat that algorithm detail as unknown.",
    },
    "z_uncertainty": {
        "product": "Total Z uncertainty",
        "unit": "m RMS error (per PGDA catalog)",
        "meaning": "Estimated elevation uncertainty accounting for track/orbit and interpolation error as described by Barker et al. (2021). It is not a per-pixel independent measurement error guarantee.",
    },
    "slope_uncertainty": {
        "product": "Slope uncertainty",
        "unit": "degrees RMS error (per PGDA catalog)",
        "meaning": "Estimated slope uncertainty; exact local statistical interpretation follows the source paper's method, not a confidence interval unless otherwise specified.",
    },
}
PERCENTILES = (0, 1, 5, 25, 50, 75, 95, 99, 100)


def finite_valid(data: np.ndarray, gdal_mask: np.ndarray) -> np.ndarray:
    """A usable value must be both GDAL-valid and finite."""
    return np.asarray(gdal_mask, dtype=bool) & np.isfinite(data)


def value_summary(data: np.ndarray, valid: np.ndarray) -> dict[str, Any]:
    values = np.asarray(data)[valid].astype(np.float64, copy=False)
    if values.size == 0:
        return {"valid_pixel_count": 0, "statistics": None}
    quantiles = np.percentile(values, PERCENTILES)
    return {
        "valid_pixel_count": int(values.size),
        "statistics": {
            "minimum": float(values.min()),
            "maximum": float(values.max()),
            "mean": float(values.mean()),
            "median": float(np.median(values)),
            "standard_deviation_population": float(values.std()),
            "percentiles": {str(p): float(q) for p, q in zip(PERCENTILES, quantiles)},
            "zero_count": int(np.count_nonzero(values == 0)),
            "negative_count": int(np.count_nonzero(values < 0)),
            "non_integer_count": int(np.count_nonzero(values != np.rint(values))),
        },
    }


def load_rasters(paths: dict[str, Path]) -> tuple[dict[str, np.ndarray], dict[str, dict[str, Any]]]:
    arrays: dict[str, np.ndarray] = {}
    masks: dict[str, np.ndarray] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for name in ASSETS:
        path = paths[name]
        if not path.is_file():
            raise FileNotFoundError(f"Missing {name} raster: {path}")
        with rasterio.open(path) as ds:
            if ds.count != 1:
                raise ValueError(f"{name} must be a single-band raster; found {ds.count} bands")
            arrays[name] = ds.read(1)
            masks[name] = ds.read_masks(1) > 0
            metadata[name] = {
                "file": str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path),
                "file_size_bytes": path.stat().st_size,
                "driver": ds.driver,
                "width": ds.width,
                "height": ds.height,
                "bands": ds.count,
                "dtype": ds.dtypes[0],
                "nodata": "NaN" if isinstance(ds.nodata, float) and math.isnan(ds.nodata) else ds.nodata,
                "crs_wkt": ds.crs.to_wkt() if ds.crs else None,
                "transform": list(ds.transform)[:6],
                "bounds": list(ds.bounds),
                "pixel_size_x": float(ds.res[0]),
                "pixel_size_y": float(abs(ds.res[1])),
                "area_or_point": ds.tags().get("AREA_OR_POINT"),
                "tags": ds.tags(),
                "band_tags": ds.tags(1),
                "gdal_mask_flags": [flag.name for flag in ds.mask_flag_enums[0]],
                "gdal_mask_valid_pixels": int(masks[name].sum()),
                "nodata_masked_pixel_count": int(ds.width * ds.height - masks[name].sum()),
                "nonfinite_pixels": int((~np.isfinite(arrays[name])).sum()),
            }
    return arrays, {**metadata, "_masks": masks}  # masks are kept internal until QA is complete


def analyze_arrays(
    arrays: dict[str, np.ndarray],
    metadata: dict[str, dict[str, Any]] | None = None,
    masks: dict[str, np.ndarray] | None = None,
    tile_size: int = 100,
) -> dict[str, Any]:
    """Analyze already loaded aligned arrays; also used by synthetic unit tests."""
    if set(arrays) != set(ASSETS):
        raise ValueError(f"Expected exactly these assets: {', '.join(ASSETS)}")
    if tile_size < 1:
        raise ValueError("tile_size must be at least 1 pixel")
    if masks is None:
        masks = {name: np.ones(a.shape, dtype=bool) for name, a in arrays.items()}
    shape = arrays["elevation"].shape
    if len(shape) != 2:
        raise ValueError("Each input array must be two-dimensional")
    shape_mismatch = {name: list(a.shape) for name, a in arrays.items() if a.shape != shape}
    if shape_mismatch:
        raise ValueError(f"Array dimension mismatch: {shape_mismatch}")
    mask_shape_mismatch = {name: list(mask.shape) for name, mask in masks.items() if mask.shape != shape}
    if set(masks) != set(ASSETS) or mask_shape_mismatch:
        raise ValueError(f"Mask shape/key mismatch: {mask_shape_mismatch or 'asset keys differ'}")

    valids = {name: finite_valid(arrays[name], masks[name]) for name in ASSETS}
    empty_layers = [name for name in ASSETS if not valids[name].any()]
    if empty_layers:
        raise ValueError(f"No finite GDAL-valid pixels in: {', '.join(empty_layers)}")
    elevation_valid = valids["elevation"]
    common_valid = np.logical_and.reduce([valids[name] for name in ASSETS])
    grid_checks = {
        "array_dimensions_match": True,
        "dimensions_pixels": {"width": shape[1], "height": shape[0]},
        "all_gdal_valid_masks_identical": all(np.array_equal(masks["elevation"], masks[n]) for n in ASSETS),
        "all_finite_valid_masks_identical": all(np.array_equal(elevation_valid, valids[n]) for n in ASSETS),
        "common_valid_pixel_count": int(common_valid.sum()),
        "common_valid_coverage_pct": 100.0 * float(common_valid.mean()),
        "per_asset_valid_pixel_count": {n: int(valids[n].sum()) for n in ASSETS},
        "mask_mismatch_pixels_vs_elevation": {
            n: int(np.count_nonzero(valids[n] != elevation_valid)) for n in ASSETS
        },
    }

    layer_reports: dict[str, Any] = {}
    for name in ASSETS:
        valid = valids[name]
        data = arrays[name]
        summary = value_summary(data, valid)
        values = data[valid].astype(np.float64, copy=False)
        physical_flags: dict[str, Any] = {}
        if name == "slope":
            physical_flags = {"outside_0_to_90_degrees": int(np.count_nonzero((values < 0) | (values > 90)))}
        elif name in ("z_uncertainty", "slope_uncertainty", "counts"):
            physical_flags = {"negative_values": int(np.count_nonzero(values < 0))}
        if name == "counts":
            physical_flags["non_integer_values"] = int(np.count_nonzero(values != np.rint(values)))
            positive = valid & (data > 0)
            zero = valid & (data == 0)
            layer_reports[name] = {
                **summary,
                "direct_observation_support": {
                    "positive_count_pixel_count": int(positive.sum()),
                    "positive_count_pixel_pct_of_valid": 100.0 * float(positive.sum()) / max(1, int(valid.sum())),
                    "zero_count_pixel_count": int(zero.sum()),
                    "zero_count_pixel_pct_of_valid": 100.0 * float(zero.sum()) / max(1, int(valid.sum())),
                    "count_value_frequency": {format(float(v), ".12g"): int(np.count_nonzero(values == v)) for v in np.unique(values)},
                    "interpretation": "PGDA defines LDEC as LOLA spots per pixel. Positive values indicate binned LOLA spot support. The Barker et al. method interpolates empty bins; zero LDEC pixels therefore represent interpolated LDEM cells, not direct observations.",
                },
                "screening_flags": physical_flags,
            }
        else:
            layer_reports[name] = {**summary, "screening_flags": physical_flags}
            if name in ("elevation", "z_uncertainty", "slope_uncertainty") and values.size:
                q1, q3 = np.percentile(values, [25, 75])
                iqr = q3 - q1
                low, high = q1 - 3 * iqr, q3 + 3 * iqr
                layer_reports[name]["exploratory_extreme_value_screen"] = {
                    "method": "Tukey 3-IQR fences; review flag only, not a scientific validity limit",
                    "lower_fence": float(low),
                    "upper_fence": float(high),
                    "flagged_pixel_count": int(np.count_nonzero((values < low) | (values > high))),
                }

    layer_reports["elevation"]["coverage"] = {
        "gdal_valid_pixels": int(masks["elevation"].sum()),
        "finite_unmasked_pixels": int(elevation_valid.sum()),
        "valid_coverage_pct": 100.0 * float(elevation_valid.mean()),
        "interpretation": "Raster value validity only; it does not imply a direct LOLA observation in every pixel.",
    }

    count_values = arrays["counts"]
    count_valid = valids["counts"]
    z_values = arrays["z_uncertainty"]
    z_valid = valids["z_uncertainty"]
    observed = count_valid & (count_values > 0) & z_valid
    interpolated = count_valid & (count_values == 0) & z_valid
    uncertainty_by_support: dict[str, Any] = {}
    for label, support_mask in (("positive_lola_count", observed), ("zero_lola_count", interpolated)):
        vals = z_values[support_mask].astype(np.float64, copy=False)
        uncertainty_by_support[label] = {
            "pixel_count": int(vals.size),
            "median_z_uncertainty_m": float(np.median(vals)) if vals.size else None,
            "p95_z_uncertainty_m": float(np.percentile(vals, 95)) if vals.size else None,
            "mean_z_uncertainty_m": float(vals.mean()) if vals.size else None,
        }

    high_z_cut = float(np.percentile(z_values[z_valid], 95))
    high_slope_unc_cut = float(np.percentile(arrays["slope_uncertainty"][valids["slope_uncertainty"]], 95))
    nrows, ncols = shape
    tiles: list[dict[str, Any]] = []
    for row0 in range(0, nrows, tile_size):
        for col0 in range(0, ncols, tile_size):
            sl = (slice(row0, min(row0 + tile_size, nrows)), slice(col0, min(col0 + tile_size, ncols)))
            cv = count_valid[sl]
            zv = z_valid[sl]
            sv = valids["slope_uncertainty"][sl]
            c = count_values[sl]
            z = z_values[sl]
            su = arrays["slope_uncertainty"][sl]
            tile_count = int(cv.sum())
            tile_z_count = int(zv.sum())
            t = {
                "row_start": row0,
                "row_end_exclusive": min(row0 + tile_size, nrows),
                "col_start": col0,
                "col_end_exclusive": min(col0 + tile_size, ncols),
                "valid_count_pixels": tile_count,
                "positive_count_pixel_pct": 100.0 * float(np.count_nonzero(cv & (c > 0))) / max(1, tile_count),
                "zero_count_pixel_pct": 100.0 * float(np.count_nonzero(cv & (c == 0))) / max(1, tile_count),
                "median_z_uncertainty_m": float(np.median(z[zv])) if tile_z_count else None,
                "p95_z_uncertainty_m": float(np.percentile(z[zv], 95)) if tile_z_count else None,
                "fraction_z_uncertainty_at_or_above_global_p95_pct": 100.0 * float(np.count_nonzero(zv & (z >= high_z_cut))) / max(1, tile_z_count),
                "median_slope_uncertainty_deg": float(np.median(su[sv])) if sv.any() else None,
                "fraction_slope_uncertainty_at_or_above_global_p95_pct": 100.0 * float(np.count_nonzero(sv & (su >= high_slope_unc_cut))) / max(1, int(sv.sum())),
            }
            # Derive map coordinates from the actual affine grid; do not assume a local origin.
            ref_meta = (metadata or {}).get("elevation", {})
            transform = ref_meta.get("transform")
            if transform and len(transform) >= 6:
                a, b, c, d, e, f = transform[:6]
                col_center = (t["col_start"] + t["col_end_exclusive"]) / 2.0
                row_center = (t["row_start"] + t["row_end_exclusive"]) / 2.0
                t["center_x_m"] = c + a * col_center + b * row_center
                t["center_y_m"] = f + d * col_center + e * row_center
            else:
                t["center_x_m"] = None
                t["center_y_m"] = None
            tiles.append(t)

    def ranked(key: str, reverse: bool, limit: int = 12) -> list[dict[str, Any]]:
        return sorted((t for t in tiles if t[key] is not None), key=lambda t: t[key], reverse=reverse)[:limit]

    return {
        "report_schema_version": 1,
        "study_area": "NASA LOLA Site04 (Shackleton rim)",
        "study_area_status": "Provisional working choice; not an officially approved team decision.",
        "sources": {"catalog": PGDA_CATALOG, "method_paper": PAPER_DOI},
        "definitions": ASSET_MEANINGS,
        "dataset_metadata": metadata or {},
        "grid_qa": grid_checks,
        "layers": layer_reports,
        "uncertainty_by_observation_support": uncertainty_by_support,
        "spatial_support_and_uncertainty": {
            "tile_size_pixels": tile_size,
            "nominal_tile_size_x_m": tile_size * float((metadata or {}).get("elevation", {}).get("pixel_size_x", 5.0)),
            "nominal_tile_size_y_m": tile_size * float((metadata or {}).get("elevation", {}).get("pixel_size_y", 5.0)),
            "high_uncertainty_cutoffs_are_empirical_p95": {
                "z_uncertainty_m": high_z_cut,
                "slope_uncertainty_degrees": high_slope_unc_cut,
                "note": "These relative screening cutoffs are dataset percentiles, not NASA quality acceptance thresholds.",
            },
            "weakest_direct_observation_support_tiles": ranked("positive_count_pixel_pct", False),
            "highest_median_z_uncertainty_tiles": ranked("median_z_uncertainty_m", True),
            "highest_median_slope_uncertainty_tiles": ranked("median_slope_uncertainty_deg", True),
        },
        "limitations": [
            "The 100% valid data mask describes finite raster pixels, not direct instrument observations.",
            "LDEC counts binned LOLA spots; zero-count cells have interpolated LDEM elevations per the product method.",
            "The exact slope numerical operator and neighborhood are not specified in the retrieved PGDA catalog and remain unknown here.",
            "A quality raster's RMS estimate is not a guarantee that every individual cell's true error equals that value.",
            "Empirical p95 and tile rankings are QA prioritization aids, not mission suitability thresholds.",
            "The local GeoTIFF CRS WKT identifies the lunar radius and polar stereographic parameters, but names the datum unknown; do not substitute an Earth EPSG CRS.",
            "Embedded GMT history metadata includes the generic output name test.grd; it is retained as source metadata but is not treated as independent evidence of processing provenance.",
        ],
    }


def markdown_report(report: dict[str, Any]) -> str:
    g = report["grid_qa"]
    lines = [
        "# NASA LOLA Site04 Raster QA",
        "",
        f"**Study area:** {report['study_area']} — {report['study_area_status']}",
        "",
        f"Catalog: {PGDA_CATALOG}  ",
        f"Method reference: Barker et al. (2021), {PAPER_DOI}",
        "",
        "## Executive QA results",
        "",
        f"- Dimensions: {g['dimensions_pixels']['width']} × {g['dimensions_pixels']['height']} pixels.",
        f"- Common valid coverage: {g['common_valid_coverage_pct']:.6f}% ({g['common_valid_pixel_count']:,} pixels).",
        f"- Identical GDAL masks: {g['all_gdal_valid_masks_identical']}; identical finite masks: {g['all_finite_valid_masks_identical']}.",
        f"- Per-pixel direct LOLA support (LDEC > 0): {report['layers']['counts']['direct_observation_support']['positive_count_pixel_pct_of_valid']:.4f}% of valid pixels.",
        f"- Valid zero-count/interpolated cells: {report['layers']['counts']['direct_observation_support']['zero_count_pixel_pct_of_valid']:.4f}% of valid pixels.",
        "",
        "## Product definitions and distributions",
        "",
        "| Asset | Meaning and unit | Valid pixels | Min | Median | Mean | Max | Review flags |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for name, definition in ASSET_MEANINGS.items():
        layer = report["layers"][name]
        s = layer.get("statistics")
        if s:
            flags = dict(layer.get("screening_flags", {}))
            if "exploratory_extreme_value_screen" in layer:
                flags["exploratory_3iqr_review_only"] = layer["exploratory_extreme_value_screen"]["flagged_pixel_count"]
            lines.append(f"| `{name}` | {definition['unit']} — {definition['product']} | {layer['valid_pixel_count']:,} | {s['minimum']:.6g} | {s['median']:.6g} | {s['mean']:.6g} | {s['maximum']:.6g} | `{json.dumps(flags, sort_keys=True)}` |")
    lines += [
        "",
        "### Observation support and uncertainty",
        "",
        "LDEC is the number of LOLA spots binned per pixel. A positive LDEC denotes direct spot support; zero means no spot was binned and the elevation was interpolated. Thus valid-data coverage and observation coverage are different quantities.",
        "",
        "| Support class | Pixels | Median Z RMS (m) | P95 Z RMS (m) |",
        "|---|---:|---:|---:|",
    ]
    for key, label in (("positive_lola_count", "LDEC > 0"), ("zero_lola_count", "LDEC = 0")):
        s = report["uncertainty_by_observation_support"][key]
        lines.append(f"| {label} | {s['pixel_count']:,} | {s['median_z_uncertainty_m']:.6g} | {s['p95_z_uncertainty_m']:.6g} |" if s['pixel_count'] else f"| {label} | 0 | n/a | n/a |")
    tile_info = report["spatial_support_and_uncertainty"]
    lines += ["", "### NoData and non-finite pixels", "", "| Asset | NoData-masked pixels | Non-finite band 1 pixels |", "|---|---:|---:|"]
    for name in ASSET_MEANINGS:
        meta = report["dataset_metadata"][name]
        lines.append(f"| `{name}` | {meta['nodata_masked_pixel_count']:,} | {meta['nonfinite_pixels']:,} |")
    lines += ["", "### Lowest direct-support tiles", "", f"Tiles are {tile_info['tile_size_pixels']}×{tile_info['tile_size_pixels']} pixels (nominally {tile_info['nominal_tile_size_x_m']:g} m × {tile_info['nominal_tile_size_y_m']:g} m). Coordinates are centers in the dataset's south polar stereographic X/Y frame, meters. The lowest 12 tiles by percentage of pixels with LDEC > 0 are shown; this is a relative ranking, not a pass/fail threshold.", "", "| Center X (m) | Center Y (m) | Positive-count pixels (%) | Zero-count pixels (%) | Median Z RMS (m) |", "|---:|---:|---:|---:|---:|"]
    for t in report["spatial_support_and_uncertainty"]["weakest_direct_observation_support_tiles"]:
        lines.append(f"| {t['center_x_m']:.1f} | {t['center_y_m']:.1f} | {t['positive_count_pixel_pct']:.3f} | {t['zero_count_pixel_pct']:.3f} | {t['median_z_uncertainty_m']:.4g} |")
    lines += ["", "### Highest median elevation-uncertainty tiles", "", "| Center X (m) | Center Y (m) | Median Z RMS (m) | P95 Z RMS (m) | Positive-count pixels (%) |", "|---:|---:|---:|---:|---:|"]
    for t in report["spatial_support_and_uncertainty"]["highest_median_z_uncertainty_tiles"]:
        lines.append(f"| {t['center_x_m']:.1f} | {t['center_y_m']:.1f} | {t['median_z_uncertainty_m']:.4g} | {t['p95_z_uncertainty_m']:.4g} | {t['positive_count_pixel_pct']:.3f} |")
    lines += ["", "### Highest median slope-uncertainty tiles", "", "| Center X (m) | Center Y (m) | Median slope RMS (degrees) | Positive-count pixels (%) |", "|---:|---:|---:|---:|"]
    for t in report["spatial_support_and_uncertainty"]["highest_median_slope_uncertainty_tiles"]:
        lines.append(f"| {t['center_x_m']:.1f} | {t['center_y_m']:.1f} | {t['median_slope_uncertainty_deg']:.4g} | {t['positive_count_pixel_pct']:.3f} |")
    lines += ["", "## Grid, masks, and value screening", "", f"Grid dimensions match: **{g['array_dimensions_match']}**. GDAL masks identical across assets: **{g['all_gdal_valid_masks_identical']}**. Finite valid masks identical: **{g['all_finite_valid_masks_identical']}**. Grid georeferencing (CRS, transform, and dimensions) is compared exactly by the script before producing this report.", "", "- NoData is read from the TIFF metadata; non-finite values are counted separately.", "- Slope values outside 0–90° and negative count/uncertainty values are flagged as physically suspicious.", "- Elevation and uncertainty Tukey 3-IQR fences are exploratory outlier screens only; flagged values are not automatically treated as errors.", "- Global p95 uncertainty cutoffs are relative data percentiles, not source-defined acceptance limits.", "", "## Metadata and limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines += ["", "The machine-readable details, transforms, CRS WKT, tags, per-layer distributions, masks, and tile rankings are in `site04_qa.json`.", ""]
    return "\n".join(lines)


def run(paths: dict[str, Path] | None = None, tile_size: int = 100) -> dict[str, Any]:
    paths = paths or {name: RAW_DIR / filename for name, filename in ASSETS.items()}
    arrays, metadata = load_rasters(paths)
    masks = metadata.pop("_masks")

    # Assert metadata-level co-registration exactly; no tolerance-based resampling is hidden here.
    reference = metadata["elevation"]
    mismatches: dict[str, list[str]] = {}
    for name in ASSETS:
        other = metadata[name]
        diff = []
        for key in ("width", "height", "bands", "crs_wkt", "transform", "bounds"):
            if other[key] != reference[key]:
                diff.append(key)
        if diff:
            mismatches[name] = diff
    if not reference["crs_wkt"]:
        raise ValueError("Elevation raster has no CRS; cannot verify geospatial alignment")
    if mismatches:
        raise ValueError(f"Grid georeferencing mismatch vs elevation: {mismatches}")
    report = analyze_arrays(arrays, metadata, masks, tile_size=tile_size)
    report["grid_qa"]["exact_metadata_grid_alignment"] = True
    report["grid_qa"]["metadata_compared"] = ["width", "height", "bands", "crs_wkt", "transform", "bounds"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tile-size", type=int, default=100, help="Spatial summary tile edge in pixels (default 100)")
    parser.add_argument("--json", type=Path, default=JSON_PATH)
    parser.add_argument("--markdown", type=Path, default=MARKDOWN_PATH)
    args = parser.parse_args()
    try:
        report = run(tile_size=args.tile_size)
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        args.markdown.write_text(markdown_report(report), encoding="utf-8")
        print(f"QA JSON: {args.json}")
        print(f"QA Markdown: {args.markdown}")
        print(f"Exact grid alignment: {report['grid_qa']['exact_metadata_grid_alignment']}")
        print(f"Common valid pixels: {report['grid_qa']['common_valid_pixel_count']:,} ({report['grid_qa']['common_valid_coverage_pct']:.6f}%)")
        support = report["layers"]["counts"]["direct_observation_support"]
        print(f"Positive LDEC pixels: {support['positive_count_pixel_count']:,} ({support['positive_count_pixel_pct_of_valid']:.4f}%)")
        print(f"Zero LDEC/interpolated pixels: {support['zero_count_pixel_count']:,} ({support['zero_count_pixel_pct_of_valid']:.4f}%)")
        return 0
    except (FileNotFoundError, ValueError, OSError, rasterio.errors.RasterioError) as exc:
        print(f"QA FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
