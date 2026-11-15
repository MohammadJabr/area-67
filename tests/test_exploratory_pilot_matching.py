from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.matching.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_site01_exploratory_pilot_matching_is_reproducible(tmp_path: Path) -> None:
    """Run the committed pilot through Omar's CLI without overwriting app outputs."""
    rankings_path = tmp_path / "pilot_rankings.csv"
    robustness_path = tmp_path / "pilot_robustness.json"

    exit_code = main(
        [
            "--fingerprints",
            str(ROOT / "data/processed/terrain_fingerprints.csv"),
            "--target-site-id",
            "MOON_SITE01_PILOT990",
            "--candidate-site-ids",
            "EARTH_HAUGHTON_REF990",
            "EARTH_YUNGAY_HYPERARID_REF990",
            "EARTH_MAUNAKEA_REF990",
            "--tolerances-json",
            str(ROOT / "config/matching_tolerances.exploratory.json"),
            "--min-feature-group-completeness",
            "1.0",
            "--min-data-completeness",
            "0.95",
            "--output",
            str(rankings_path),
            "--robustness-output",
            str(robustness_path),
        ]
    )

    assert exit_code == 0
    assert rankings_path.is_file()
    assert robustness_path.is_file()

    rankings = pd.read_csv(rankings_path)
    assert len(rankings) == 3
    assert rankings["target_site_id"].nunique() == 1
    assert rankings["target_site_id"].iloc[0] == "MOON_SITE01_PILOT990"
    assert set(rankings["candidate_site_id"]) == {
        "EARTH_HAUGHTON_REF990",
        "EARTH_YUNGAY_HYPERARID_REF990",
        "EARTH_MAUNAKEA_REF990",
    }
    assert sorted(rankings["rank"].tolist()) == [1, 2, 3]

    robustness = json.loads(robustness_path.read_text(encoding="utf-8"))
    assert robustness["target_site_id"] == "MOON_SITE01_PILOT990"
    assert robustness["mission_profile"] == "Rover Navigation / Terrain Traversal"
    assert robustness["matching_configuration"]["min_feature_group_completeness"] == 1.0
    assert robustness["matching_configuration"]["min_data_completeness"] == 0.95
    assert len(robustness["slope_only_baseline"]["ranking"]) == 3
    assert robustness["tolerance_sensitivity"]["scenario_count"] == 11
    assert robustness["tolerance_sensitivity"]["factors"] == [0.5, 1.0, 1.5]
    assert len(robustness["tolerance_sensitivity"]["scenario_rankings"]) == 11
    assert "rejected_candidates_by_scenario" in robustness["tolerance_sensitivity"]
    assert robustness["candidate_site_ids"] == [
        "EARTH_HAUGHTON_REF990",
        "EARTH_MAUNAKEA_REF990",
        "EARTH_YUNGAY_HYPERARID_REF990",
    ]
    assert robustness["run_provenance"]["fingerprint_input"]["sha256"]
    assert robustness["run_provenance"]["matching_configuration"]["sha256"]
