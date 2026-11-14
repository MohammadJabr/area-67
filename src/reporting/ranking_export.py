"""Export canonical candidate rankings for the AREA 67 application.

Similarity score is 100 / (1 + weighted_distance). It is a monotonic
0-100 ranking index, not a percentage of physical equivalence or success.
"""

import csv
from collections.abc import Mapping
from math import isfinite
from pathlib import Path


OUTPUT_COLUMNS = [
    "target_site_id",
    "candidate_site_id",
    "mission_profile",
    "rank",
    "similarity_score",
    "weighted_distance",
    "slope_contribution",
    "tri_contribution",
    "relief_contribution",
    "distribution_contribution",
    "spatial_pattern_contribution",
    "data_completeness",
    "feature_group_completeness",
    "valid_raster_coverage_completeness",
    "ranking_stability_note",
    "ranking_note",
]


GROUP_COLUMNS = {
    "slope": "slope_contribution",
    "tri": "tri_contribution",
    "local_relief": "relief_contribution",
    "terrain_distribution": "distribution_contribution",
    "spatial_pattern": "spatial_pattern_contribution",
}


def relative_similarity_index(distance: float) -> float:
    """Map a non-negative weighted distance to a monotonic 0-100 index."""
    if (
        isinstance(distance, bool)
        or not isinstance(distance, (int, float))
        or not isfinite(distance)
        or distance < 0
    ):
        raise ValueError("Distance must be finite, numeric, and non-negative.")
    return 100.0 / (1.0 + float(distance))


def export_rankings_csv(
    ranking_result: Mapping,
    mission_profile: str,
    output_path: str | Path,
    ranking_stability_note: str = "",
) -> Path:
    """Export rankings using the canonical application integration fields."""
    if not isinstance(ranking_result, Mapping):
        raise TypeError("ranking_result must be a mapping.")

    candidates = ranking_result.get("ranking")
    if not isinstance(candidates, list):
        raise ValueError("ranking_result must contain a ranking list.")

    target_site_id = ranking_result.get("target_site_id")
    if not isinstance(target_site_id, str) or not target_site_id.strip():
        raise ValueError("ranking_result must include a non-empty target_site_id.")

    if not isinstance(mission_profile, str) or not mission_profile.strip():
        raise ValueError("mission_profile cannot be empty.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise TypeError("Every ranked candidate must be a mapping.")

        candidate_site_id = candidate.get("candidate_site_id", candidate.get("site_id"))
        if not isinstance(candidate_site_id, str) or not candidate_site_id.strip():
            raise ValueError("Every candidate must include candidate_site_id or site_id.")

        distance = candidate.get("similarity_distance", candidate.get("weighted_distance"))
        score = candidate.get("similarity_score")
        if score is None:
            score = relative_similarity_index(distance)
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not isfinite(score)
            or not 0.0 <= score <= 100.0
        ):
            raise ValueError("similarity_score must be finite and between 0 and 100.")

        completeness = candidate.get("data_completeness")
        if (
            isinstance(completeness, bool)
            or not isinstance(completeness, (int, float))
            or not isfinite(completeness)
            or not 0.0 <= completeness <= 1.0
        ):
            raise ValueError("data_completeness must be finite and between 0 and 1.")

        row = {
            "target_site_id": target_site_id.strip(),
            "candidate_site_id": candidate_site_id.strip(),
            "mission_profile": mission_profile.strip(),
            "rank": candidate.get("rank"),
            "similarity_score": round(float(score), 4),
            "weighted_distance": round(float(distance), 8),
            "data_completeness": round(float(completeness), 4),
            "feature_group_completeness": candidate.get("feature_group_completeness", ""),
            "valid_raster_coverage_completeness": candidate.get(
                "valid_raster_coverage_completeness", ""
            ),
            "ranking_stability_note": ranking_stability_note,
            "ranking_note": (
                "similarity_score = 100 / (1 + weighted_distance); "
                "relative ranking index, not a probability or certification"
            ),
        }

        contributions = candidate.get("group_contributions", {})
        for group, column in GROUP_COLUMNS.items():
            contribution = contributions.get(group) if isinstance(contributions, Mapping) else None
            value = contribution.get("distance_share") if isinstance(contribution, Mapping) else None
            row[column] = round(float(value), 6) if value is not None else ""

        rows.append(row)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return path
