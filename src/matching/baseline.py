"""Compare multi-feature rankings with a Slope-only baseline."""

from collections.abc import Mapping

from src.matching.ranking import rank_candidates


def compare_slope_only_baseline(matching_result: Mapping) -> dict:
    """Compare an existing multi-feature ranking with Slope-only ordering.

    The comparison uses only candidates accepted by the multi-feature pipeline.
    Candidates without a computed Slope group are excluded from the baseline
    and reported, rather than being assigned a zero distance.
    """
    if not isinstance(matching_result, Mapping):
        raise TypeError("matching_result must be a mapping.")

    target_site_id = matching_result.get("target_site_id")
    if not isinstance(target_site_id, str) or not target_site_id.strip():
        raise ValueError("matching_result must contain target_site_id.")

    full_ranking = matching_result.get("ranking")
    if not isinstance(full_ranking, list) or not full_ranking:
        raise ValueError("matching_result must contain a non-empty ranking list.")

    slope_candidates = {}
    for candidate in full_ranking:
        site_id = candidate.get("site_id")
        group_distances = candidate.get("group_distances", {})
        if not isinstance(site_id, str) or not isinstance(group_distances, Mapping):
            raise ValueError("Each ranked candidate must contain site_id and group_distances.")
        slope_candidates[site_id] = {"slope": group_distances.get("slope")}

    baseline_result = rank_candidates(
        candidates=slope_candidates,
        weights={"slope": 1.0},
        target_site_id=target_site_id,
    )

    full_ranks = {
        item["site_id"]: item["rank"]
        for item in full_ranking
    }
    baseline_ranks = {
        item["site_id"]: item["rank"]
        for item in baseline_result["ranking"]
    }

    comparison = []
    for site_id, full_rank in full_ranks.items():
        baseline_rank = baseline_ranks.get(site_id)
        comparison.append({
            "site_id": site_id,
            "multi_feature_rank": full_rank,
            "slope_only_rank": baseline_rank,
            "rank_change_vs_slope_only": (
                full_rank - baseline_rank if baseline_rank is not None else None
            ),
            "included_in_slope_baseline": baseline_rank is not None,
        })

    comparison.sort(key=lambda item: item["multi_feature_rank"])

    return {
        "target_site_id": target_site_id,
        "multi_feature_ranking": full_ranking,
        "slope_only_ranking": baseline_result["ranking"],
        "slope_only_rejected_candidates": baseline_result["rejected_candidates"],
        "rank_comparison": comparison,
        "interpretation": (
            "Rank change is descriptive: positive means the candidate ranks "
            "lower in the multi-feature result than in the Slope-only baseline. "
            "It is not an accuracy or probability measure."
        ),
    }
