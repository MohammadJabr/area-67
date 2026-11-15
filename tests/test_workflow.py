import csv
import json

import pandas as pd
import pytest

from src.data.contracts import (
    normalize_rankings,
    validate_fingerprints,
    validate_ranking_references,
    validate_rankings,
    validate_space_to_earth,
)
from src.matching.mission_profiles import (
    ROVER_NAVIGATION_PROFILE,
    get_mission_weights,
)
from src.matching.workflow import run_matching_from_csv


def _write_fingerprint_csv(path, rows):
    fieldnames = list(dict.fromkeys(
        field for row in rows for field in row
    ))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_workflow_reads_fingerprints_and_exports_results(
    tmp_path, target_fingerprint, earth_candidate, matching_tolerances
):
    candidate_a = dict(earth_candidate)
    candidate_a["site_id"] = "EARTH_A"
    candidate_a["source_id"] = "DEM_A"

    candidate_b = dict(earth_candidate)
    candidate_b.update({
        "site_id": "EARTH_B",
        "source_id": "DEM_B",
        "slope_median": 18.0,
        "slope_p90": 28.0,
        "tri_median": 4.0,
        "tri_p90": 7.0,
        "local_relief_p95_p5": 45.0,
        "terrain_low_pct": 10.0,
        "terrain_mid_pct": 40.0,
        "terrain_high_pct": 50.0,
        "largest_steep_patch_pct": 30.0,
    })

    held_out = dict(candidate_b)
    held_out.update({"site_id": "EARTH_HELD_OUT", "source_id": "DEM_HELD_OUT"})

    fingerprints_path = tmp_path / "terrain_fingerprints.csv"
    _write_fingerprint_csv(
        fingerprints_path,
        [target_fingerprint, candidate_a, candidate_b, held_out],
    )

    ranking_path = tmp_path / "candidate_rankings.csv"
    robustness_path = tmp_path / "ranking_robustness.json"

    result = run_matching_from_csv(
        fingerprints_path,
        "MOON_SITE04",
        get_mission_weights(),
        matching_tolerances,
        candidate_site_ids=["EARTH_A", "EARTH_B"],
        mission_profile=ROVER_NAVIGATION_PROFILE["name"],
        min_feature_group_completeness=0.0,
        min_data_completeness=0.0,
        ranking_output_path=ranking_path,
        robustness_output_path=robustness_path,
    )

    assert ranking_path.is_file()
    assert robustness_path.is_file()
    assert [row["site_id"] for row in result["ranking_result"]["ranking"]] == [
        "EARTH_A",
        "EARTH_B",
    ]

    with ranking_path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        exported = list(reader)
        assert "target_site_id" in reader.fieldnames
        assert "candidate_site_id" in reader.fieldnames
        assert "similarity_score" in reader.fieldnames
        assert "weighted_distance" in reader.fieldnames
        assert "ranking_stability_note" in reader.fieldnames

    assert exported[0]["target_site_id"] == "MOON_SITE04"
    assert exported[0]["candidate_site_id"] == "EARTH_A"
    assert "Top-3 in" in exported[0]["ranking_stability_note"]
    assert exported[0]["slope_only_rank"] != ""

    # Check the files against the application's actual contract validators.
    fingerprint_frame = pd.read_csv(fingerprints_path)
    ranking_frame = normalize_rankings(pd.read_csv(ranking_path))
    contract_errors = (
        validate_fingerprints(fingerprint_frame)
        + validate_rankings(ranking_frame)
        + validate_ranking_references(fingerprint_frame, ranking_frame)
        + validate_space_to_earth(fingerprint_frame, ranking_frame)
    )
    assert contract_errors == []

    summary = json.loads(robustness_path.read_text(encoding="utf-8"))
    assert summary["sensitivity"]["scenario_count"] == 11
    assert summary["matching_configuration"] == {
        "min_feature_group_completeness": 0.0,
        "min_data_completeness": 0.0,
        "scale_relative_tolerance": 0.01,
        "distribution_sum_tolerance_pp": 0.5,
        "weight_relative_change": 0.2,
        "top_k": [3, 5],
    }
    assert "slope_only_baseline" in summary
    assert summary["candidate_site_ids"] == ["EARTH_A", "EARTH_B"]
    assert "EARTH_HELD_OUT" not in {
        row["site_id"] for row in result["ranking_result"]["ranking"]
    }



def test_workflow_refuses_to_run_without_explicit_completeness_policy(
    target_fingerprint, earth_candidate, matching_tolerances
):
    from src.matching.workflow import run_matching_workflow

    candidate = dict(earth_candidate)
    candidate["site_id"] = "EARTH_A"
    candidate["source_id"] = "DEM_A"

    with pytest.raises(ValueError, match="explicit completeness policy"):
        run_matching_workflow(
            target_fingerprint,
            {"EARTH_A": candidate},
            get_mission_weights(),
            matching_tolerances,
            mission_profile=ROVER_NAVIGATION_PROFILE["name"],
        )
