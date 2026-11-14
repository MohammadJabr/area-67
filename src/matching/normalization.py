"""Tolerance-based normalization for heterogeneous terrain descriptors.

Distances are expressed in units of explicitly declared tolerances. They are
not probabilities and are not bounded to [0, 1].
"""

from collections.abc import Iterable
from math import isfinite, sqrt


def standardized_rms_distance(
    target_values: Iterable[float],
    candidate_values: Iterable[float],
    tolerance: float,
) -> float:
    """Return RMS absolute difference divided by a physical tolerance.

    Both value sequences must describe the same ordered metrics and use the
    same units. The tolerance must be in those units and strictly positive.
    """
    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not isfinite(tolerance)
        or tolerance <= 0
    ):
        raise ValueError("tolerance must be a finite number greater than zero.")

    target = list(target_values)
    candidate = list(candidate_values)

    if not target or len(target) != len(candidate):
        raise ValueError("Target and candidate values must be non-empty and equal in length.")

    squared = []
    for index, (target_value, candidate_value) in enumerate(zip(target, candidate)):
        for label, value in (("target", target_value), ("candidate", candidate_value)):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
            ):
                raise ValueError(f"{label} value at position {index} must be finite and numeric.")

        standardized_difference = (float(target_value) - float(candidate_value)) / float(tolerance)
        squared.append(standardized_difference ** 2)

    return sqrt(sum(squared) / len(squared))
