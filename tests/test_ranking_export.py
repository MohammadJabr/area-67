import csv

import pytest

from src.matching.ranking import rank_candidates
from src.reporting.ranking_export import (
    OUTPUT_COLUMNS,
    export_rankings_csv,
)


def test_exported_rankings_use_canonical_application_fields(tmp_path):
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
        reader = csv.DictReader(file)
        rows = list(reader)
        assert reader.fieldnames == OUTPUT_COLUMNS

    assert len(rows) == 2
    assert {row["target_site_id"] for row in rows} == {"MOON_SITE04"}
    assert {row["candidate_site_id"] for row in rows} == {"EARTH_A", "EARTH_B"}
    assert rows[0]["mission_profile"] == "Rover Navigation / Terrain Traversal"
    assert rows[0]["rank"] == "1"
    assert float(rows[0]["similarity_score"]) > 0
    assert float(rows[0]["weighted_distance"]) >= 0
    assert "not a probability" in rows[0]["ranking_note"]


def test_export_rejects_rankings_without_target_site_id(tmp_path):
    with pytest.raises(ValueError, match="target_site_id"):
        export_rankings_csv(
            ranking_result={"ranking": []},
            mission_profile="Rover Navigation / Terrain Traversal",
            output_path=tmp_path / "candidate_rankings.csv",
        )


def test_export_rejects_invalid_completeness(tmp_path):
    result = {
        "target_site_id": "MOON_SITE04",
        "ranking": [{
            "site_id": "EARTH_A",
            "rank": 1,
            "similarity_distance": 0.5,
            "data_completeness": 1.5,
            "group_contributions": {},
        }],
    }
    with pytest.raises(ValueError, match="data_completeness"):
        export_rankings_csv(
            result,
            "Rover Navigation",
            tmp_path / "candidate_rankings.csv",
        )
