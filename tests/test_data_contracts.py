from pathlib import Path

import pandas as pd

from src.data.contracts import (
    FINGERPRINT_REQUIRED_COLUMNS,
    RANKING_REQUIRED_COLUMNS,
    fingerprint_quality_warnings,
    validate_fingerprints,
    validate_ranking_references,
    validate_rankings,
    validate_space_to_earth,
)
from src.reporting.passport import build_passport, passport_to_markdown

ROOT = Path(__file__).resolve().parents[1]


def load_demo_data():
    fingerprints = pd.read_csv(ROOT / "data/sample/demo_terrain_fingerprints.csv")
    rankings = pd.read_csv(ROOT / "data/sample/demo_candidate_rankings.csv")
    return fingerprints, rankings


def test_demo_files_match_integration_contract():
    fingerprints, rankings = load_demo_data()
    assert not validate_fingerprints(fingerprints)
    assert not validate_rankings(rankings)
    assert set(FINGERPRINT_REQUIRED_COLUMNS).issubset(fingerprints.columns)
    assert set(RANKING_REQUIRED_COLUMNS).issubset(rankings.columns)


def test_fingerprint_validation_reports_missing_columns():
    errors = validate_fingerprints(pd.DataFrame({"site_id": ["x"]}))
    assert any("Missing required column: slope_median" in error for error in errors)


def test_fingerprint_validation_rejects_invalid_scales_percentages_and_slope_order():
    fingerprints, _ = load_demo_data()
    fingerprints.loc[0, "analysis_scale_m"] = 0
    fingerprints.loc[0, "terrain_flat_pct"] = 120
    fingerprints.loc[0, "slope_p90"] = 1
    errors = validate_fingerprints(fingerprints)
    assert any("analysis_scale_m must be greater than zero" in error for error in errors)
    assert any("terrain_flat_pct must be between 0 and 100" in error for error in errors)
    assert any("slope_p90 must be greater than or equal to slope_median" in error for error in errors)


def test_ranking_validation_rejects_duplicate_site_profile_and_rank_rows():
    _, rankings = load_demo_data()
    duplicate = rankings.iloc[[0]].copy()
    invalid = pd.concat([rankings, duplicate], ignore_index=True)
    errors = validate_rankings(invalid)
    assert any("target/candidate/mission_profile" in error for error in errors)
    assert any("Ranks must be unique" in error for error in errors)


def test_ranking_references_must_exist_in_fingerprint_table():
    fingerprints, rankings = load_demo_data()
    rankings.loc[0, "candidate_site_id"] = "NOT_IN_FINGERPRINTS"
    errors = validate_ranking_references(fingerprints, rankings)
    assert any("candidate_site_id values absent" in error for error in errors)


def test_active_mvp_requires_moon_or_mars_target_and_earth_candidates():
    fingerprints, rankings = load_demo_data()
    fingerprints.loc[
        fingerprints["site_id"] == "EARTH_DEMO_01", "planet"
    ] = "Mars"
    errors = validate_space_to_earth(fingerprints, rankings)
    assert any("must be an Earth site" in error for error in errors)


def test_quality_audit_reports_absent_method_metadata():
    fingerprints, _ = load_demo_data()
    warnings = fingerprint_quality_warnings(fingerprints)
    assert any("tri_definition" in warning for warning in warnings)


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
