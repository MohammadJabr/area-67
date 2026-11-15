"""One-at-a-time feature-tolerance sensitivity for AREA 67 matching.

Each scenario changes one declared feature tolerance while holding the other
tolerances, mission weights, completeness gates, and input fingerprints fixed.
Scenario counts are descriptive robustness checks, not probabilities.
"""
from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

from src.matching.pipeline import rank_terrain_fingerprints


def run_tolerance_sensitivity(
    target_fingerprint: Mapping,
    candidate_fingerprints: Mapping[str, Mapping],
    weights: Mapping[str, float],
    tolerances: Mapping[str, float],
    *,
    mission_profile: str,
    min_feature_group_completeness: float,
    min_data_completeness: float,
    scale_relative_tolerance: float = 0.01,
    distribution_sum_tolerance_pp: float = 0.5,
    factors: tuple[float, ...] = (0.5, 1.0, 1.5),
    top_k: tuple[int, ...] = (1, 3, 5),
) -> dict:
    """Run baseline plus one-at-a-time low/high tolerance perturbations."""
    if not isinstance(tolerances, Mapping) or not tolerances:
        raise ValueError("tolerances must be a non-empty mapping.")
    if len(factors) != 3 or any(
        isinstance(factor, bool)
        or not isinstance(factor, (int, float))
        or not isfinite(factor)
        or factor <= 0
        for factor in factors
    ):
        raise ValueError("factors must contain three positive finite numbers.")
    if factors[1] != 1.0 or not factors[0] < 1.0 < factors[2]:
        raise ValueError("factors must be ordered around the 1.0 baseline.")
    if not top_k or any(
        isinstance(k, bool) or not isinstance(k, int) or k < 1 for k in top_k
    ):
        raise ValueError("top_k must contain positive integers.")

    scenarios = {"baseline": dict(tolerances)}
    for key, value in tolerances.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value <= 0
        ):
            raise ValueError(f"Tolerance {key!r} must be positive and finite.")
        for factor in (factors[0], factors[2]):
            adjusted = dict(tolerances)
            adjusted[key] = float(value) * float(factor)
            scenarios[f"{key}_{factor:g}x"] = adjusted

    rankings = {}
    rejected = {}
    candidate_ids = list(candidate_fingerprints)
    appearances = {k: {site_id: 0 for site_id in candidate_ids} for k in top_k}

    for name, scenario_tolerances in scenarios.items():
        result = rank_terrain_fingerprints(
            target_fingerprint,
            candidate_fingerprints,
            weights,
            scenario_tolerances,
            mission_profile=mission_profile,
            min_feature_group_completeness=min_feature_group_completeness,
            min_data_completeness=min_data_completeness,
            scale_relative_tolerance=scale_relative_tolerance,
            distribution_sum_tolerance_pp=distribution_sum_tolerance_pp,
        )
        ranking = result["ranking"]
        rankings[name] = [
            {
                "site_id": item["site_id"],
                "rank": item["rank"],
                "similarity_distance": item["similarity_distance"],
                "similarity_score": item["similarity_score"],
            }
            for item in ranking
        ]
        rejected[name] = result["rejected_candidates"]
        for k in top_k:
            for item in ranking[:k]:
                appearances[k][item["site_id"]] += 1

    baseline_order = [item["site_id"] for item in rankings["baseline"]]
    rank_changes = {}
    for scenario_name, ranking in rankings.items():
        scenario_order = [item["site_id"] for item in ranking]
        rank_changes[scenario_name] = {
            site_id: (
                scenario_order.index(site_id) + 1 if site_id in scenario_order else None
            )
            for site_id in candidate_ids
        }

    return {
        "scenario_count": len(scenarios),
        "factors": list(factors),
        "method": (
            "Baseline plus one-at-a-time 0.5x and 1.5x perturbations of each "
            "feature tolerance; all other settings and inputs are held fixed."
        ),
        "baseline_order": baseline_order,
        "scenario_rankings": rankings,
        "rank_by_scenario": rank_changes,
        "top_k_counts": appearances,
        "rejected_candidates_by_scenario": rejected,
        "interpretation": (
            "Top-K appearances and rank changes are descriptive sensitivity "
            "results, not probabilities, confidence levels, or validation."
        ),
    }
