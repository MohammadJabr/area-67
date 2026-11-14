"""Command-line entry point for AREA 67 Space-to-Earth matching.

Example:
python -m src.matching.cli \
  --fingerprints data/processed/terrain_fingerprints.csv \
  --target-site-id MOON_SITE04 \
  --tolerances-json config/matching_tolerances.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.matching.mission_profiles import (
    ROVER_NAVIGATION_PROFILE,
    get_mission_weights,
)
from src.matching.workflow import run_matching_from_csv


def _load_tolerances(path: str | Path) -> dict:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Tolerance configuration not found: {source}")

    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in tolerance configuration: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Tolerance configuration must be a JSON object.")

    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank Earth terrain fingerprints against one Moon/Mars target."
    )
    parser.add_argument(
        "--fingerprints",
        default="data/processed/terrain_fingerprints.csv",
        help="Path to the canonical terrain_fingerprints.csv file.",
    )
    parser.add_argument(
        "--target-site-id",
        required=True,
        help="Exact site_id of the Moon/Mars target row.",
    )
    parser.add_argument(
        "--tolerances-json",
        required=True,
        help="JSON file containing explicit metric tolerances. No defaults are invented.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/candidate_rankings.csv",
        help="Canonical ranking CSV output path.",
    )
    parser.add_argument(
        "--robustness-output",
        default="data/processed/ranking_robustness.json",
        help="Baseline and sensitivity JSON output path.",
    )
    parser.add_argument(
        "--min-feature-group-completeness",
        type=float,
        required=True,
        help="Team-approved minimum available mission-weight fraction (0 to 1).",
    )
    parser.add_argument(
        "--min-data-completeness",
        type=float,
        required=True,
        help="Team-approved minimum conservative data completeness (0 to 1).",
    )
    parser.add_argument(
        "--scale-relative-tolerance",
        type=float,
        default=0.01,
        help="Allowed relative difference between target and candidate analysis scales.",
    )
    parser.add_argument(
        "--distribution-sum-tolerance-pp",
        type=float,
        default=0.5,
        help="Allowed deviation from 100 percentage points for terrain-class shares.",
    )
    parser.add_argument(
        "--weight-relative-change",
        type=float,
        default=0.20,
        help="One-at-a-time relative weight perturbation for sensitivity analysis.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        tolerances = _load_tolerances(args.tolerances_json)
        result = run_matching_from_csv(
            fingerprints_csv=args.fingerprints,
            target_site_id=args.target_site_id,
            weights=get_mission_weights(),
            tolerances=tolerances,
            mission_profile=ROVER_NAVIGATION_PROFILE["name"],
            ranking_output_path=args.output,
            robustness_output_path=args.robustness_output,
            min_feature_group_completeness=args.min_feature_group_completeness,
            min_data_completeness=args.min_data_completeness,
            scale_relative_tolerance=args.scale_relative_tolerance,
            distribution_sum_tolerance_pp=args.distribution_sum_tolerance_pp,
            weight_relative_change=args.weight_relative_change,
        )

        ranking = result["ranking_result"]["ranking"]
        print(f"Target: {result['ranking_result']['target_site_id']}")
        print(f"Mission: {result['ranking_result']['mission_profile']}")
        print(f"Ranked Earth candidates: {len(ranking)}")
        if len(ranking) < 3:
            print(
                "WARNING: fewer than three Earth candidates were ranked. "
                "The MVP should use at least three candidates when suitable data are available."
            )
        for item in ranking:
            print(
                f"{item['rank']}. {item['site_id']} | "
                f"distance={item['similarity_distance']:.4f} | "
                f"score={item['similarity_score']:.2f} | "
                f"completeness={item['data_completeness']:.1%}"
            )

        rejected = result["ranking_result"]["rejected_candidates"]
        if rejected:
            print(f"Rejected candidates: {len(rejected)}")
            for item in rejected:
                print(f"- {item['site_id']}: {item['reason']}")

        print(f"Ranking CSV: {result['ranking_csv']}")
        print(f"Robustness JSON: {result['robustness_json']}")
        print(
            "Note: similarity_score is a relative ranking index, "
            "not a probability or certification."
        )
        return 0

    except (FileNotFoundError, TypeError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
