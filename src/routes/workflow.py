"""End-to-end A* route workflow from aligned elevation/slope/TRI rasters."""

from __future__ import annotations

from pathlib import Path

from src.routes.astar import plan_rover_route
from src.routes.raster_io import load_aligned_route_rasters
from src.routes.reporting import (
    export_route_metadata_json,
    export_route_profile_csv,
)


def plan_route_from_rasters(
    elevation_path: str | Path,
    slope_path: str | Path,
    tri_path: str | Path,
    start: tuple[int, int],
    goal: tuple[int, int],
    *,
    elevation_unit: str,
    slope_unit: str,
    tri_unit: str,
    slope_scale_deg: float,
    tri_scale_m: float,
    alpha: float = 1.0,
    beta: float = 1.0,
    connectivity: int = 8,
    blocked_mask=None,
    penalty=None,
    output_path: str | Path = "data/processed/rover_route.csv",
    metadata_output_path: str | Path = "data/processed/rover_route_metadata.json",
    max_grid_cells: int = 250_000,
) -> dict:
    """Load compatible raster layers, plan A*, and export a route profile CSV.

    The raster inputs must share one projected, square-pixel grid. The supplied
    normalization scales and weights are explicit operating assumptions.
    """
    grids = load_aligned_route_rasters(
        elevation_path,
        slope_path,
        tri_path,
        elevation_unit=elevation_unit,
        slope_unit=slope_unit,
        tri_unit=tri_unit,
        max_grid_cells=max_grid_cells,
    )

    route = plan_rover_route(
        grids["elevation_m"],
        grids["slope_deg"],
        grids["tri_m"],
        start,
        goal,
        cell_size_m=grids["grid_metadata"]["cell_size_m"],
        slope_scale_deg=slope_scale_deg,
        tri_scale_m=tri_scale_m,
        alpha=alpha,
        beta=beta,
        valid_mask=grids["valid_mask"],
        blocked_mask=blocked_mask,
        penalty=penalty,
        connectivity=connectivity,
        max_grid_cells=max_grid_cells,
    )

    route_csv = export_route_profile_csv(
        route,
        output_path,
        transform=grids["grid_metadata"]["transform"],
        crs=grids["grid_metadata"]["crs"],
    )

    route_metadata = export_route_metadata_json(
        route,
        metadata_output_path,
        elevation_path=elevation_path,
        slope_path=slope_path,
        tri_path=tri_path,
        parameters={
            "start_cell": list(start),
            "goal_cell": list(goal),
            "elevation_unit": elevation_unit,
            "slope_unit": slope_unit,
            "tri_unit": tri_unit,
            "slope_scale_deg": slope_scale_deg,
            "tri_scale_m": tri_scale_m,
            "alpha": alpha,
            "beta": beta,
            "connectivity": connectivity,
            "max_grid_cells": max_grid_cells,
        },
        grid_metadata=grids["grid_metadata"],
        blocked_mask=blocked_mask,
        penalty=penalty,
    )

    return {
        "route": route,
        "route_csv": route_csv,
        "route_metadata_json": route_metadata,
        "grid_metadata": grids["grid_metadata"],
    }
