import csv

import pytest

from src.data.fingerprint_loader import (
    load_terrain_fingerprints_csv,
    select_space_to_earth_fingerprints,
)


def test_loader_preserves_missing_values_and_parses_numeric_fields(tmp_path):
    source = tmp_path / "terrain_fingerprints.csv"
    source.write_text(
        "site_id,planet,analysis_scale_m,slope_median,nodata_pct,tri_window_cells\n"
        "MOON_A,Moon,20,12.5,0,1\n"
        "EARTH_A,Earth,20,,5,1\n",
        encoding="utf-8",
    )

    rows = load_terrain_fingerprints_csv(source)

    assert rows[0]["analysis_scale_m"] == 20.0
    assert rows[0]["tri_window_cells"] == 1
    assert rows[1]["slope_median"] is None
    assert rows[1]["nodata_pct"] == 5.0


def test_loader_rejects_non_finite_numeric_measurements(tmp_path):
    source = tmp_path / "terrain_fingerprints.csv"
    source.write_text(
        "site_id,planet,slope_median\nMOON_A,Moon,inf\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be finite"):
        load_terrain_fingerprints_csv(source)


def test_loader_rejects_duplicate_site_ids(tmp_path):
    source = tmp_path / "terrain_fingerprints.csv"
    source.write_text(
        "site_id,planet\nMOON_A,Moon\nMOON_A,Moon\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate site_id"):
        load_terrain_fingerprints_csv(source)


def test_space_to_earth_selector_returns_target_and_only_earth_candidates():
    rows = [
        {"site_id": "MOON_A", "planet": "Moon"},
        {"site_id": "EARTH_A", "planet": "Earth"},
        {"site_id": "EARTH_B", "planet": "Earth"},
        {"site_id": "MARS_OTHER", "planet": "Mars"},
    ]

    target, candidates = select_space_to_earth_fingerprints(rows, "MOON_A")

    assert target["site_id"] == "MOON_A"
    assert set(candidates) == {"EARTH_A", "EARTH_B"}


def test_space_to_earth_selector_rejects_earth_target():
    rows = [
        {"site_id": "EARTH_TARGET", "planet": "Earth"},
        {"site_id": "EARTH_CANDIDATE", "planet": "Earth"},
    ]

    with pytest.raises(ValueError, match="Moon or Mars"):
        select_space_to_earth_fingerprints(rows, "EARTH_TARGET")
