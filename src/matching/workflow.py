"""Run matching, robustness analysis, and canonical CSV export."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from src.data.contracts import validate_fingerprints
from src.data.fingerprint_loader import (
    load_terrain_fingerprints_csv,
    select_space_to_earth_fingerprints,
)
from src.matching.pipeline import rank_terrain_fingerprints
from src.matching.sensitivity import run_matching_robustness
from src.reporting.ranking_export import export_rankings_csv


def _write_robustness_summary(
    output_path: str | Path,
    ranking_result: Mapping,
    robustness_result: Mapping,
) -> Path:
    """Write a compact, reproducible JSON sidecar for baseline/sensitivity."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    sensitivity = robustness_result["weight_sensitivity"]
    baseline = robustness_result["slope_only_baseline"]

    summary = {
        "target_site_id": ranking_result["target_site_id"],
        "mission_profile": ranking_result["mission_profile"],
        "mission_weights": ranking_result.get("mission_weights", {}),
        "feature_tolerances": ranking_result.get("feature_tolerances", {}),
        "matching_method": ranking_result.get("matching_method", {}),
        "sensitivity": {
            "scenario_count": sensitivity["scenario_count"],
            "relative_change": sensitivity["relative_change"],
            "top_k_counts": sensitivity["top_k_counts"],
            "interpretation": sensitivity["interpretation"],
        },
        "slope_only_baseline": {
            "ranking": [
                {
                    "site_id": item["site_id"],
                    "rank": item["rank"],
                    "similarity_distance": item["similarity_distance"],
                }
                for item in baseline["slope_only_ranking"]
            ],
            "rank_comparison": baseline["rank_comparison"],
            "interpretation": baseline["interpretation"],
        },
        "limitations": [
            "Top-K appearance counts are descriptive counts across tested weight scenarios, not probabilities.",
            "The similarity score is a relative ranking index, not a mission-success probability or site certification.",
            "Results depend on the supplied feature tolerances, mission weights, source quality, and method metadata.",
        ],
    }

    path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path


def run_matching_workflow(
    target_fingerprint: Mapping,
    candidate_fingerprints: Mapping[str, Mapping],
    weights: Mapping[str, float],
    tolerances: Mapping[str, float],
    *,
    mission_profile: str,
    ranking_output_path: str | Path = "data/processed/candidate_rankings.csv",
    robustness_output_path: str | Path = "data/processed/ranking_robustness.json",
    min_feature_group_completeness: float = 0.0,
    min_data_completeness: float = 0.0,
    scale_relative_tolerance: float = 0.01,
    distribution_sum_tolerance_pp: float = 0.5,
    weight_relative_change: float = 0.20,
    top_k: tuple[int, ...] = (3, 5),
) -> dict:
    """Execute one complete target-to-Earth matching and export workflow.

    This function deliberately requires explicit tolerances. It never supplies
    scientific threshold values implicitly.
    """
    ranking_result = rank_terrain_fingerprints(
        target_fingerprint=target_fingerprint,
        candidate_fingerprints=candidate_fingerprints,
        weights=weights,
        tolerances=tolerances,
        mission_profile=mission_profile,
        min_feature_group_completeness=min_feature_group_completeness,
        min_data_completeness=min_data_completeness,
        scale_relative_tolerance=scale_relative_tolerance,
        distribution_sum_tolerance_pp=distribution_sum_tolerance_pp,
    )

    if not ranking_result["ranking"]:
        reasons = "; ".join(
            f"{item['site_id']}: {item['reason']}"
            for item in ranking_result["rejected_candidates"]
        )
        raise ValueError(
            "No candidate could be ranked. Review fingerprint metadata and method "
            f"compatibility. Rejections: {reasons or 'no eligible candidates'}"
        )

    robustness_result = run_matching_robustness(
        ranking_result,
        weights,
        relative_change=weight_relative_change,
        top_k=top_k,
        min_completeness=min_feature_group_completeness,
    )

    ranking_path = export_rankings_csv(
        ranking_result=ranking_result,
        mission_profile=mission_profile,
        output_path=ranking_output_path,
        robustness_result=robustness_result,
    )
    robustness_path = _write_robustness_summary(
        robustness_output_path,
        ranking_result,
        robustness_result,
    )

    return {
        "ranking_result": ranking_result,
        "robustness_result": robustness_result,
        "ranking_csv": ranking_path,
        "robustness_json": robustness_path,
    }


def run_matching_from_csv(
    fingerprints_csv: str | Path,
    target_site_id: str,
    weights: Mapping[str, float],
    tolerances: Mapping[str, float],
    **workflow_options,
) -> dict:
    """Load the canonical fingerprint table and execute the matching workflow."""
    records = load_terrain_fingerprints_csv(fingerprints_csv)

    # Validate the complete table against the same fingerprint contract used
    # by the Streamlit application before producing an app-facing ranking.
    fingerprint_errors = validate_fingerprints(pd.DataFrame(records))
    if fingerprint_errors:
        raise ValueError(
            "Terrain fingerprints do not satisfy the application data contract: "
            + "; ".join(fingerprint_errors)
        )

    target, candidates = select_space_to_earth_fingerprints(
        records,
        target_site_id,
    )
    return run_matching_workflow(
        target,
        candidates,
        weights,
        tolerances,
        **workflow_options,
    )
