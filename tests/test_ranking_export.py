import csv

import pytest

from src.matching.ranking import rank_candidates
from src.reporting.ranking_export import export_rankings_csv


def test_exported_rankings_include_target_site_id(tmp_path):
    result = rank_candidates(
        candidates={
            "EARTH_A": {"slope": 0.2, "tri": 0.3},
            "EARTH_B": {"slope": 0.5, "tri": 0.6},
        },
        weights={"slope": 0.6, "tri": 0.4},
        target_site_id="MOON_SITE04",
    )

    output = export_rankings_csv(
        ranking_result=result,
        mission_profile="Rover Navigation / Terrain Traversal",
        output_path=tmp_path / "candidate_rankings.csv",
        ranking_stability_note="Synthetic unit-test fixture only.",
    )

    with output.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2
    assert {row["target_site_id"] for row in rows} == {"MOON_SITE04"}
    assert {row["site_id"] for row in rows} == {"EARTH_A", "EARTH_B"}
    assert rows[0]["mission_profile"] == "Rover Navigation / Terrain Traversal"
    assert rows[0]["rank"] == "1"


def test_export_rejects_rankings_without_target_site_id(tmp_path):
    with pytest.raises(ValueError, match="target_site_id"):
        export_rankings_csv(
            ranking_result={"ranking": []},
            mission_profile="Rover Navigation / Terrain Traversal",
            output_path=tmp_path / "candidate_rankings.csv",
        )
