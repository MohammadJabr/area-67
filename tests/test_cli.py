import csv
import json

import pytest

from src.matching.cli import build_parser, main


def test_cli_runs_csv_to_matching_outputs(
    tmp_path, target_fingerprint, earth_candidate, matching_tolerances, capsys
):
    candidate = dict(earth_candidate)
    candidate["site_id"] = "EARTH_A"
    candidate["source_id"] = "DEM_EARTH_A"

    fingerprints_path = tmp_path / "terrain_fingerprints.csv"
    rows = [target_fingerprint, candidate]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with fingerprints_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    tolerances_path = tmp_path / "tolerances.json"
    tolerances_path.write_text(
        json.dumps(matching_tolerances),
        encoding="utf-8",
    )

    ranking_path = tmp_path / "candidate_rankings.csv"
    robustness_path = tmp_path / "ranking_robustness.json"

    exit_code = main([
        "--fingerprints", str(fingerprints_path),
        "--target-site-id", "MOON_SITE04",
        "--candidate-site-ids", "EARTH_A",
        "--tolerances-json", str(tolerances_path),
        "--min-feature-group-completeness", "0.0",
        "--min-data-completeness", "0.0",
        "--output", str(ranking_path),
        "--robustness-output", str(robustness_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Ranked Earth candidates: 1" in captured.out
    assert ranking_path.is_file()
    assert robustness_path.is_file()


def test_cli_returns_error_for_unfilled_tolerance_template(
    tmp_path, target_fingerprint, earth_candidate, capsys
):
    candidate = dict(earth_candidate)
    candidate["site_id"] = "EARTH_A"
    candidate["source_id"] = "DEM_EARTH_A"

    fingerprints_path = tmp_path / "terrain_fingerprints.csv"
    rows = [target_fingerprint, candidate]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with fingerprints_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    tolerances_path = tmp_path / "template.json"
    tolerances_path.write_text(
        json.dumps({
            "slope_deg": None,
            "tri_m": None,
            "local_relief_m": None,
            "terrain_distribution_pp": None,
            "spatial_pattern_pct": None,
        }),
        encoding="utf-8",
    )

    exit_code = main([
        "--fingerprints", str(fingerprints_path),
        "--target-site-id", "MOON_SITE04",
        "--candidate-site-ids", "EARTH_A",
        "--tolerances-json", str(tolerances_path),
        "--min-feature-group-completeness", "0.0",
        "--min-data-completeness", "0.0",
    ])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Tolerance" in captured.err



def test_cli_requires_explicit_completeness_policy():
    parser = build_parser()
    with pytest.raises(SystemExit) as error:
        parser.parse_args([
            "--target-site-id", "MOON_SITE04",
            "--candidate-site-ids", "EARTH_A",
            "--tolerances-json", "config/matching_tolerances.json",
        ])
    assert error.value.code == 2
