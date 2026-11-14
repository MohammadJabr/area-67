
"""
CSV export for AREA 67 candidate rankings.

The relative similarity index is 100 / (1 + distance).
It is a relative ranking indicator, NOT a probability
or a measure of mission success.
"""

import csv
from pathlib import Path
from collections.abc import Mapping
from math import isfinite


OUTPUT_COLUMNS = [
    "site_id",
    "mission_profile",
    "similarity_distance",
    "relative_similarity",
    "rank",
    "slope_contribution",
    "tri_contribution",
    "relief_contribution",
    "distribution_contribution",
    "spatial_pattern_contribution",
    "data_completeness",
    "ranking_stability_note",
]


GROUP_COLUMNS = {
    "slope": "slope_contribution",
    "tri": "tri_contribution",
    "local_relief": "relief_contribution",
    "terrain_distribution": "distribution_contribution",
    "spatial_pattern": "spatial_pattern_contribution",
}


def relative_similarity_index(distance: float) -> float:
    """Convert distance into a relative ranking index."""

    if not isinstance(distance, (int, float)):
        raise ValueError("Distance must be numeric.")

    if not isfinite(distance) or distance < 0:
        raise ValueError("Distance must be finite and non-negative.")

    return 100.0 / (1.0 + distance)


def export_rankings_csv(
    ranking_result: Mapping,
    mission_profile: str,
    output_path: str | Path,
    ranking_stability_note: str = "",
) -> Path:
    """Export ranked candidates and their feature contributions."""

    if not isinstance(ranking_result, Mapping):
        raise TypeError("ranking_result must be a mapping.")

    candidates = ranking_result.get("ranking")

    if not isinstance(candidates, list):
        raise ValueError("ranking_result must contain a ranking list.")

    if not isinstance(mission_profile, str) or not mission_profile.strip():
        raise ValueError("mission_profile cannot be empty.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for candidate in candidates:
        distance = candidate["similarity_distance"]

        row = {
            "site_id": candidate["site_id"],
            "mission_profile": mission_profile,
            "similarity_distance": distance,
            "relative_similarity": round(
                relative_similarity_index(distance), 4
            ),
            "rank": candidate["rank"],
            "data_completeness": round(
                candidate["data_completeness"], 4
            ),
            "ranking_stability_note": ranking_stability_note,
        }

        contributions = candidate.get("group_contributions", {})

        for group, column in GROUP_COLUMNS.items():
            contribution = contributions.get(group)

            # Keep missing feature contributions blank.
            row[column] = (
                round(contribution["distance_share"], 6)
                if contribution is not None
                else ""
            )

        rows.append(row)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return path
