import math
import pytest

from src.matching.normalization import standardized_rms_distance


def test_identical_vectors_have_zero_distance():
    assert standardized_rms_distance([10, 20], [10, 20], 5) == 0.0


def test_tolerance_scaled_rms_distance():
    assert math.isclose(
        standardized_rms_distance([10, 20], [15, 25], 5),
        1.0,
    )


@pytest.mark.parametrize("tolerance", [0, -1, float("nan"), float("inf")])
def test_invalid_tolerance_is_rejected(tolerance):
    with pytest.raises(ValueError):
        standardized_rms_distance([1], [2], tolerance)


def test_mismatched_or_empty_vectors_are_rejected():
    with pytest.raises(ValueError):
        standardized_rms_distance([1, 2], [1], 1)
    with pytest.raises(ValueError):
        standardized_rms_distance([], [], 1)
