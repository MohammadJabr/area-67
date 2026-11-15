#!/usr/bin/env python3
"""Read-only metadata audit for the selectively downloaded Connecting Ridge SDEM GeoTIFFs.

This utility inspects headers and metadata only. It does not read raster pixel
arrays, reproject, resample, modify, or combine any source datasets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import rasterio

DEFAULT_ROOT = Path("data/raw/moon/sdem_connecting_ridge/A3CLR22_6_Connecting_Ridge")
EXPECTED_LAYERS = (
    "A306_GLDELEV_005.tif",
    "A306_GLDMASK_005.tif",
    "A306_GLDBRES_005.tif",
    "A306_GLDSBCT_005.tif",
    "A306_GLDSBCTALL_005.tif",
)


def raster_metadata(path: Path) -> dict[str, Any]:
    """Return header-level metadata for one raster without reading pixel values."""
    with rasterio.open(path) as dataset:
        crs = dataset.crs
        return {
            "path": str(path),
            "driver": dataset.driver,
            "width": dataset.width,
            "height": dataset.height,
            "band_count": dataset.count,
            "dtypes": list(dataset.dtypes),
            "crs": crs.to_string() if crs else None,
            "crs_wkt": crs.to_wkt() if crs else None,
            "crs_geodetic": str(crs.geodetic_crs) if crs and crs.geodetic_crs else None,
            "bounds": {
                "left": dataset.bounds.left,
                "bottom": dataset.bounds.bottom,
                "right": dataset.bounds.right,
                "top": dataset.bounds.top,
            },
            "resolution": list(dataset.res),
            "transform": list(dataset.transform),
            "nodata": dataset.nodata,
            "nodatavals": list(dataset.nodatavals),
            "units": list(dataset.units),
            "descriptions": list(dataset.descriptions),
            "scales": list(dataset.scales),
            "offsets": list(dataset.offsets),
            "block_shapes": [list(shape) for shape in dataset.block_shapes],
            "mask_flags": [[flag.name for flag in flags] for flags in dataset.mask_flag_enums],
            "dataset_tags": dataset.tags(),
            "band_tags": [dataset.tags(index) for index in range(1, dataset.count + 1)],
        }


def same_grid(reference: dict[str, Any], candidate: dict[str, Any]) -> bool:
    """Check exact CRS, dimensions, and affine transform equality."""
    return (
        reference["crs_wkt"] == candidate["crs_wkt"]
        and reference["width"] == candidate["width"]
        and reference["height"] == candidate["height"]
        and reference["transform"] == candidate["transform"]
    )


def compare_grids(
    reference: dict[str, Any], candidate: dict[str, Any], *, tolerance_m: float = 0.01
) -> dict[str, Any]:
    """Explain why two rasters do or do not share an exact grid."""
    bound_keys = ("left", "bottom", "right", "top")
    bound_deltas = {
        key: candidate["bounds"][key] - reference["bounds"][key]
        for key in bound_keys
    }
    max_bound_delta = max(abs(value) for value in bound_deltas.values())
    same_crs = reference["crs_wkt"] == candidate["crs_wkt"]
    same_dimensions = (
        reference["width"] == candidate["width"]
        and reference["height"] == candidate["height"]
    )
    same_resolution = all(
        abs(a - b) <= tolerance_m
        for a, b in zip(reference["resolution"], candidate["resolution"])
    )
    same_extent = max_bound_delta <= tolerance_m
    return {
        "same_crs": same_crs,
        "same_dimensions": same_dimensions,
        "same_resolution": same_resolution,
        "same_extent_within_tolerance": same_extent,
        "max_absolute_bound_delta_m": max_bound_delta,
        "bound_deltas_m": bound_deltas,
        "same_grid": same_grid(reference, candidate),
    }


def print_metadata(metadata: dict[str, Any]) -> None:
    print(f"\n{'=' * 88}")
    print(metadata["path"])
    print(f"{'=' * 88}")
    for key in (
        "driver", "width", "height", "band_count", "dtypes", "crs",
        "crs_geodetic", "bounds", "resolution", "transform", "nodata",
        "nodatavals", "units", "descriptions", "scales", "offsets",
        "block_shapes", "mask_flags",
    ):
        print(f"{key}: {metadata[key]}")
    print("CRS WKT:")
    print(metadata["crs_wkt"] or "(missing)")
    print("Dataset tags:")
    print(json.dumps(metadata["dataset_tags"], indent=2, ensure_ascii=False))
    print("Band tags:")
    print(json.dumps(metadata["band_tags"], indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit downloaded SDEM GeoTIFF headers without reading raster pixels."
    )
    parser.add_argument(
        "--root", type=Path, default=DEFAULT_ROOT,
        help=f"Extracted Connecting Ridge directory (default: {DEFAULT_ROOT})",
    )
    args = parser.parse_args()
    root = args.root

    readme = root / "README.txt"
    if readme.is_file():
        print("CONNECTING RIDGE README")
        print("-" * 88)
        print(readme.read_text(encoding="utf-8", errors="replace"))
    else:
        print(f"README not found: {readme}")

    summaries: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for filename in EXPECTED_LAYERS:
        path = root / filename
        if not path.is_file():
            failures.append(f"Missing expected layer: {path}")
            continue
        try:
            summary = raster_metadata(path)
        except Exception as exc:  # report all failed layers in one pass
            failures.append(f"Could not inspect {path}: {type(exc).__name__}: {exc}")
            continue
        summaries[filename] = summary
        print(f"\nFile size: {path.stat().st_size:,} bytes")
        print_metadata(summary)

    reference_name = "A306_GLDELEV_005.tif"
    reference = summaries.get(reference_name)
    if reference:
        print("\nGRID COMPARISON AGAINST SDEM ELEVATION")
        print("-" * 88)
        for filename, summary in summaries.items():
            if filename == reference_name:
                continue
            comparison = compare_grids(reference, summary)
            if comparison["same_grid"]:
                status = "EXACT SAME GRID"
            elif (
                comparison["same_crs"]
                and comparison["same_extent_within_tolerance"]
                and not comparison["same_resolution"]
            ):
                status = "SAME CRS/FOOTPRINT; DIFFERENT PIXEL SIZE"
            elif (
                comparison["same_crs"]
                and comparison["max_absolute_bound_delta_m"] <= 20.0
            ):
                status = "SAME CRS; NEAR-COINCIDENT EXTENT; GRID DIFFERS"
            elif comparison["same_crs"]:
                status = "SAME CRS; EXTENT/GRID DIFFERS"
            else:
                status = "CRS DIFFERS; GRID DIFFERS"
            print(f"{filename}: {status}")
            print(
                f"  resolution: reference={reference['resolution']} m, "
                f"candidate={summary['resolution']} m"
            )
            print(
                f"  dimensions: reference={reference['width']}x{reference['height']}, "
                f"candidate={summary['width']}x{summary['height']}"
            )
            print(
                f"  max absolute bounds delta: "
                f"{comparison['max_absolute_bound_delta_m']:.6f} m"
            )
            print(f"  bounds deltas (candidate - reference): {comparison['bound_deltas_m']}")

    if failures:
        print("\nINSPECTION WARNINGS")
        for failure in failures:
            print(f"- {failure}")
        return 1 if not summaries else 0

    print("\nHeader inspection complete. No raster pixel arrays were read or modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
