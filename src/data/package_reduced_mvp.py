"""Package the existing canonical Slope-only baseline as a separate MVP dataset.

This utility selects and reformats already-computed outputs. It does not read or
process rasters, calculate fingerprints, or implement a matching method.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

DEFAULT_FINGERPRINTS = Path("data/processed/terrain_fingerprints.csv")
DEFAULT_RANKINGS = Path("data/processed/candidate_rankings.csv")
DEFAULT_ROBUSTNESS = Path("data/processed/ranking_robustness.json")
DEFAULT_OUTPUT = Path("data/processed/exploratory_mvp_2026-11-15_v2")
TARGET_ID = "MOON_SITE01_PILOT990"
RANKING_FIELDS = (
    "target_site_id",
    "candidate_site_id",
    "mission_profile",
    "rank",
    "similarity_score",
    "weighted_distance",
    "slope_group_distance",
    "ranking_basis",
    "ranking_stability_note",
    "ranking_note",
    "scientific_status",
    "source_multifeature_rank",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required input file is missing: {path}")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"Input CSV has no header: {path}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Input CSV has no data rows: {path}")
    return list(reader.fieldnames), rows


def write_csv(path: Path, fields: tuple[str, ...] | list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def package_reduced_mvp(
    fingerprints_path: Path = DEFAULT_FINGERPRINTS,
    rankings_path: Path = DEFAULT_RANKINGS,
    robustness_path: Path = DEFAULT_ROBUSTNESS,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    """Write a new, no-overwrite, one-target/three-candidate Slope-only package."""
    if output_dir.exists():
        raise FileExistsError(
            f"Output path already exists; choose a new path to preserve it: {output_dir}"
        )
    if not robustness_path.is_file():
        raise FileNotFoundError(f"Required input file is missing: {robustness_path}")

    fingerprint_fields, fingerprints = read_csv(fingerprints_path)
    _, prior_rankings = read_csv(rankings_path)
    robustness = json.loads(robustness_path.read_text(encoding="utf-8"))

    if robustness.get("status") != "EXPLORATORY_NOT_APPROVED":
        raise ValueError("Expected exploratory, not-approved source results.")
    if robustness.get("target_site_id") != TARGET_ID:
        raise ValueError("Robustness input does not describe the configured Site01 target.")
    target_ids = [row.get("site_id") for row in fingerprints if row.get("planet", "").casefold() == "moon"]
    if target_ids != [TARGET_ID]:
        raise ValueError(f"Expected exactly one Moon target {TARGET_ID}; found {target_ids}.")

    configured_candidates = robustness.get("scope", {}).get("candidate_windows", [])
    if len(configured_candidates) != 3 or len(set(configured_candidates)) != 3:
        raise ValueError("Expected the existing three-candidate exploratory shortlist.")
    fingerprint_ids = [row.get("site_id") for row in fingerprints]
    expected_ids = {TARGET_ID, *configured_candidates}
    if set(fingerprint_ids) != expected_ids or len(fingerprint_ids) != len(expected_ids):
        raise ValueError("Fingerprint rows do not match the target and configured candidate set.")

    slope_rows = robustness.get("slope_only_baseline")
    if not isinstance(slope_rows, list) or len(slope_rows) != len(configured_candidates):
        raise ValueError("Slope-only baseline is missing or has the wrong candidate count.")
    baseline_ids = [row.get("site_id") for row in slope_rows]
    if set(baseline_ids) != set(configured_candidates) or len(set(baseline_ids)) != len(baseline_ids):
        raise ValueError("Slope-only baseline candidates do not match the configured shortlist.")

    prior_by_candidate = {row.get("candidate_site_id"): row for row in prior_rankings}
    if set(prior_by_candidate) != set(configured_candidates):
        raise ValueError("Existing matcher ranking rows do not match the configured candidates.")
    for candidate_id in configured_candidates:
        prior = prior_by_candidate[candidate_id]
        if prior.get("target_site_id") != TARGET_ID:
            raise ValueError(f"Existing ranking has an unexpected target for {candidate_id}.")

    ranked = sorted(slope_rows, key=lambda row: int(row["rank"]))
    output_rankings: list[dict[str, Any]] = []
    for row in ranked:
        candidate_id = row["site_id"]
        prior = prior_by_candidate[candidate_id]
        score = float(row["similarity_score"])
        distance = float(row["similarity_distance"])
        if not math.isfinite(score) or not math.isfinite(distance) or distance < 0:
            raise ValueError(f"Non-finite or invalid Slope-only result for {candidate_id}.")
        output_rankings.append({
            "target_site_id": TARGET_ID,
            "candidate_site_id": candidate_id,
            "mission_profile": robustness.get("mission_profile", ""),
            "rank": int(row["rank"]),
            "similarity_score": score,
            "weighted_distance": distance,
            "slope_group_distance": distance,
            "ranking_basis": "Slope P50 and P90 only; canonical matcher Slope-only baseline",
            "ranking_stability_note": "No Slope-only sensitivity scenarios are included in this package.",
            "ranking_note": (
                "EXPLORATORY ONLY: relative result from provisional reference-centred windows; "
                "not an approved geomorphic AOI, site certification, or mission suitability."
            ),
            "scientific_status": "EXPLORATORY_NOT_APPROVED",
            "source_multifeature_rank": prior.get("rank", ""),
        })

    output_dir.mkdir(parents=True)
    fp_path = output_dir / "terrain_fingerprints.csv"
    rank_path = output_dir / "candidate_rankings.csv"
    robustness_out = output_dir / "ranking_robustness.json"
    readme_path = output_dir / "README.md"
    manifest_path = output_dir / "package_manifest.json"

    selected_fingerprints = [row for row in fingerprints if row["site_id"] in expected_ids]
    selected_fingerprints.sort(key=lambda row: (row["planet"] != "Moon", row["site_id"]))
    write_csv(fp_path, fingerprint_fields, selected_fingerprints)
    write_csv(rank_path, RANKING_FIELDS, output_rankings)

    compact_robustness = {
        "status": "EXPLORATORY_NOT_APPROVED",
        "target_site_id": TARGET_ID,
        "candidate_site_ids": [row["site_id"] for row in ranked],
        "ranking_basis": "Canonical matcher Slope-only baseline using supplied slope P50/P90 features.",
        "source_robustness_status": robustness["status"],
        "source_slope_only_baseline": ranked,
        "multi_feature_ranking_preserved_separately": str(rankings_path),
        "limitations": [
            "All footprints are provisional reference-centred windows, not approved geomorphic AOIs.",
            "Scores are relative indices, not probabilities or suitability certification.",
            "No Slope-only tolerance/weight sensitivity analysis is included.",
            "Slope-only ranking does not establish that slope alone is scientifically sufficient.",
            "The original multi-feature fingerprint, ranking, and robustness files are unchanged.",
        ],
    }
    robustness_out.write_text(json.dumps(compact_robustness, indent=2) + "\n", encoding="utf-8")
    readme_path.write_text(
        "# Reduced exploratory MVP dataset\n\n"
        "One Site01 target and three existing Earth reference windows. The ranking uses only the "
        "canonical matcher Slope-only baseline (Slope P50/P90 inputs). The fingerprint table keeps "
        "all supplied feature/provenance columns unchanged for context; non-Slope groups do not "
        "contribute to this package's ranking. All study windows and matching settings remain "
        "exploratory and unapproved. See `docs/FINAL_MVP_METHOD_AND_RESULTS_2026-11-15.md`.\n",
        encoding="utf-8",
    )

    source_paths = [fingerprints_path, rankings_path, robustness_path]
    outputs = [fp_path, rank_path, robustness_out, readme_path]
    manifest = {
        "status": "EXPLORATORY_NOT_APPROVED",
        "target_site_id": TARGET_ID,
        "candidate_site_ids": [row["site_id"] for row in ranked],
        "ranking_basis": "Existing canonical Slope-only baseline; no matching algorithm implemented here.",
        "source_files": {str(path): sha256_file(path) for path in source_paths},
        "outputs": {path.name: sha256_file(path) for path in outputs},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "output_dir": str(output_dir),
        "target_site_id": TARGET_ID,
        "candidate_site_ids": [row["candidate_site_id"] for row in output_rankings],
        "ranking": output_rankings,
        "manifest": str(manifest_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fingerprints", type=Path, default=DEFAULT_FINGERPRINTS)
    parser.add_argument("--rankings", type=Path, default=DEFAULT_RANKINGS)
    parser.add_argument("--robustness", type=Path, default=DEFAULT_ROBUSTNESS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(package_reduced_mvp(args.fingerprints, args.rankings, args.robustness, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
