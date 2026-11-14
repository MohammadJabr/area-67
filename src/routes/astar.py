"""A* least-cost routing on a small, aligned rover-terrain grid.

This is a hypothetical DEM cost model, not rover-safety certification.
All distance terms are in metres. Feature normalization scales must be
explicitly chosen and documented for the study.
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Sequence

import numpy as np


Cell = tuple[int, int]


def _as_grid(values, name: str) -> np.ndarray:
    grid = np.asarray(values, dtype=float)
    if grid.ndim != 2 or grid.size == 0:
        raise ValueError(f"{name} must be a non-empty two-dimensional grid.")
    return grid


def _check_positive_finite(value, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a finite number greater than zero.")
    return float(value)


def _check_non_negative_finite(value, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"{name} must be a finite, non-negative number.")
    return float(value)


def _validate_cell(cell: Sequence[int], name: str, shape: tuple[int, int]) -> Cell:
    if (
        not isinstance(cell, (tuple, list))
        or len(cell) != 2
        or any(isinstance(value, bool) or not isinstance(value, (int, np.integer)) for value in cell)
    ):
        raise ValueError(f"{name} must be a (row, column) integer pair.")

    row, column = int(cell[0]), int(cell[1])
    if not (0 <= row < shape[0] and 0 <= column < shape[1]):
        raise ValueError(f"{name} {cell!r} is outside grid bounds {shape}.")
    return row, column


def _heuristic(cell: Cell, goal: Cell, cell_size_m: float) -> float:
    """Euclidean lower bound; the base movement multiplier is at least one."""
    row_delta = goal[0] - cell[0]
    column_delta = goal[1] - cell[1]
    return cell_size_m * math.hypot(row_delta, column_delta)


def plan_rover_route(
    elevation_m,
    slope_deg,
    tri_m,
    start: Cell,
    goal: Cell,
    *,
    cell_size_m: float,
    slope_scale_deg: float,
    tri_scale_m: float,
    alpha: float = 1.0,
    beta: float = 1.0,
    valid_mask=None,
    blocked_mask=None,
    penalty=None,
    connectivity: int = 8,
    max_grid_cells: int = 250_000,
) -> dict:
    """Find a least-cost path over an aligned DEM-derived grid using A*.

    Step-cost model:
        step_cost = distance_m * (
            1 + alpha * slope_norm + beta * tri_norm + penalty_norm
        )

    slope_norm and tri_norm are the mean of the normalized values at the two
    cells being traversed. penalty_norm is the mean of an optional non-negative
    dimensionless penalty grid at those cells.

    Invalid/NoData and blocked cells are excluded. Diagonal moves are forbidden
    from cutting across blocked/invalid corners. With non-negative feature
    penalties, Euclidean distance is an admissible heuristic.

    slope_scale_deg and tri_scale_m are explicit operational scales, not
    NASA or rover-manufacturer limits. max_grid_cells is a software memory/
    performance guard, not a science or vehicle threshold.
    """
    elevation = _as_grid(elevation_m, "elevation_m")
    slope = _as_grid(slope_deg, "slope_deg")
    tri = _as_grid(tri_m, "tri_m")
    shape = elevation.shape

    if slope.shape != shape or tri.shape != shape:
        raise ValueError("Elevation, slope, and TRI grids must have identical shapes.")
    if (
        isinstance(max_grid_cells, bool)
        or not isinstance(max_grid_cells, int)
        or max_grid_cells < 1
    ):
        raise ValueError("max_grid_cells must be a positive integer.")
    cell_count = shape[0] * shape[1]
    if cell_count > max_grid_cells:
        raise ValueError(
            f"Route grid has {cell_count:,} cells, exceeding max_grid_cells="
            f"{max_grid_cells:,}. Crop to an approved ROI or raise the limit "
            "only after benchmarking the intended environment."
        )

    cell_size_m = _check_positive_finite(cell_size_m, "cell_size_m")
    slope_scale_deg = _check_positive_finite(slope_scale_deg, "slope_scale_deg")
    tri_scale_m = _check_positive_finite(tri_scale_m, "tri_scale_m")
    alpha = _check_non_negative_finite(alpha, "alpha")
    beta = _check_non_negative_finite(beta, "beta")

    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8.")

    valid = np.isfinite(elevation) & np.isfinite(slope) & np.isfinite(tri)
    if valid_mask is not None:
        mask = np.asarray(valid_mask, dtype=bool)
        if mask.shape != shape:
            raise ValueError("valid_mask must have the same shape as the terrain grids.")
        valid &= mask

    if blocked_mask is not None:
        blocked = np.asarray(blocked_mask, dtype=bool)
        if blocked.shape != shape:
            raise ValueError("blocked_mask must have the same shape as the terrain grids.")
        valid &= ~blocked

    if np.any(valid & ((slope < 0) | (slope > 90))):
        raise ValueError("Valid slope values must be between 0 and 90 degrees.")
    if np.any(valid & (tri < 0)):
        raise ValueError("Valid TRI values must be non-negative.")

    penalty_grid = np.zeros(shape, dtype=float) if penalty is None else _as_grid(
        penalty, "penalty"
    )
    if penalty_grid.shape != shape:
        raise ValueError("penalty must have the same shape as the terrain grids.")
    if not np.isfinite(penalty_grid[valid]).all() or np.any(penalty_grid[valid] < 0):
        raise ValueError("Penalty values on valid cells must be finite and non-negative.")

    start_cell = _validate_cell(start, "start", shape)
    goal_cell = _validate_cell(goal, "goal", shape)

    if not valid[start_cell]:
        raise ValueError("Start cell is invalid, NoData, or blocked.")
    if not valid[goal_cell]:
        raise ValueError("Goal cell is invalid, NoData, or blocked.")
    if start_cell == goal_cell:
        return {
            "status": "success",
            "path_cells": [start_cell],
            "total_cost_m": 0.0,
            "path_length_m": 0.0,
            "step_costs_m": [0.0],
            "cumulative_cost_m": [0.0],
            "elevation_profile_m": [float(elevation[start_cell])],
            "slope_profile_deg": [float(slope[start_cell])],
            "tri_profile_m": [float(tri[start_cell])],
            "route_model": "A* with Euclidean heuristic and normalized slope/TRI penalties",
            "assumptions": [
                "This is a hypothetical DEM least-cost path, not a rover-safety certification.",
                "The supplied feature scales and alpha/beta weights are operational assumptions.",
            ],
        }

    if connectivity == 4:
        neighbor_offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))
    else:
        neighbor_offsets = (
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        )

    g_score = np.full(shape, np.inf, dtype=float)
    g_score[start_cell] = 0.0
    came_from: dict[Cell, Cell] = {}

    open_heap: list[tuple[float, float, Cell]] = []
    heapq.heappush(
        open_heap,
        (_heuristic(start_cell, goal_cell, cell_size_m), 0.0, start_cell),
    )
    closed: set[Cell] = set()

    while open_heap:
        _, queued_g, current = heapq.heappop(open_heap)

        if current in closed or queued_g > g_score[current]:
            continue

        if current == goal_cell:
            break

        closed.add(current)
        current_row, current_column = current

        for row_offset, column_offset in neighbor_offsets:
            neighbor = (
                current_row + row_offset,
                current_column + column_offset,
            )

            if not (
                0 <= neighbor[0] < shape[0]
                and 0 <= neighbor[1] < shape[1]
                and valid[neighbor]
            ):
                continue

            is_diagonal = row_offset != 0 and column_offset != 0
            if is_diagonal:
                # Do not squeeze diagonally between two blocked/NoData cells.
                orthogonal_a = (current_row + row_offset, current_column)
                orthogonal_b = (current_row, current_column + column_offset)
                if not (valid[orthogonal_a] and valid[orthogonal_b]):
                    continue

            distance_m = cell_size_m * (
                math.sqrt(2.0) if is_diagonal else 1.0
            )

            slope_norm = (
                (slope[current] + slope[neighbor]) / 2.0
            ) / slope_scale_deg
            tri_norm = (
                (tri[current] + tri[neighbor]) / 2.0
            ) / tri_scale_m
            penalty_norm = (
                penalty_grid[current] + penalty_grid[neighbor]
            ) / 2.0

            step_cost = distance_m * (
                1.0
                + alpha * slope_norm
                + beta * tri_norm
                + penalty_norm
            )
            tentative_g = g_score[current] + step_cost

            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                priority = tentative_g + _heuristic(
                    neighbor, goal_cell, cell_size_m
                )
                heapq.heappush(
                    open_heap,
                    (priority, tentative_g, neighbor),
                )

    if not np.isfinite(g_score[goal_cell]):
        raise ValueError("No valid route exists between start and goal.")

    path = [goal_cell]
    while path[-1] != start_cell:
        previous = came_from.get(path[-1])
        if previous is None:
            raise RuntimeError("A* reached the goal but the predecessor chain is incomplete.")
        path.append(previous)
    path.reverse()

    step_costs = [0.0]
    step_lengths = [0.0]
    for previous, current in zip(path, path[1:]):
        row_delta = current[0] - previous[0]
        column_delta = current[1] - previous[1]
        diagonal = row_delta != 0 and column_delta != 0
        length = cell_size_m * (math.sqrt(2.0) if diagonal else 1.0)

        slope_norm = (slope[previous] + slope[current]) / (2.0 * slope_scale_deg)
        tri_norm = (tri[previous] + tri[current]) / (2.0 * tri_scale_m)
        penalty_norm = (penalty_grid[previous] + penalty_grid[current]) / 2.0
        cost = length * (
            1.0 + alpha * slope_norm + beta * tri_norm + penalty_norm
        )
        step_lengths.append(length)
        step_costs.append(float(cost))

    cumulative_cost = np.cumsum(step_costs).tolist()

    return {
        "status": "success",
        "path_cells": path,
        "total_cost_m": float(g_score[goal_cell]),
        "path_length_m": float(sum(step_lengths)),
        "step_costs_m": step_costs,
        "cumulative_cost_m": [float(value) for value in cumulative_cost],
        "elevation_profile_m": [float(elevation[cell]) for cell in path],
        "slope_profile_deg": [float(slope[cell]) for cell in path],
        "tri_profile_m": [float(tri[cell]) for cell in path],
        "route_model": "A* with Euclidean heuristic and normalized slope/TRI penalties",
        "assumptions": [
            "This is a hypothetical DEM least-cost path, not a rover-safety certification.",
            "Slope and TRI are averaged across each traversed cell pair.",
            "Invalid/NoData and blocked cells are excluded; diagonal corner-cutting is disabled.",
            "Feature scales, alpha/beta weights, and optional penalties are operational assumptions.",
        ],
    }
