from src.matching.baseline import compare_slope_only_baseline


def test_slope_only_baseline_reports_rank_changes():
    matching_result = {
        "target_site_id": "MOON_SITE04",
        "ranking": [
            {
                "site_id": "EARTH_A",
                "rank": 1,
                "group_distances": {"slope": 0.7},
            },
            {
                "site_id": "EARTH_B",
                "rank": 2,
                "group_distances": {"slope": 0.1},
            },
            {
                "site_id": "EARTH_C",
                "rank": 3,
                "group_distances": {"slope": 0.4},
            },
        ],
    }

    result = compare_slope_only_baseline(matching_result)

    assert [item["site_id"] for item in result["slope_only_ranking"]] == [
        "EARTH_B",
        "EARTH_C",
        "EARTH_A",
    ]
    changes = {
        item["site_id"]: item["rank_change_vs_slope_only"]
        for item in result["rank_comparison"]
    }
    assert changes == {"EARTH_A": -2, "EARTH_B": 1, "EARTH_C": 1}
