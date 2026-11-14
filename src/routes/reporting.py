"""Export a rover route cell/profile CSV with optional native-CRS coordinates."""

from __future__ import annotations

import csv
from pathlib import Path

from affine import Affine
from rasterio.transform import xy


def export_route_profile_csv(
    route_result: dict,
    output_path: str | Path,
    *,
    transform: tuple | None = None,
    crs: str | None = None,
) -> Path:
    """Write row/column, optional map coordinates, and terrain profiles."""
    required = (
        "path_cells",
        "elevation_profile_m",
        "slope_profile_deg",
        "tri_profile_m",
        "step_costs_m",
        "cumulative_cost_m",
    )
    missing = [key for key in required if key not in route_result]
    if missing:
        raise ValueError("Route result is missing fields: " + ", ".join(missing))

    path_cells = route_result["path_cells"]
    lengths = [
        len(route_result[key])
        for key in (
            "elevation_profile_m",
            "slope_profile_deg",
            "tri_profile_m",
            "step_costs_m",
            "cumulative_cost_m",
        )
    ]
    if not path_cells or any(length != len(path_cells) for length in lengths):
        raise ValueError("Route path and terrain/cost profiles must have equal non-zero lengths.")

    affine_transform = Affine(*transform) if transform is not None else None
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "step",
        "row",
        "column",
        "map_x",
        "map_y",
        "crs",
        "elevation_m",
        "slope_deg",
        "tri_m",
        "step_cost_m",
        "cumulative_cost_m",
        "total_route_cost_m",
        "path_length_m",
        "route_model",
        "assumptions",
    ]

    assumptions = "; ".join(route_result.get("assumptions", []))
    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for index, (row, column) in enumerate(path_cells):
            if affine_transform is not None:
                map_x, map_y = xy(
                    affine_transform,
                    row,
                    column,
                    offset="center",
                )
            else:
                map_x, map_y = "", ""

            writer.writerow({
                "step": index,
                "row": row,
                "column": column,
                "map_x": map_x,
                "map_y": map_y,
                "crs": crs or "",
                "elevation_m": route_result["elevation_profile_m"][index],
                "slope_deg": route_result["slope_profile_deg"][index],
                "tri_m": route_result["tri_profile_m"][index],
                "step_cost_m": route_result["step_costs_m"][index],
                "cumulative_cost_m": route_result["cumulative_cost_m"][index],
                "total_route_cost_m": route_result["total_cost_m"],
                "path_length_m": route_result["path_length_m"],
                "route_model": route_result["route_model"],
                "assumptions": assumptions,
            })

    return output
