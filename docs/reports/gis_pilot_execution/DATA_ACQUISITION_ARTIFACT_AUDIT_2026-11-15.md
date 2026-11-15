# GIS acquisition artifact audit — 2026-11-15

**Purpose:** Record a read-only inspection of the raw Earth and lunar rasters produced by GitHub Actions run [#43700032212](https://github.com/MohammadJabr/area-67/actions/runs/43700032212). This report is an acquisition and structural inventory, not AOI approval, terrain fingerprinting, or scientific validation.

## Run and artifact provenance

- Workflow run: 43700032212 — AREA 67 GIS data acquisition and audit.
- Acquired from repository commit: d8d81d1 was not the run commit; the actual run commit was ccfe1cfb5d9667c0919b5f237a199ecae44e69b6.
- Artifact: area67-gis-both-43700032212.zip, artifact ID 14156191503.
- Artifact size: 405,027,240 bytes (15 GeoTIFF files).
- Artifact expiry at capture: 2026-11-29 09:39:50 UTC.
- Acquisition outcomes: Earth success; Moon Site01/Site04 success; optional ROI acquisition skipped because include_rois=false.
- The archive contains five Earth GLO-30 DSM tiles and ten lunar LOLA GeoTIFF layers. It contains no ROI shapefiles/archives and no processed fingerprints or rankings.

The artifact was inspected in place using GDAL/Rasterio 1.5.0 and NumPy 2.3.5. All 15 TIFFs were opened and read block-wise. The inspection recorded dimensions, CRS, affine transform, bounds, NoData/mask, finite-value counts, descriptive value ranges, and SHA-256 hashes. No raster was modified, resampled, clipped, reprojected, or copied into Git.

## Earth source rasters

All five tiles are single-band Float32 GeoTIFFs in EPSG:4326. Every cell is finite and mask-valid in the downloaded source tile. The exact SHA-256 values match the existing data/metadata/earth_dem_manifest.csv.

| Candidate tile | Grid (columns × rows) | Finite/mask-valid cells | SHA-256 |
|---|---:|---:|---|
| Haughton | 1200 × 3600 | 100.000% | 6731d23cff09f4cb7d2c72ec1d41c7ae9b6389565434e820692e08c2a4bcefa7 |
| McMurdo | 1200 × 3600 | 100.000% | dae6c48d7642f87b5b9fc24df4dcd39847b8e991f3d5c99e83365549d87fa138 |
| Askja | 1800 × 3600 | 100.000% | 1c663c1b6c3263c763ee40e5e20b85dfacdfeddaf3c41acb6b60cac8581cd56e |
| Mauna Kea | 3600 × 3600 | 100.000% | a1881be4ef3710ebf3d0e59a7a22e77ca79e2a6a3f51cdbadb74209e0698e00d |
| Yungay | 3600 × 3600 | 100.000% | ac7b8fce2e8598c5d522fd0f6ff0b4a1ae6f6c5aecda55671fc6e2bd82ec7710 |

Interpretation limits:

- These are broad source tiles, not candidate AOI polygons or analysis-ready rasters.
- 100% finite/mask-valid coverage describes the delivered tile's raster mask only; it does not establish elevation accuracy, effective resolution, landform suitability, or AOI coverage.
- The tiles are DSMs. Per-pixel quality/uncertainty companions were not included in this acquisition.
- Product-level EGM2008/metre documentation does not replace per-tile metadata or an approved cross-source vertical-processing policy.

## Lunar LOLA source rasters

Site01 and Site04 each contain five single-band Float32 layers: surface elevation, LDEC shot counts, slope, total-elevation RMS uncertainty, and slope RMS uncertainty.

For each site, all five rasters are 3200 × 3200 and have exactly matching CRS WKT, affine transform, bounds, and raster dimensions. All 10,240,000 cells per layer are finite and mask-valid. The nominal grid posting is 5 m; it is not a demonstrated 5 m effective terrain resolution.

| Site | Affine transform (a, b, c, d, e, f) | Bounds (m) | Positive LDEC cells | Zero LDEC cells | Positive support |
|---|---|---|---:|---:|---:|
| Site01 | [5, 0, -19000, 0, -5, -4000] | X [-19000, -3000], Y [-20000, -4000] | 972,204 | 9,267,796 | 9.4942% |
| Site04 | [5, 0, -9000, 0, -5, 1000] | X [-9000, 7000], Y [-15000, 1000] | 937,381 | 9,302,619 | 9.1541% |

The remaining LDEC cells are zero-count/interpolated LDEM support, not NoData. Both sites have 100% raster-valid masks while only about 9–9.5% of cells have positive shot counts. These are distinct measures and must remain separate in all downstream quality reporting.

The embedded lunar WKT for both sites declares an unknown datum. It is a south-polar stereographic grid in metres, but this artifact alone does not resolve the Moon-fixed frame identity. Do not infer or relabel the datum from projection parameters.

### Lunar file checksums

| Site / layer | SHA-256 |
|---|---|
| Site01 elevation | 3ba7b97cb00a2bcf21189c3aeb535f65afc21207154ab9f0d43c5bdc1f7e747e |
| Site01 LDEC | 16d6ed21020ad48fa71d94e7437492acf5bf04118f52bcd292f57f22ead4cd23 |
| Site01 slope | 3a90035a4946b4a04b7332c52f0b2b1cff71648bd8c105e14d8a7e15c6bcfe8e |
| Site01 Z RMS uncertainty | cf2cf52f52d2aa51e60d058010d10b0ebfb1d3e920f5a2b9a46eb6c51054ab1c |
| Site01 slope RMS uncertainty | 52bc3b239f61605e6bb98bab6d6b17acd22389c59e57336862157f2fbd643a33 |
| Site04 elevation | 38ff70dbdf2f066c2cfa94a646c3a59d653ce7f6b4528b15fc1b43ee397ce758 |
| Site04 LDEC | fcc8c2219ae2368d5b2a1f6aec05fcf96cf725f3035ac8d80efc312a4ff29227 |
| Site04 slope | ec3cfa184b114d95aff498e7452764a8569737ae829e7ff3efd38d5187182579 |
| Site04 Z RMS uncertainty | 416c4baa3b64def0182bb3379a1a9228482efd8ce32a39309ea8de5d0330fbe6 |
| Site04 slope RMS uncertainty | 067cd4d8e3e8c14a9a5be1915242532f85063f1b300f248407cc8c8b68e90695 |

## Workflow failure diagnosis and subsequent fix

The acquisition steps in run #43700032212 both completed successfully. The job failed later in python -m src.data.ci_gis_audit when json.dumps(report, allow_nan=False) encountered a non-finite NaN value in raster metadata. This was a report-serialization defect, not a failed Earth or LOLA download. The targeted GIS test step still completed with 80 passed, 71 warnings.

The defect was fixed on current main in commit d8d81d1b35ddcd55e1e0d2bf78e5a063ea14c14d: src/data/ci_gis_audit.py now recursively converts non-finite numeric metadata to JSON null, with a regression test in tests/test_ci_gis_audit.py.

Current-main verification at that commit:

- GitHub Actions full test suite: 202 passed, 491 warnings.
- python -m compileall -q src tests: passed.
- Geospatial artifact ignore-policy check: passed.

The fixed project audit has not yet been rerun against this acquired raw-data artifact. The independent inspection in this report confirms that all 15 TIFFs are readable and records their grid/mask/checksum properties; it does not replace a fresh run of the project's own audit on the fixed commit.

## Remaining gates

1. Re-run the GIS acquisition/audit workflow from current main after the JSON-safety fix, retaining separate compact QA reports.
2. Acquire/inspect official Site01 and Site04 ROI archives; this run skipped that optional step.
3. Confirm lunar frame provenance and the A306/Site01 grid/ROI compatibility before using provider polygons.
4. Approve actual lunar and Earth study AOIs with stable IDs; no source tile or provider ROI is automatically an AREA 67 AOI.
5. Agree the projected metric analysis grid, physical scale, neighborhood windows, vertical-reference policy, mask/uncertainty treatment, and candidate source set.
6. Only then prepare analysis-ready rasters, run five-group fingerprints, configure approved matching tolerances/completeness cutoffs, and produce real rankings.

No terrain fingerprint, Earth–Moon similarity score, candidate ranking, rover route, or permanent-base recommendation was produced by this acquisition or audit.
