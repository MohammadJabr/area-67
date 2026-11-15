from src.reporting.passport import build_passport, passport_to_markdown


def test_exploratory_lunar_passport_includes_aoi_and_direct_support_caveats():
    row = {
        "site_id": "MOON_SITE01_PILOT990",
        "site_name": "NASA LOLA Site01 / Connecting Ridge",
        "planet": "Moon",
        "source_id": "NASA_PGDA_LOLA_Site01_final_adj_5mpp_surf",
        "source_name": "NASA PGDA LOLA Site01",
        "product_version": "Site01_final_adj_5mpp",
        "access_date": "2026-11-15",
        "crs": "Custom south polar stereographic",
        "vertical_reference": "Unknown in local WKT",
        "analysis_scale_m": 30.0,
        "nodata_pct": 0.0,
        "license": "NASA PGDA data terms",
        "scientific_status": "EXPLORATORY_NOT_APPROVED",
        "aoi_status": "PROVISIONAL_REFERENCE_WINDOW_NOT_APPROVED_AOI",
        "aoi_approval": "NOT_APPROVED",
        "aoi_note": "990m reference-centred sampling window; not an approved AOI.",
        "analysis_scale_status": "PROVISIONAL_30M_PILOT_ASSUMPTION",
        "relief_window_m": 150.0,
        "relief_window_cells": 5,
        "relief_window_span_m": 120.0,
        "direct_observation_coverage_pct": 9.235,
        "z_rms_median_m": 0.3379,
        "effective_resolution_note": "Product 90 EFFRES P90 24.08m.",
        "source_quality_note": "Local CRS datum label remains unknown.",
        "source_checksum_sha256": "3ba7b97cb00a2bcf21189c3aeb535f65afc21207154ab9f0d43c5bdc1f7e747e",
        "slope_median": 4.545,
        "slope_p90": 9.463,
        "tri_median": 6.069,
        "tri_p90": 12.279,
        "local_relief_p95_p5": 9.883,
        "terrain_low_pct": 93.34,
        "terrain_mid_pct": 6.66,
        "terrain_high_pct": 0.0,
        "largest_steep_patch_pct": 0.0,
    }
    passport = build_passport(row)
    report = passport_to_markdown(passport)

    assert "EXPLORATORY REAL-DATA PILOT" in report
    assert "AOI approval" in report
    assert "NOT_APPROVED" in report
    assert "Direct LOLA shot support (%)" in report
    assert "9.235" in report
    assert "centre-to-centre span (m)" in report
    assert "120.0" in report


def test_earth_passport_states_direct_observation_support_not_supplied():
    row = {
        "site_id": "EARTH_HAUGHTON_REF990",
        "site_name": "Haughton reference window",
        "planet": "Earth",
        "source_id": "Copernicus_GLO30_Haughton",
        "scientific_status": "EXPLORATORY_NOT_APPROVED",
        "aoi_approval": "NOT_APPROVED",
        "slope_median": 3.23,
        "slope_p90": 5.88,
        "tri_median": 4.33,
        "local_relief_p95_p5": 7.24,
    }
    report = passport_to_markdown(build_passport(row))
    assert "EXPLORATORY REAL-DATA PILOT" in report
    assert "Direct instrument-shot support: not supplied for this Earth DSM" in report
