import math

import numpy as np
import pytest

from src.routes.astar import plan_rover_route


def _flat_grids(rows=3, columns=3):
    elevation = np.full((rows, columns), 100.0)
    slope = np.zeros((rows, columns))
    tri = np.zeros((rows, columns))
    return elevation, slope, tri


def test_flat_terrain_uses_direct_diagonal_path():
    elevation, slope, tri = _flat_grids()

    result = plan_rover_route(
        elevation,
        slope,
        tri,
        (0, 0),
        (2, 2),
        cell_size_m=10,
        slope_scale_deg=10,
        tri_scale_m=5,
        connectivity=8,
    )

    assert result["path_cells"] == [(0, 0), (1, 1), (2, 2)]
    assert math.isclose(result["path_length_m"], 20 * math.sqrt(2))
    assert math.isclose(result["total_cost_m"], result["path_length_m"])
    assert len(result["elevation_profile_m"]) == len(result["path_cells"])


def test_blocked_cells_are_never_used():
    elevation, slope, tri = _flat_grids(3, 3)
    blocked = np.zeros((3, 3), dtype=bool)
    blocked[1, 1] = True

    result = plan_rover_route(
        elevation,
        slope,
        tri,
        (1, 0),
        (1, 2),
        cell_size_m=5,
        slope_scale_deg=10,
        tri_scale_m=5,
        blocked_mask=blocked,
        connectivity=4,
    )

    assert (1, 1) not in result["path_cells"]
    assert result["path_length_m"] == 20.0


def test_a_star_avoids_a_high_slope_cell_when_a_lower_cost_detour_exists():
    elevation, slope, tri = _flat_grids(3, 3)
    slope[1, 1] = 80.0

    result = plan_rover_route(
        elevation,
        slope,
        tri,
        (1, 0),
        (1, 2),
        cell_size_m=10,
        slope_scale_deg=10,
        tri_scale_m=5,
        alpha=1,
        beta=0,
        connectivity=8,
    )

    assert (1, 1) not in result["path_cells"]
    assert result["total_cost_m"] < 100.0


def test_no_data_and_invalid_cells_are_excluded():
    elevation, slope, tri = _flat_grids()
    elevation[1, 1] = np.nan
    valid = np.ones((3, 3), dtype=bool)

    result = plan_rover_route(
        elevation,
        slope,
        tri,
        (0, 0),
        (2, 2),
        cell_size_m=10,
        slope_scale_deg=10,
        tri_scale_m=5,
        valid_mask=valid,
        connectivity=4,
    )

    assert (1, 1) not in result["path_cells"]


def test_no_path_raises_instead_of_crossing_a_blocked_barrier():
    elevation, slope, tri = _flat_grids(3, 3)
    blocked = np.zeros((3, 3), dtype=bool)
    blocked[1, :] = True

    with pytest.raises(ValueError, match="No valid route"):
        plan_rover_route(
            elevation,
            slope,
            tri,
            (0, 0),
            (2, 2),
            cell_size_m=10,
            slope_scale_deg=10,
            tri_scale_m=5,
            blocked_mask=blocked,
            connectivity=8,
        )


def test_start_on_no_data_is_rejected():
    elevation, slope, tri = _flat_grids()
    valid = np.ones((3, 3), dtype=bool)
    valid[0, 0] = False

    with pytest.raises(ValueError, match="Start cell is invalid"):
        plan_rover_route(
            elevation,
            slope,
            tri,
            (0, 0),
            (2, 2),
            cell_size_m=10,
            slope_scale_deg=10,
            tri_scale_m=5,
            valid_mask=valid,
        )


def test_diagonal_corner_cutting_is_forbidden():
    elevation, slope, tri = _flat_grids(2, 2)
    blocked = np.array([
        [False, True],
        [True, False],
    ])

    with pytest.raises(ValueError, match="No valid route"):
        plan_rover_route(
            elevation,
            slope,
            tri,
            (0, 0),
            (1, 1),
            cell_size_m=10,
            slope_scale_deg=10,
            tri_scale_m=5,
            blocked_mask=blocked,
            connectivity=8,
        )


def test_invalid_scale_and_connectivity_are_rejected():
    elevation, slope, tri = _flat_grids()

    with pytest.raises(ValueError, match="cell_size_m"):
        plan_rover_route(
            elevation,
            slope,
            tri,
            (0, 0),
            (2, 2),
            cell_size_m=0,
            slope_scale_deg=10,
            tri_scale_m=5,
        )

    with pytest.raises(ValueError, match="connectivity"):
        plan_rover_route(
            elevation,
            slope,
            tri,
            (0, 0),
            (2, 2),
            cell_size_m=10,
            slope_scale_deg=10,
            tri_scale_m=5,
            connectivity=6,
        )
