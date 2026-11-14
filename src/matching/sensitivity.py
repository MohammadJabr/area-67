
"""
Weight sensitivity analysis for AREA 67.

Tests how candidate rankings respond to reasonable
changes in mission feature weights.

Counts Top-K appearances; these counts are NOT probabilities.
"""

from collections.abc import Mapping
from math import isfinite

from src.matching.ranking import rank_candidates


def normalize_weights(weights: Mapping[str, float]) -> dict:
    """Normalize weights so that their sum equals 1."""

    if not weights:
        raise ValueError("Weights cannot be empty.")

    validated = {}

    for group, weight in weights.items():
        if (
            not isinstance(weight, (int, float))
            or not isfinite(weight)
            or weight < 0
        ):
            raise ValueError(f"Invalid weight for {group}.")

        validated[group] = float(weight)

    total = sum(validated.values())

    if total <= 0:
        raise ValueError("At least one weight must be positive.")

    return {
        group: weight / total
        for group, weight in validated.items()
    }


def build_weight_scenarios(
    base_weights: Mapping[str, float],
    relative_change: float = 0.20,
) -> dict:
    """
    Generate baseline and one-at-a-time weight scenarios.

    Each feature weight is reduced and increased independently,
    then all weights are renormalized.
    """

    if (
        not isinstance(relative_change, (int, float))
        or not isfinite(relative_change)
        or not 0 < relative_change < 1
    ):
        raise ValueError("relative_change must be between 0 and 1.")

    base = normalize_weights(base_weights)

    scenarios = {
        "baseline": base
    }

    for group, weight in base.items():

        for direction, factor in (
            ("down", 1 - relative_change),
            ("up", 1 + relative_change),
        ):
            modified = dict(base)
            modified[group] = weight * factor

            scenarios[f"{group}_{direction}"] = (
                normalize_weights(modified)
            )

    return scenarios


def run_weight_sensitivity(
    candidates: Mapping,
    base_weights: Mapping[str, float],
    *,
    target_site_id: str,
    relative_change: float = 0.20,
    top_k: tuple[int, ...] = (3, 5),
) -> dict:
    """
    Rank candidates under multiple weight scenarios.

    Reports how many scenarios each site appears in Top-K.
    """

    if not isinstance(target_site_id, str) or not target_site_id.strip():
        raise ValueError("target_site_id must be a non-empty string.")

    if not candidates:
        raise ValueError("At least one candidate is required.")

    if not top_k or any(
        not isinstance(k, int) or isinstance(k, bool) or k < 1
        for k in top_k
    ):
        raise ValueError("top_k must contain positive integers.")

    scenarios = build_weight_scenarios(
        base_weights,
        relative_change,
    )

    # A simple slope-only baseline helps reveal whether the full feature set
    # adds value beyond the most obvious terrain descriptor.
    slope_only_baseline = rank_candidates(
        candidates=candidates,
        weights={"slope": 1.0},
        target_site_id=target_site_id,
    )

    scenario_rankings = {};

    appearance_counts = {
        k: {site_id: 0 for site_id in candidates}
        for k in top_k
    }

    for scenario_name, weights in scenarios.items():

        result = rank_candidates(
            candidates=candidates,
            weights=weights,
            target_site_id=target_site_id,
        )

        ranking = result["ranking"]
        scenario_rankings[scenario_name] = ranking

        for k in top_k:
            for candidate in ranking[:k]:
                appearance_counts[k][candidate["site_id"]] += 1

    return {
        "target_site_id": target_site_id.strip(),
        "scenario_count": len(scenarios),
        "relative_change": relative_change,
        "scenario_rankings": scenario_rankings,
        "slope_only_baseline": slope_only_baseline,
        "top_k_counts": appearance_counts,
    }
