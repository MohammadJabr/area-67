"""
Weight sensitivity analysis for AREA 67.

One-at-a-time weight perturbations are descriptive robustness checks.
Top-K appearance counts are not probabilities.
"""

from collections.abc import Mapping
from math import isfinite

from src.matching.ranking import rank_candidates


def normalize_weights(weights: Mapping[str, float]) -> dict:
    """Normalize finite non-negative weights so their sum equals one."""
    if not isinstance(weights, Mapping) or not weights:
        raise ValueError("Weights cannot be empty.")

    validated = {}
    for group, weight in weights.items():
        if (
            isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not isfinite(weight)
            or weight < 0
        ):
            raise ValueError(f"Invalid weight for {group}.")
        validated[group] = float(weight)

    total = sum(validated.values())
    if total <= 0:
        raise ValueError("At least one weight must be positive.")

    return {group: weight / total for group, weight in validated.items()}


def build_weight_scenarios(
    base_weights: Mapping[str, float],
    relative_change: float = 0.20,
) -> dict:
    """Generate baseline and one-at-a-time down/up scenarios."""
    if (
        isinstance(relative_change, bool)
        or not isinstance(relative_change, (int, float))
        or not isfinite(relative_change)
        or not 0 < relative_change < 1
    ):
        raise ValueError("relative_change must be between 0 and 1.")

    base = normalize_weights(base_weights)
    scenarios = {"baseline": base}

    for group, weight in base.items():
        for direction, factor in (
            ("down", 1 - relative_change),
            ("up", 1 + relative_change),
        ):
            modified = dict(base)
            modified[group] = weight * factor
            scenarios[f"{group}_{direction}"] = normalize_weights(modified)

    return scenarios


def run_weight_sensitivity(
    candidates: Mapping,
    base_weights: Mapping[str, float],
    *,
    target_site_id: str,
    relative_change: float = 0.20,
    top_k: tuple[int, ...] = (3, 5),
    min_completeness: float = 0.0,
) -> dict:
    """Run weight perturbations and a Slope-only baseline on group distances."""
    if not isinstance(target_site_id, str) or not target_site_id.strip():
        raise ValueError("target_site_id must be a non-empty string.")
    if not isinstance(candidates, Mapping) or not candidates:
        raise ValueError("At least one candidate is required.")
    if not top_k or any(
        not isinstance(k, int) or isinstance(k, bool) or k < 1
        for k in top_k
    ):
        raise ValueError("top_k must contain positive integers.")
    if (
        isinstance(min_completeness, bool)
        or not isinstance(min_completeness, (int, float))
        or not isfinite(min_completeness)
        or not 0 <= min_completeness <= 1
    ):
        raise ValueError("min_completeness must be between 0 and 1.")

    scenarios = build_weight_scenarios(base_weights, relative_change)
    scenario_rankings = {}
    appearance_counts = {
        k: {site_id: 0 for site_id in candidates}
        for k in top_k
    }

    for scenario_name, weights in scenarios.items():
        result = rank_candidates(
            candidates=candidates,
            weights=weights,
            target_site_id=target_site_id,
            min_completeness=min_completeness,
        )
        ranking = result["ranking"]
        scenario_rankings[scenario_name] = ranking

        for k in top_k:
            for candidate in ranking[:k]:
                appearance_counts[k][candidate["site_id"]] += 1

    # Slope-only baseline, calculated over the same accepted candidate inputs.
    slope_candidates = {
        site_id: {"slope": distances.get("slope")}
        for site_id, distances in candidates.items()
    }
    slope_baseline_result = rank_candidates(
        candidates=slope_candidates,
        weights={"slope": 1.0},
        target_site_id=target_site_id,
        min_completeness=min_completeness,
    )

    return {
        "target_site_id": target_site_id.strip(),
        "scenario_count": len(scenarios),
        "relative_change": relative_change,
        "scenario_rankings": scenario_rankings,
        "top_k_counts": appearance_counts,
        "slope_only_baseline": {
            "ranking": slope_baseline_result["ranking"],
            "rejected_candidates": slope_baseline_result["rejected_candidates"],
        },
        "interpretation": (
            "Top-K values are counts across tested weight scenarios, "
            "not probabilities or confidence levels."
        ),
    }


def run_matching_robustness(
    matching_result: Mapping,
    base_weights: Mapping[str, float],
    *,
    relative_change: float = 0.20,
    top_k: tuple[int, ...] = (3, 5),
    min_completeness: float = 0.0,
) -> dict:
    """Run weight sensitivity and a rank-change Slope-only baseline."""
    if not isinstance(matching_result, Mapping):
        raise TypeError("matching_result must be a mapping.")

    target_site_id = matching_result.get("target_site_id")
    full_ranking = matching_result.get("ranking")
    if not isinstance(target_site_id, str) or not target_site_id.strip():
        raise ValueError("matching_result must include target_site_id.")
    if not isinstance(full_ranking, list) or not full_ranking:
        raise ValueError("matching_result must include a non-empty ranking.")

    candidate_distances = {}
    for item in full_ranking:
        site_id = item.get("site_id")
        group_distances = item.get("group_distances")
        if not isinstance(site_id, str) or not isinstance(group_distances, Mapping):
            raise ValueError("Each ranked candidate must include site_id and group_distances.")
        candidate_distances[site_id] = group_distances

    sensitivity = run_weight_sensitivity(
        candidate_distances,
        base_weights,
        target_site_id=target_site_id,
        relative_change=relative_change,
        top_k=top_k,
        min_completeness=min_completeness,
    )

    from src.matching.baseline import compare_slope_only_baseline

    baseline = compare_slope_only_baseline(matching_result)

    return {
        "target_site_id": target_site_id,
        "weight_sensitivity": sensitivity,
        "slope_only_baseline": baseline,
    }
