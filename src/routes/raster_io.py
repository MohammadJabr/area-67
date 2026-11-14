"""Read aligned elevation, slope, and TRI rasters for the A* route planner."""

from __future__ import annotations

import math
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import rasterio
from pyproj import CRS


def _elevation_factor_to_meters(unit: str) -> float:
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("An explicit elevation/TRI unit is required.")
    key = unit.strip().lower()
    factors = {
        "m": 1.0,
        "meter": 1.0,
        "meters": 1.0,
        "metre": 1.0,
        "metres": 1.0,
        "cm": 0.01,
        "mm": 0.001,
        "ft": 0.3048,
        "feet": 0.3048,
    }
    if key not in factors:
        raise ValueError(f"Unsupported elevation unit: {unit!r}.")
    return factors[key]


def _slope_factor_to_degrees(unit: str) -> float:
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("An explicit slope unit is required.")
    key = unit.strip().lower()
    if key in {"degree", "degrees", "deg"}:
        return 1.0
    if key in {"radian", "radians", "rad"}:
        return 180.0 / math.pi
    raise ValueError(f"Unsupported slope unit: {unit!r}.")


def _validate_projected_meter_grid(dataset, name: str) -> tuple[float, float, float, float]:
    if dataset.crs is None:
        raise ValueError(f"{name} raster has no CRS.")
    crs = CRS.from_user_input(dataset.crs)
    if not crs.is_projected:
        raise ValueError(f"{name} raster must use a projected CRS, not geographic degrees.")

    if not crs.axis_info:
        raise ValueError(f"{name} raster CRS does not declare linear coordinate units.")
    unit_factor = crs.axis_info[0].unit_conversion_factor
    if unit_factor is None or not math.isfinite(unit_factor) or unit_factor <= 0:
        raise ValueError(f"{name} raster CRS has an unsupported linear unit.")

    transform = dataset.transform
    column_vector = (transform.a, transform.d)
    row_vector = (transform.b, transform.e)
    column_size_native = math.hypot(*column_vector)
    row_size_native = math.hypot(*row_vector)
    if column_size_native <= 0 or row_size_native <= 0:
        raise ValueError(f"{name} raster has an invalid affine pixel basis.")

    # A* assumes perpendicular row/column directions and square cells. Equal
    # basis-vector lengths alone do not prove orthogonality (a sheared grid can
    # have equal lengths while diagonal movement is not sqrt(2) cell widths).
    dot_product = (
        column_vector[0] * row_vector[0]
        + column_vector[1] * row_vector[1]
    )
    normalized_dot = abs(dot_product) / (column_size_native * row_size_native)
    if normalized_dot > 1e-9:
        raise ValueError(
            f"{name} raster affine grid is not orthogonal "
            f"(normalized row/column dot product={normalized_dot:.3g})."
        )

    pixel_x_m = column_size_native * unit_factor
    pixel_y_m = row_size_native * unit_factor
    if not math.isclose(pixel_x_m, pixel_y_m, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(
            f"{name} raster pixels are not square in metres: "
            f"x={pixel_x_m}, y={pixel_y_m}."
        )
    if pixel_x_m <= 0:
        raise ValueError(f"{name} raster has an invalid pixel size.")
    return pixel_x_m, unit_factor, pixel_y_m, normalized_dot


def load_aligned_route_rasters(
    elevation_path: str | Path,
    slope_path: str | Path,
    tri_path: str | Path,
    *,
    elevation_unit: str,
    slope_unit: str,
    tri_unit: str,
    max_grid_cells: int = 250_000,
) -> dict:
    """Load three single-band rasters that share an identical projected grid.

    Invalid and NoData pixels are represented by NaN and a combined valid_mask.
    Horizontal pixel size is converted from the projected CRS linear unit to
    metres. Elevation and TRI are converted to metres; slope is converted to
    degrees. Vertical/elevation units must be supplied explicitly.
    """
    if (
        isinstance(max_grid_cells, bool)
        or not isinstance(max_grid_cells, int)
        or max_grid_cells < 1
    ):
        raise ValueError("max_grid_cells must be a positive integer.")

    paths = {
        "elevation": Path(elevation_path),
        "slope": Path(slope_path),
        "tri": Path(tri_path),
    }
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"{name} raster not found: {path}")

    elevation_factor = _elevation_factor_to_meters(elevation_unit)
    tri_factor = _elevation_factor_to_meters(tri_unit)
    slope_factor = _slope_factor_to_degrees(slope_unit)

    with ExitStack() as stack:
        datasets = {
            name: stack.enter_context(rasterio.open(path))
            for name, path in paths.items()
        }

        reference = datasets["elevation"]
        if reference.count != 1:
            raise ValueError("Elevation raster must contain exactly one band.")
        reference_crs = reference.crs
        reference_transform = reference.transform
        reference_shape = (reference.height, reference.width)

        cell_size_m, crs_unit_factor, pixel_y_m, normalized_dot = (
            _validate_projected_meter_grid(reference, "Elevation")
        )
        pixel_x_m = cell_size_m

        arrays = {}
        masks = {}
        for name, dataset in datasets.items():
            if dataset.count != 1:
                raise ValueError(f"{name.capitalize()} raster must contain exactly one band.")
            if dataset.crs != reference_crs:
                raise ValueError(f"{name.capitalize()} raster CRS does not match elevation CRS.")
            if dataset.transform != reference_transform:
                raise ValueError(
                    f"{name.capitalize()} raster transform does not match elevation transform."
                )
            if (dataset.height, dataset.width) != reference_shape:
                raise ValueError(
                    f"{name.capitalize()} raster dimensions do not match elevation raster."
                )

        cell_count = reference_shape[0] * reference_shape[1]
        if cell_count > max_grid_cells:
            raise ValueError(
                f"Route grid has {cell_count:,} cells, exceeding max_grid_cells="
                f"{max_grid_cells:,}. Crop to an approved ROI or raise the limit "
                "only after benchmarking the intended environment."
            )

        for name, dataset in datasets.items():
            values = dataset.read(1).astype("float64", copy=False)
            mask = (dataset.read_masks(1) > 0) & np.isfinite(values)
            arrays[name] = values
            masks[name] = mask

        valid_mask = masks["elevation"] & masks["slope"] & masks["tri"]
        if not valid_mask.any():
            raise ValueError("Aligned route rasters have no common valid cells.")

        elevation_m = arrays["elevation"] * elevation_factor
        slope_deg = arrays["slope"] * slope_factor
        tri_m = arrays["tri"] * tri_factor

        elevation_m = np.where(valid_mask, elevation_m, np.nan)
        slope_deg = np.where(valid_mask, slope_deg, np.nan)
        tri_m = np.where(valid_mask, tri_m, np.nan)

        # Float32 rasters can represent pi/2 radians with a tiny rounding
        # error, which may convert to a value such as 90.000002 degrees.
        # Accept only this small numerical tolerance and clamp to physical
        # endpoints; genuinely invalid slope values are still rejected.
        slope_numeric_tolerance_deg = 1e-4
        if np.any(
            valid_mask
            & (
                (slope_deg < -slope_numeric_tolerance_deg)
                | (slope_deg > 90.0 + slope_numeric_tolerance_deg)
            )
        ):
            raise ValueError("Slope raster contains values outside 0–90 degrees.")
        slope_deg = np.where(
            valid_mask,
            np.clip(slope_deg, 0.0, 90.0),
            np.nan,
        )
        if np.any(valid_mask & (tri_m < 0)):
            raise ValueError("TRI raster contains negative values.")

        return {
            "elevation_m": elevation_m,
            "slope_deg": slope_deg,
            "tri_m": tri_m,
            "valid_mask": valid_mask,
            "grid_metadata": {
                "width_pixels": reference.width,
                "height_pixels": reference.height,
                "crs": reference_crs.to_string(),
                "transform": tuple(reference_transform)[:6],
                "cell_size_m": cell_size_m,
                "column_pixel_size_m": pixel_x_m,
                "row_pixel_size_m": pixel_y_m,
                "affine_grid_orthogonality_error": normalized_dot,
                "crs_linear_unit_to_metre_factor": crs_unit_factor,
                "bounds_native_crs_units": tuple(reference.bounds),
                "source_paths": {
                    name: str(path) for name, path in paths.items()
                },
            },
        }
