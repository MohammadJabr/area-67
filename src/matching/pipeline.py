"""End-to-end Space-to-Earth matching from terrain fingerprints."""

from collections.abc import Mapping
from math import isfinite

from src.matching.feature_distances import compare_terrain_fingerprints
from src.matching.similarity import weighted_similarity_distance


def rank_terrain_fingerprints(
    target_fingerprint: Mapping,
    candidate_fingerprints: Mapping[str, Mapping],
    weights: Mapping[str, float],
    tolerances: Mapping[str, float],
    *,
    mission_profile: str,
    min_feature_group_completeness: float = 0.0,
    min_data_completeness: float = 0.0,
    scale_relative_tolerance: float = 0.01,
    distribution_sum_tolerance_pp: float = 0.5,
) -> dict:
    """Compare one planetary target with Earth fingerprints and rank candidates.

    data_completeness is the conservative minimum of:
    - the fraction of mission weight represented by available feature groups;
    - the lower valid-raster coverage of the target/candidate pair.

    This does not represent direct instrument-observation coverage. Such
    support (for example, LOLA LDEC counts) is reported separately when supplied.
    """
    if not isinstance(target_fingerprint, Mapping):
        raise TypeError("target_fingerprint must be a mapping.")
    target_site_id = target_fingerprint.get("site_id")
    if not isinstance(target_site_id, str) or not target_site_id.strip():
        raise ValueError("Target fingerprint must have a non-empty site_id.")

    if not isinstance(candidate_fingerprints, Mapping) or not candidate_fingerprints:
        raise ValueError("At least one candidate fingerprint is required.")

    if not isinstance(mission_profile, str) or not mission_profile.strip():
        raise ValueError("mission_profile must be a non-empty string.")

    for name, value in (
        ("min_feature_group_completeness", min_feature_group_completeness),
        ("min_data_completeness", min_data_completeness),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or not 0.0 <= value <= 1.0
        ):
            raise ValueError(f"{name} must be between 0 and 1.")

    ranked = []
    rejected = []

    for candidate_key, fingerprint in candidate_fingerprints.items():
        try:
            if not isinstance(candidate_key, str) or not candidate_key.strip():
                raise ValueError("Candidate mapping keys must be non-empty site IDs.")
            if not isinstance(fingerprint, Mapping):
                raise TypeError("Candidate fingerprint must be a mapping.")

            fingerprint_id = fingerprint.get("site_id")
            if fingerprint_id != candidate_key:
                raise ValueError(
                    f"Candidate mapping key {candidate_key!r} does not match "
                    f"fingerprint site_id {fingerprint_id!r}."
                )

            comparison = compare_terrain_fingerprints(
                target_fingerprint,
                fingerprint,
                tolerances,
                scale_relative_tolerance=scale_relative_tolerance,
                distribution_sum_tolerance_pp=distribution_sum_tolerance_pp,
            )

            aggregation = weighted_similarity_distance(
                comparison["group_distances"],
                weights,
                min_completeness=min_feature_group_completeness,
            )

            feature_completeness = aggregation["data_completeness"]
            raster_completeness = comparison["valid_raster_coverage_completeness"]
            overall_completeness = min(feature_completeness, raster_completeness)

            if overall_completeness < min_data_completeness:
                raise ValueError(
                    f"Data completeness {overall_completeness:.2%} is below "
                    f"the required minimum {min_data_completeness:.2%}."
                )

            distance = aggregation["similarity_distance"]
            ranked.append({
                "site_id": candidate_key,
                "candidate_site_id": candidate_key,
                "similarity_distance": distance,
                "similarity_score": 100.0 / (1.0 + distance),
                "feature_group_completeness": feature_completeness,
                "valid_raster_coverage_completeness": raster_completeness,
                "data_completeness": overall_completeness,
                "used_groups": aggregation["used_groups"],
                "missing_groups": comparison["missing_groups"],
                "group_distances": comparison["group_distances"],
                "group_contributions": aggregation["group_contributions"],
                "method_warnings": comparison["method_warnings"],
                "target_analysis_scale_m": comparison["target_analysis_scale_m"],
                "candidate_analysis_scale_m": comparison["candidate_analysis_scale_m"],
                "target_valid_coverage_pct": comparison["target_valid_coverage_pct"],
                "candidate_valid_coverage_pct": comparison["candidate_valid_coverage_pct"],
                "target_direct_observation_coverage_pct": (
                    comparison["target_direct_observation_coverage_pct"]
                ),
                "candidate_direct_observation_coverage_pct": (
                    comparison["candidate_direct_observation_coverage_pct"]
                ),
                "normalization_method": comparison["normalization_method"],
                "normalization_tolerances": comparison["normalization_tolerances"],
            })

        except (ValueError, TypeError) as error:
            rejected.append({
                "site_id": candidate_key,
                "reason": str(error),
            })

    ranked.sort(
        key=lambda item: (item["similarity_distance"], item["site_id"])
    )
    for position, candidate in enumerate(ranked, start=1):
        candidate["rank"] = position

    return {
        "target_site_id": target_site_id.strip(),
        "candidate_site_ids": sorted(candidate_fingerprints),
        "mission_profile": mission_profile.strip(),
        "mission_weights": dict(weights),
        "feature_tolerances": dict(tolerances),
        "min_feature_group_completeness": float(min_feature_group_completeness),
        "min_data_completeness": float(min_data_completeness),
        "scale_relative_tolerance": float(scale_relative_tolerance),
        "distribution_sum_tolerance_pp": float(distribution_sum_tolerance_pp),
        "ranking": ranked,
        "rejected_candidates": rejected,
        "matching_method": {
            "group_distance": (
                "RMS of metric differences divided by explicit feature tolerances"
            ),
            "aggregation": (
                "square root of weighted mean squared group distances; "
                "available weights are renormalized when groups are missing"
            ),
            "similarity_score": "100 / (1 + weighted_distance); index from 0 to 100",
            "score_interpretation": (
                "Monotonic relative ranking index, not a probability, "
                "site certification, or mission-success estimate"
            ),
            "data_completeness": (
                "minimum of available feature-weight fraction and lower "
                "valid-raster coverage for the target/candidate pair"
            ),
            "weight_status": (
                "Mission weights are team-selected operational assumptions, "
                "not NASA or rover-manufacturer specifications."
            ),
        },
    }
