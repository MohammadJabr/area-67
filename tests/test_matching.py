
import math

from src.matching.similarity import weighted_similarity_distance
from src.matching.ranking import rank_candidates


def test_weighted_similarity_distance():
    result = weighted_similarity_distance(
        group_distances={
            "slope": 2.0,
            "tri": 1.0,
        },
        weights={
            "slope": 0.6,
            "tri": 0.4,
        },
    )

    assert math.isclose(
        result["similarity_distance"],
        math.sqrt(2.8),
    )

    assert result["data_completeness"] == 1.0

    assert math.isclose(
        result["group_contributions"]["slope"]["distance_share"],
        6 / 7,
    )


def test_missing_data_is_not_treated_as_zero():
    result = weighted_similarity_distance(
        group_distances={
            "slope": 2.0,
            "tri": None,
        },
        weights={
            "slope": 0.6,
            "tri": 0.4,
        },
        min_completeness=0.5,
    )

    assert result["similarity_distance"] == 2.0
    assert math.isclose(result["data_completeness"], 0.6)
    assert "tri" in result["missing_groups"]


def test_candidates_are_ranked_correctly():
    candidates = {
        "Site_A": {"slope": 0.2, "tri": 0.3},
        "Site_B": {"slope": 0.5, "tri": 0.6},
        "Site_C": {"slope": 0.1, "tri": 0.2},
    }

    weights = {
        "slope": 0.5,
        "tri": 0.5,
    }

    result = rank_candidates(
        candidates,
        weights,
        target_site_id="MOON_SITE04",
    )

    ranking = result["ranking"]

    assert [site["site_id"] for site in ranking] == [
        "Site_C",
        "Site_A",
        "Site_B",
    ]

    assert [site["rank"] for site in ranking] == [1, 2, 3]

    assert result["target_site_id"] == "MOON_SITE04"
    assert result["rejected_candidates"] == []
