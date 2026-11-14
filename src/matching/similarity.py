
"""
Weighted terrain similarity calculations for AREA 67.

This module combines already-computed, non-negative group distances.
It does NOT calculate raw terrain features or normalize raw measurements.
"""

from collections.abc import Mapping
from math import isfinite, sqrt


def weighted_similarity_distance(
    group_distances: Mapping[str, float | None],
    weights: Mapping[str, float],
    min_completeness: float = 0.0,
) -> dict:
    """
    Calculate weighted distance between a target and one candidate.

    Missing groups are excluded, and the remaining weights are
    renormalized. Data completeness is reported explicitly.

    Each group distance must already be computed and be non-negative.
    """

    if not weights:
        raise ValueError("At least one group weight is required.")

    if not isfinite(min_completeness) or not 0 <= min_completeness <= 1:
        raise ValueError("min_completeness must be between 0 and 1.")

    total_weight = 0.0

    for group, weight in weights.items():
        if not isinstance(weight, (int, float)) or not isfinite(weight):
            raise ValueError(f"Invalid weight for {group}.")

        if weight < 0:
            raise ValueError(f"Weight for {group} cannot be negative.")

        total_weight += weight

    if total_weight <= 0:
        raise ValueError("The sum of weights must be greater than zero.")

    available = {}
    missing_groups = []
    zero_weight_groups = []

    for group, weight in weights.items():
        value = group_distances.get(group)

        if value is None:
            missing_groups.append(group)
            continue

        if not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"Invalid distance for {group}.")

        if value < 0:
            raise ValueError(f"Distance for {group} cannot be negative.")

        if weight == 0:
            zero_weight_groups.append(group)
            continue

        available[group] = (float(value), float(weight))

    active_weight = sum(weight for _, weight in available.values())

    if active_weight <= 0:
        raise ValueError("No valid groups with positive weights.")

    completeness = active_weight / total_weight

    if completeness < min_completeness:
        raise ValueError(
            f"Data completeness {completeness:.2%} is below "
            f"the required minimum {min_completeness:.2%}."
        )

    weighted_terms = {
        group: weight * distance**2
        for group, (distance, weight) in available.items()
    }

    total_squared_distance = sum(weighted_terms.values())

    distance = sqrt(total_squared_distance / active_weight)

    contributions = {}

    for group, (group_distance, weight) in available.items():
        term = weighted_terms[group]

        contributions[group] = {
            "group_distance": group_distance,
            "weight": weight,
            "weighted_squared_contribution": term / active_weight,
            "distance_share": (
                term / total_squared_distance
                if total_squared_distance > 0
                else 0.0
            ),
        }

    return {
        "similarity_distance": distance,
        "data_completeness": completeness,
        "used_groups": list(available.keys()),
        "missing_groups": missing_groups,
        "zero_weight_groups": zero_weight_groups,
        "group_contributions": contributions,
    }
