
"""
Mission profiles for AREA 67.

Initial weights are operational assumptions for the prototype.
They are NOT official NASA specifications.
"""

from math import isclose, isfinite


ROVER_NAVIGATION_PROFILE = {
    "name": "Rover Navigation / Terrain Traversal",
    "description": (
        "Terrain matching focused on rover traversal "
        "and navigation."
    ),

    "weights": {
        "slope": 0.30,
        "tri": 0.25,
        "local_relief": 0.20,
        "spatial_pattern": 0.20,
        "terrain_distribution": 0.05,
    },
}


def validate_weights(weights: dict) -> None:
    """Validate mission weights and ensure they sum to 1."""

    if not weights:
        raise ValueError("Mission weights cannot be empty.")

    for group, weight in weights.items():

        if not isinstance(weight, (int, float)):
            raise ValueError(f"Invalid weight for {group}.")

        if not isfinite(weight) or weight < 0:
            raise ValueError(f"Invalid weight for {group}.")

    total = sum(weights.values())

    if not isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError(
            f"Weights must sum to 1. Current sum: {total}"
        )


def get_mission_weights() -> dict:
    """Return a validated copy of the Rover Navigation weights."""

    weights = dict(ROVER_NAVIGATION_PROFILE["weights"])
    validate_weights(weights)

    return weights
