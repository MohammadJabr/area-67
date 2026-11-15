import io
import json
import zipfile

from src.reporting.evidence_bundle import build_evidence_bundle


def test_evidence_bundle_contains_traceable_payloads_and_no_raw_rasters():
    passport = {
        "identity": {"site_id": "EARTH_TEST", "site_name": "Test site"},
        "provenance": {"source_id": "TEST_DEM", "aoi_approval": "NOT_APPROVED"},
    }
    fingerprint = {
        "site_id": "EARTH_TEST",
        "site_name": "Test site",
        "scientific_status": "EXPLORATORY_NOT_APPROVED",
        "slope_median": 4.2,
    }
    ranking = {
        "candidate_site_id": "EARTH_TEST",
        "rank": 1,
        "similarity_score": 61.2,
    }

    payload = build_evidence_bundle(
        passport=passport,
        fingerprint_row=fingerprint,
        ranking_row=ranking,
        passport_markdown="# Test passport\n\nEXPLORATORY",
        demo_mode=False,
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        assert names == {
            "README.txt",
            "analog_passport.md",
            "analog_passport.json",
            "site_terrain_fingerprint.csv",
            "matching_result.csv",
        }
        exported_passport = json.loads(archive.read("analog_passport.json"))
        assert exported_passport["identity"]["site_id"] == "EARTH_TEST"
        assert "EXPLORATORY" in archive.read("analog_passport.md").decode("utf-8")
        assert "not included" in archive.read("README.txt").decode("utf-8")
        assert "site_terrain_fingerprint.csv" in names
        assert not any(name.endswith((".tif", ".tiff", ".img")) for name in names)


def test_evidence_bundle_discloses_synthetic_demo_mode():
    payload = build_evidence_bundle(
        passport={"identity": {"site_id": "DEMO"}},
        fingerprint_row={"site_id": "DEMO"},
        ranking_row=None,
        passport_markdown="# Demo",
        demo_mode=True,
    )
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        readme = archive.read("README.txt").decode("utf-8")
        assert "YES" in readme
        assert "synthetic fixtures" in readme
        assert archive.read("matching_result.csv").decode("utf-8") == ""
