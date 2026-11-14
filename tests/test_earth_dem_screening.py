import csv
import hashlib
import json

import numpy as np
import rasterio
from rasterio.transform import from_origin

from src.data.earth_dem_screening import inspect_candidates


def test_candidate_integrity_and_metadata_are_verified_read_only(tmp_path):
    raw = tmp_path / "raw" / "demo"
    qa_root = tmp_path / "qa"
    raw.mkdir(parents=True)
    qa_root.mkdir()
    tif = raw / "tile_demo.tif"
    with rasterio.open(
        tif, "w", driver="GTiff", width=2, height=2, count=1, dtype="float32",
        crs="EPSG:4326", transform=from_origin(-1, 2, 1, 1), nodata=-9999,
    ) as ds:
        ds.write(np.array([[1, 2], [3, -9999]], dtype="float32"), 1)
    digest = hashlib.sha256(tif.read_bytes()).hexdigest()
    row = {
        "site_id": "demo", "source_id": "tile_demo", "longitude": "-0.5", "latitude": "1.5",
        "checksum_sha256": digest, "crs": "EPSG:4326", "nodata_value": "-9999",
        "valid_cell_count": "3", "valid_coverage_pct": "75.0",
    }
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
    qa = {
        "status": "checks_passed",
        "dem": {
            "path": str(tif), "sha256": digest, "file_size_bytes": tif.stat().st_size,
            "crs": "EPSG:4326", "nodata": -9999,
            "width": 2, "height": 2, "band_count": 1,
            "transform": [1.0, 0.0, -1.0, 0.0, -1.0, 2.0],
            "bounds": [-1.0, 0.0, 1.0, 2.0],
            "bands": [{"statistics": {"valid_coverage_pct": 75.0, "valid_pixel_count": 3}}],
        },
    }
    (qa_root / "demo.json").write_text(json.dumps(qa), encoding="utf-8")
    (qa_root / "demo.md").write_text(f"**Status:** checks_passed\n`{digest}`", encoding="utf-8")

    result = inspect_candidates(manifest, tmp_path / "raw", qa_root)[0]

    assert result["findings"] == []
    assert result["sha256"] == digest
    assert result["qa_valid_coverage_pct"] == 75.0
    assert result["raster"]["valid_pixels"] == 3
    assert result["raster"]["site_pixel_value_m"] == 1
    assert tif.exists()  # Screening did not replace or remove the source.


def test_manifest_checksum_and_site_coordinate_problems_are_reported(tmp_path):
    raw = tmp_path / "raw" / "demo"
    qa_root = tmp_path / "qa"
    raw.mkdir(parents=True)
    qa_root.mkdir()
    tif = raw / "tile_demo.tif"
    with rasterio.open(
        tif, "w", driver="GTiff", width=2, height=2, count=1, dtype="float32",
        crs="EPSG:4326", transform=from_origin(-1, 2, 1, 1), nodata=-9999,
    ) as ds:
        ds.write(np.ones((2, 2), dtype="float32"), 1)
    row = {
        "site_id": "demo", "source_id": "tile_demo", "longitude": "10", "latitude": "10",
        "checksum_sha256": "bad", "crs": "EPSG:4326", "nodata_value": "-9999",
        "valid_cell_count": "4", "valid_coverage_pct": "100.0",
    }
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
    (qa_root / "demo.json").write_text("{}", encoding="utf-8")

    result = inspect_candidates(manifest, tmp_path / "raw", qa_root)[0]

    assert any("SHA-256" in finding for finding in result["findings"])
    assert any("outside the raster footprint" in finding for finding in result["findings"])
