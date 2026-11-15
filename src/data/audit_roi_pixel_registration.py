"""Audit ROI polygon vertices against a raster's affine pixel lattice.

This read-only diagnostic quantifies whether source ROI vertices coincide
with raster pixel centres, pixel corners, or neither. It does not reproject,
shift, repair, rasterize, or modify any source geometry or raster.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterator

import rasterio

try:
    from .lola_roi_quality import same_crs
except ImportError:
    from lola_roi_quality import same_crs


def _iter_geometry_vertices(geometry: Any) -> Iterator[tuple[float, float]]:
    """Yield XY vertices from polygon rings and nested geometry collections."""
    if geometry is None or geometry.is_empty:
        return

    geometry_type = geometry.geom_type
    if geometry_type == "Polygon":
        for coordinate in geometry.exterior.coords:
            yield float(coordinate[0]), float(coordinate[1])
        for ring in geometry.interiors:
            for coordinate in ring.coords:
                yield float(coordinate[0]), float(coordinate[1])
        return

    if geometry_type in {"Point", "LineString", "LinearRing"}:
        for coordinate in geometry.coords:
            yield float(coordinate[0]), float(coordinate[1])
        return

    if hasattr(geometry, "geoms"):
        for child in geometry.geoms:
            yield from _iter_geometry_vertices(child)


def _nearest_lattice_residual(
    column: float,
    row: float,
    *,
    offset: float,
    transform: Any,
) -> tuple[float, float, float]:
    """Return fractional pixel offsets and their map-unit magnitude.

    offset=0.5 represents pixel centres in the corner-based affine coordinate
    system; offset=0.0 represents pixel corners.
    """
    nearest_column = round(column - offset) + offset
    nearest_row = round(row - offset) + offset
    delta_column = column - nearest_column
    delta_row = row - nearest_row

    # Apply the affine linear part so this remains correct for rotated/sheared
    # grids instead of assuming north-up square pixels.
    delta_x = transform.a * delta_column + transform.b * delta_row
    delta_y = transform.d * delta_column + transform.e * delta_row
    residual_m = math.hypot(delta_x, delta_y)
    return delta_column, delta_row, residual_m


def audit_shapefile_registration(
    shapefile_path: str | Path,
    raster_path: str | Path,
    *,
    tolerance_m: float = 1e-6,
) -> dict[str, Any]:
    """Measure every source vertex's residual to pixel-centre and pixel-corner lattices."""
    if not math.isfinite(tolerance_m) or tolerance_m <= 0:
        raise ValueError("tolerance_m must be a finite positive number")

    shapefile_path = Path(shapefile_path)
    raster_path = Path(raster_path)
    if not shapefile_path.is_file():
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")
    if not raster_path.is_file():
        raise FileNotFoundError(f"Reference raster not found: {raster_path}")

    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError("ROI registration audit requires geopandas") from exc

    frame = gpd.read_file(shapefile_path)
    if frame.crs is None:
        raise ValueError(f"{shapefile_path}: shapefile CRS is missing")
    if len(frame) == 0:
        raise ValueError(f"{shapefile_path}: shapefile contains no features")

    with rasterio.open(raster_path) as dataset:
        if dataset.crs is None:
            raise ValueError(f"{raster_path}: raster CRS is missing")
        try:
            linear_unit_name, linear_unit_to_metre = dataset.crs.linear_units_factor
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(
                f"{raster_path}: raster CRS does not expose a projected linear unit"
            ) from exc
        if (
            str(linear_unit_name).casefold() not in {"metre", "meter", "metres", "meters"}
            or not math.isclose(float(linear_unit_to_metre), 1.0, rel_tol=0, abs_tol=1e-12)
        ):
            raise ValueError(
                f"{raster_path}: this audit reports residuals in metres and requires "
                f"a metre-based projected CRS; found {linear_unit_name!r}"
            )
        if not same_crs(frame.crs, dataset.crs):
            raise ValueError(
                "Shapefile CRS is not nominally compatible with the raster CRS; "
                "no reprojection was attempted."
            )

        transform = dataset.transform
        feature_results: list[dict[str, Any]] = []
        all_center_residuals: list[float] = []
        all_corner_residuals: list[float] = []
        total_vertices = 0
        total_center_aligned = 0
        total_corner_aligned = 0

        inverse_transform = ~transform
        for feature_index, geometry in enumerate(frame.geometry):
            center_residuals: list[float] = []
            corner_residuals: list[float] = []
            for x, y in _iter_geometry_vertices(geometry):
                column, row = inverse_transform @ (x, y)
                _, _, center_error = _nearest_lattice_residual(
                    column, row, offset=0.5, transform=transform
                )
                _, _, corner_error = _nearest_lattice_residual(
                    column, row, offset=0.0, transform=transform
                )
                center_residuals.append(center_error)
                corner_residuals.append(corner_error)

            vertex_count = len(center_residuals)
            center_aligned_count = sum(
                residual <= tolerance_m for residual in center_residuals
            )
            corner_aligned_count = sum(
                residual <= tolerance_m for residual in corner_residuals
            )
            if vertex_count and center_aligned_count == vertex_count:
                alignment_class = "pixel_centres"
            elif vertex_count and corner_aligned_count == vertex_count:
                alignment_class = "pixel_corners"
            elif center_aligned_count or corner_aligned_count:
                alignment_class = "mixed_or_partial"
            else:
                alignment_class = "off_grid"

            feature_results.append(
                {
                    "feature_index": int(feature_index),
                    "geometry_type": (
                        str(geometry.geom_type) if geometry is not None else None
                    ),
                    "vertex_count": vertex_count,
                    "alignment_class": alignment_class,
                    "pixel_center_aligned_vertex_count": center_aligned_count,
                    "pixel_center_aligned_pct": (
                        100.0 * center_aligned_count / vertex_count
                        if vertex_count else None
                    ),
                    "pixel_corner_aligned_vertex_count": corner_aligned_count,
                    "pixel_corner_aligned_pct": (
                        100.0 * corner_aligned_count / vertex_count
                        if vertex_count else None
                    ),
                    "maximum_pixel_center_residual_m": (
                        max(center_residuals) if center_residuals else None
                    ),
                    "maximum_pixel_corner_residual_m": (
                        max(corner_residuals) if corner_residuals else None
                    ),
                }
            )
            total_vertices += vertex_count
            total_center_aligned += center_aligned_count
            total_corner_aligned += corner_aligned_count
            all_center_residuals.extend(center_residuals)
            all_corner_residuals.extend(corner_residuals)

        center_pct = (
            100.0 * total_center_aligned / total_vertices
            if total_vertices else None
        )
        corner_pct = (
            100.0 * total_corner_aligned / total_vertices
            if total_vertices else None
        )
        if total_vertices and total_center_aligned == total_vertices:
            overall_class = "pixel_centres"
        elif total_vertices and total_corner_aligned == total_vertices:
            overall_class = "pixel_corners"
        elif total_center_aligned or total_corner_aligned:
            overall_class = "mixed_or_partial"
        else:
            overall_class = "off_grid"

        tags = dataset.tags()
        report = {
            "schema_version": 1,
            "status": "inventory_complete",
            "shapefile": str(shapefile_path),
            "raster": str(raster_path),
            "crs_check": (
                "nominal CRS compatibility accepted; this does not identify "
                "an unknown lunar body-fixed frame"
            ),
            "raster_grid": {
                "width": int(dataset.width),
                "height": int(dataset.height),
                "transform": list(transform)[:6],
                "bounds": [
                    float(dataset.bounds.left),
                    float(dataset.bounds.bottom),
                    float(dataset.bounds.right),
                    float(dataset.bounds.top),
                ],
                "pixel_size_map_units": [
                    float(math.hypot(transform.a, transform.d)),
                    float(math.hypot(transform.b, transform.e)),
                ],
                "area_or_point": tags.get("AREA_OR_POINT"),
                "linear_units": str(linear_unit_name),
                "crs_wkt": dataset.crs.to_wkt(),
            },
            "tolerance_m": float(tolerance_m),
            "summary": {
                "feature_count": int(len(frame)),
                "vertex_count": total_vertices,
                "alignment_class": overall_class,
                "pixel_center_aligned_vertex_count": total_center_aligned,
                "pixel_center_aligned_pct": center_pct,
                "pixel_corner_aligned_vertex_count": total_corner_aligned,
                "pixel_corner_aligned_pct": corner_pct,
                "maximum_pixel_center_residual_m": (
                    max(all_center_residuals) if all_center_residuals else None
                ),
                "maximum_pixel_corner_residual_m": (
                    max(all_corner_residuals) if all_corner_residuals else None
                ),
            },
            "features": feature_results,
            "limitations": [
                "No reprojection, coordinate shift, geometry repair, rasterization, or source modification is performed.",
                "Pixel-lattice alignment is a geometric registration diagnostic; it does not prove the physical lunar datum or ME/PA frame.",
                "A pixel-centre result does not independently prove the ROI's scientific selection rule or illumination threshold.",
                "The affine transform is interpreted using pixel centres at (column + 0.5, row + 0.5) in its corner-based pixel coordinate system.",
                "The tolerance is a numerical comparison setting, not a scientific acceptance threshold.",
            ],
        }

    if total_vertices == 0:
        report["status"] = "review_required"
        report["warnings"] = ["No geometry vertices were available to audit."]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shapefile", type=Path, required=True)
    parser.add_argument("--raster", type=Path, required=True)
    parser.add_argument("--tolerance-m", type=float, default=1e-6)
    parser.add_argument("--output", type=Path, help="Optional JSON path; existing files are never overwritten.")
    args = parser.parse_args(argv)

    try:
        report = audit_shapefile_registration(
            args.shapefile,
            args.raster,
            tolerance_m=args.tolerance_m,
        )
        payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output is None:
            print(payload, end="")
        else:
            if args.output.exists():
                raise FileExistsError(
                    f"Refusing to overwrite existing report: {args.output}"
                )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
            print(f"Registration audit: {args.output}")
            print(json.dumps(report["summary"], indent=2))
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
