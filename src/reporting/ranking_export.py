"""Export canonical candidate rankings for the AREA 67 application.

Similarity score is 100 / (1 + weighted_distance). It is a monotonic
0-100 ranking index, not a percentage of physical equivalence or success.
"""

import csv
from collections.abc import Mapping
from math import isclose, isfinite
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
    "target_valid_coverage_pct",
    "candidate_valid_coverage_pct",
    "target_direct_observation_coverage_pct",
    "candidate_direct_observation_coverage_pct",
    "target_analysis_scale_m",
    "candidate_analysis_scale_m",
    "missing_groups",
    "method_warnings",
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


def _optional_finite_number(value, field: str):
    if value is None:
        return ""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
    ):
        raise ValueError(f"{field} must be finite and numeric when supplied.")
    return round(float(value), 6)


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
        expected_score = relative_similarity_index(distance)
        score = candidate.get("similarity_score", expected_score)
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not isfinite(score)
            or not 0.0 <= score <= 100.0
        ):
            raise ValueError("similarity_score must be finite and between 0 and 100.")
        if not isclose(float(score), expected_score, rel_tol=1e-8, abs_tol=1e-8):
            raise ValueError("similarity_score does not match 100 / (1 + weighted_distance).")

        rank = candidate.get("rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            raise ValueError("rank must be a positive integer.")

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
            "rank": rank,
            "similarity_score": round(float(score), 4),
            "weighted_distance": round(float(distance), 8),
            "data_completeness": round(float(completeness), 4),
            "feature_group_completeness": _optional_finite_number(
                candidate.get("feature_group_completeness"), "feature_group_completeness"
            ),
            "valid_raster_coverage_completeness": _optional_finite_number(
                candidate.get("valid_raster_coverage_completeness"),
                "valid_raster_coverage_completeness",
            ),
            "target_valid_coverage_pct": _optional_finite_number(
                candidate.get("target_valid_coverage_pct"), "target_valid_coverage_pct"
            ),
            "candidate_valid_coverage_pct": _optional_finite_number(
                candidate.get("candidate_valid_coverage_pct"), "candidate_valid_coverage_pct"
            ),
            "target_direct_observation_coverage_pct": _optional_finite_number(
                candidate.get("target_direct_observation_coverage_pct"),
                "target_direct_observation_coverage_pct",
            ),
            "candidate_direct_observation_coverage_pct": _optional_finite_number(
                candidate.get("candidate_direct_observation_coverage_pct"),
                "candidate_direct_observation_coverage_pct",
            ),
            "target_analysis_scale_m": _optional_finite_number(
                candidate.get("target_analysis_scale_m"), "target_analysis_scale_m"
            ),
            "candidate_analysis_scale_m": _optional_finite_number(
                candidate.get("candidate_analysis_scale_m"), "candidate_analysis_scale_m"
            ),
            "missing_groups": ";".join(candidate.get("missing_groups", [])),
            "method_warnings": "; ".join(candidate.get("method_warnings", [])),
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
            row[column] = _optional_finite_number(value, column)

        rows.append(row)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return path
