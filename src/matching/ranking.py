
"""
Candidate ranking engine for AREA 67.
"""

from collections.abc import Mapping

from src.matching.similarity import weighted_similarity_distance


def rank_candidates(
    candidates: Mapping[str, Mapping[str, float | None]],
    weights: Mapping[str, float],
    min_completeness: float = 0.0,
) -> dict:
    """
    Rank Earth candidate sites by ascending similarity distance.
    Smaller distance means greater terrain similarity.
    """

    if not candidates:
        raise ValueError("At least one candidate is required.")

    ranked = []
    rejected = []

    for site_id, group_distances in candidates.items():
        try:
            result = weighted_similarity_distance(
                group_distances=group_distances,
                weights=weights,
                min_completeness=min_completeness,
            )

            ranked.append({
                "site_id": site_id,
                **result,
            })

        except (ValueError, TypeError) as error:
            rejected.append({
                "site_id": site_id,
                "reason": str(error),
            })

    ranked.sort(
        key=lambda item: (
            item["similarity_distance"],
            item["site_id"],
        )
    )

    for position, candidate in enumerate(ranked, start=1):
        candidate["rank"] = position

    return {
        "ranking": ranked,
        "rejected_candidates": rejected,
    }
