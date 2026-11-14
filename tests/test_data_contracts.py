from pathlib import Path
import pandas as pd
from src.data.contracts import FINGERPRINT_REQUIRED_COLUMNS, RANKING_REQUIRED_COLUMNS, validate_fingerprints, validate_rankings
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
    passport = build_passport({"site_id": "X", "planet": "Moon", "source_id": "SRC"})
    text = passport_to_markdown(passport)
    assert "Slope distribution" in text
    assert "Measurement not supplied." in text
    assert "Not provided" in text
    assert "probability of mission success" in text
