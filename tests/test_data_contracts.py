from pathlib import Path

import pandas as pd

from src.data.contracts import (
    FINGERPRINT_REQUIRED_COLUMNS,
    RANKING_REQUIRED_COLUMNS,
    validate_fingerprints,
    validate_rankings,
)
from src.reporting.passport import build_passport, passport_to_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_demo_files_match_integration_contract():
    fingerprints = pd.read_csv(ROOT / "data/sample/demo_terrain_fingerprints.csv")
    rankings = pd.read_csv(ROOT / "data/sample/demo_candidate_rankings.csv")
    assert not validate_fingerprints(fingerprints)
    assert not validate_rankings(rankings)
    assert set(FINGERPRINT_REQUIRED_COLUMNS).issubset(fingerprints.columns)
    assert set(RANKING_REQUIRED_COLUMNS).issubset(rankings.columns)


def test_fingerprint_validation_reports_missing_columns():
    errors = validate_fingerprints(pd.DataFrame({"site_id": ["x"]}))
    assert any("Missing required column: slope_median" in error for error in errors)


def test_passport_does_not_invent_missing_values():
    passport = build_passport(
        {"site_id": "X", "planet": "Moon", "source_id": "SRC"}
    )
    text = passport_to_markdown(passport)
    assert "Slope distribution" in text
    assert "Measurement not supplied." in text
    assert "Not provided" in text
    assert "probability of mission success" in text


def test_passport_preserves_matcher_reported_differences_only():
    comparison = {
        "target_site_id": "MOON_X",
        "candidate_site_id": "EARTH_Y",
        "mission_profile": "Rover navigation",
        "target_features": {"slope_median": 12.0},
        "candidate_features": {"slope_median": 13.5},
        "reported_differences": {"slope_difference": 1.5},
    }
    passport = build_passport(
        {"site_id": "EARTH_Y", "planet": "Earth", "source_id": "SRC"},
        {"rank": 1, "similarity_score": 0.8},
        comparison=comparison,
    )
    text = passport_to_markdown(passport)
    assert "Target-to-candidate comparison" in text
    assert "slope_difference" in text
    assert "1.5" in text


def test_passport_marks_unreported_differences_as_not_supplied():
    passport = build_passport(
        {"site_id": "EARTH_Y", "planet": "Earth", "source_id": "SRC"},
        comparison={
            "target_site_id": "MOON_X",
            "candidate_site_id": "EARTH_Y",
            "mission_profile": "Rover navigation",
            "target_features": {"slope_median": 12.0},
            "candidate_features": {"slope_median": 13.5},
            "reported_differences": {},
        },
    )
    text = passport_to_markdown(passport)
    assert "Matcher-reported differences" in text
    assert "Not supplied by the upstream analysis." in text
