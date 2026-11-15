import csv
import json
from pathlib import Path

import pytest

from src.data.package_reduced_mvp import package_reduced_mvp


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def inputs(tmp_path: Path):
    fingerprints = tmp_path / "fingerprints.csv"
    rankings = tmp_path / "rankings.csv"
    robustness = tmp_path / "robustness.json"
    candidates = ["EARTH_HAUGHTON_REF990", "EARTH_YUNGAY_HYPERARID_REF990", "EARTH_MAUNAKEA_REF990"]
    write_csv(
        fingerprints,
        ["site_id", "planet", "site_name", "slope_median", "slope_p90"],
        [{"site_id": "MOON_SITE01_PILOT990", "planet": "Moon", "site_name": "Site01"}]
        + [{"site_id": site, "planet": "Earth", "site_name": site, "slope_median": 1, "slope_p90": 2} for site in candidates],
    )
    write_csv(
        rankings,
        ["target_site_id", "candidate_site_id", "rank"],
        [{"target_site_id": "MOON_SITE01_PILOT990", "candidate_site_id": site, "rank": i} for i, site in enumerate(candidates, 1)],
    )
    robustness.write_text(json.dumps({
        "status": "EXPLORATORY_NOT_APPROVED",
        "target_site_id": "MOON_SITE01_PILOT990",
        "mission_profile": "Rover Navigation / Terrain Traversal",
        "scope": {"candidate_windows": candidates},
        "slope_only_baseline": [
            {"site_id": site, "rank": i, "similarity_distance": 0.5 * i, "similarity_score": 100 / (1 + 0.5 * i)}
            for i, site in enumerate(candidates, 1)
        ],
    }), encoding="utf-8")
    return fingerprints, rankings, robustness, candidates


def test_package_uses_canonical_slope_only_baseline_and_preserves_fingerprints(tmp_path):
    fingerprints, rankings, robustness, candidates = inputs(tmp_path)
    output = tmp_path / "reduced"

    result = package_reduced_mvp(fingerprints, rankings, robustness, output)

    with (output / "terrain_fingerprints.csv").open(newline="", encoding="utf-8") as stream:
        fingerprint_rows = list(csv.DictReader(stream))
    with (output / "candidate_rankings.csv").open(newline="", encoding="utf-8") as stream:
        ranking_rows = list(csv.DictReader(stream))
    assert len(fingerprint_rows) == 4
    assert [row["candidate_site_id"] for row in ranking_rows] == candidates
    assert [row["similarity_score"] for row in ranking_rows] == [str(100 / (1 + 0.5 * i)) for i in range(1, 4)]
    assert all("Slope P50 and P90 only" in row["ranking_basis"] for row in ranking_rows)
    assert result["candidate_site_ids"] == candidates
    assert (output / "package_manifest.json").is_file()


def test_package_does_not_overwrite_existing_output(tmp_path):
    fingerprints, rankings, robustness, _ = inputs(tmp_path)
    output = tmp_path / "reduced"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(FileExistsError, match="choose a new path"):
        package_reduced_mvp(fingerprints, rankings, robustness, output)
    assert marker.read_text(encoding="utf-8") == "preserve"


def test_package_rejects_candidate_mismatch(tmp_path):
    fingerprints, rankings, robustness, _ = inputs(tmp_path)
    data = json.loads(robustness.read_text(encoding="utf-8"))
    data["slope_only_baseline"].pop()
    robustness.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="wrong candidate count"):
        package_reduced_mvp(fingerprints, rankings, robustness, tmp_path / "reduced")
