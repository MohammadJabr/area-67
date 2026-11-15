# Hiba — Terrain Fingerprint Execution Readiness

**Owner:** Hiba Sbouh  
**Workstream:** Terrain Fingerprint · Statistics · Quality Validation  
**Assessment date:** 2026-11-15  
**Repository:** `MohammadJabr/area-67`

## Executive status

The software portion of Hiba's workstream is implemented and its tests pass in GitHub Actions. The calculation method, validation coverage, handoff schema, and execution checklist are documented in `docs/reports/hiba/`.

**The canonical scientific extraction is not yet runnable from the repository's approved inputs.** This is not a missing-code problem. The canonical run configuration is intentionally empty because the project has not approved the AOI geometries, lunar ROI physical frame, common metric grid, resampling/mask policy, and final analytical settings. Raw rasters and source metadata exist, but they are not the same as analysis-ready, co-registered DEM/AOI pairs.

This document is the practical status and next-action sheet for Hiba. It separates work already completed from the exact handoffs still needed.

## 1. Hiba's original MVP deliverables — status

| Deliverable in the 24-hour playbook | Current status | Evidence / next step |
|---|---|---|
| One lunar/Martian target and at least 3 Earth candidates | **Working scope selected** | Site01 / Connecting Ridge; Haughton, Askja, Mauna Kea. This is a sprint shortlist, not AOI approval. |
| Five terrain groups | **Implemented** | Slope, Riley TRI, Local Relief, Terrain Distribution, Spatial Pattern in `src/features/terrain_fingerprint.py`. |
| At least one documented indicator per group | **Implemented** | Definitions and exact summaries in the method report. |
| One row per stable site ID in fingerprint CSV | **Schema implemented; canonical file pending** | `docs/INTEGRATION_CONTRACT.md`; output is produced only after an approved real-data run. |
| Synthetic calculation tests | **Implemented; CI passed** | `tests/test_terrain_fingerprint.py`; latest dedicated Hiba handoff PR test and post-merge main test both passed. |
| Real DEM mask/scale/NoData inspection | **Source inventories and preflight tooling exist** | Earth GLO-30 and lunar LOLA source audits exist; analysis-ready common-grid inputs and AOIs remain pending. |
| Three or more candidate fingerprints | **Blocked on AOIs and common-grid inputs** | Do not use exploratory reference-centred pilot windows as approved landform AOIs. |
| Scale/window sensitivity | **Utilities and comparison function exist; canonical results pending** | Run at two approved scales only after valid inputs and settings exist. |
| Feature correlation / redundancy review | **Audit function exists; actual canonical sample too small/not run** | At least three comparable site rows are needed; explain Terrain Distribution's dependence on Slope. |
| Independent reference comparison | **Not completed** | Optional in the playbook; perform only if an independent suitable reference product exists for the same footprint and compatible scale. |
| Quality/uncertainty evidence | **Partial source audit exists; extractor propagation incomplete** | Preserve valid coverage, LOLA direct support (LDEC), Z RMS, slope RMS and effective-resolution notes separately. Per-pixel LOLA quality layers are not yet propagated through the fingerprint metrics. |
| Derived maps and handoff package | **Software supports maps; canonical maps pending** | GeoTIFF maps are written by the extractor after the canonical run. Method report and checklist are ready. |

## 2. What is already in the repository

### Code

- `src/features/terrain_fingerprint.py`
  - central-difference Slope in degrees (median, P90, P95);
  - Riley eight-neighbour TRI (median, P90);
  - moving-window local P95–P5 relief (median and P90 of the local-relief map);
  - low/mid/high slope-class percentages;
  - largest connected steep patch percentage with 4/8 connectivity;
  - GeoTIFF/AOI masking, metric-grid checks, NoData preservation and optional derived-map export.
- `src/features/validation.py`
  - fingerprint contract checks;
  - scale-run comparison;
  - descriptive Spearman correlation audit (requires at least 3 sites).
- `tests/test_terrain_fingerprint.py`
  - flat surface, analytic plane, bump, NoData, terrain distribution, spatial patches, scale mismatch, window rounding, schema, scale sensitivity, GeoTIFF/AOI, CRS, vertical-reference, integer DEM and run-config tests.
  - Additional invalid-config, map-NoData and class-contract tests were added in PR #103.

### Data evidence

- Earth GLO-30 DSM source tiles for Haughton, Askja, Mauna Kea, Yungay and McMurdo are inventoried with checksums. GLO-30 is a DSM; its local per-pixel quality companions are absent. Effective terrain resolution is not established.
- The Earth manifest records EGM2008 as product-level vertical reference, but the exact package release is not identified in the local tile filename/tags.
- A local USGS 3DEP 1 m Mauna Kea bare-earth tile is documented, but it uses EPSG:26904 / NAVD88 and lies about 150 m from the provisional point's east edge. It cannot be mixed with GLO-30 without an explicit source/grid/datum policy and complete footprint coverage.
- NASA PGDA Site01 and Site04 have five aligned native LOLA layers: elevation, LDEC counts, slope, Z RMS and slope RMS. Provider ROI support/uncertainty is audited. The raster GeoTIFF product is documented as MOON_ME / DE421, but the provider ROI shapefile frame remains unverified. Invalid polygons are not auto-repaired.
- Site01 Feature 4 is the current primary registration/quality review anchor and Feature 2 is the direct-support cross-check in the delegated baseline. Neither is approved as the final operations AOI. Feature numbers are 1-based in the report.

## 3. Exact blockers before canonical execution

These are hard gates, not optional polish:

1. **Earth AOIs:** Ghassan/team must supply source-backed geometries for Haughton, Askja and Mauna Kea, including source map/landform rationale, geometry validity, exclusions and coverage.
2. **Lunar target footprint:** Hiba + GIS owner must verify the ROI geometry frame and select a defensible Site01 footprint. Do not infer the shapefile frame from the raster CRS.
3. **Common analysis grid:** Ghassan + Hiba must specify the projected metric CRS, grid origin/alignment, target scale(s), resampling/aggregation by layer and NoData/mask rules.
4. **Vertical reference:** Document each source's vertical reference and any defensible transformation. Do not compare absolute Earth/Moon elevations or infer unknown datums.
5. **Quality policy:** Specify how LDEC, Z RMS and slope RMS are summarized and reported. LDEC-positive direct-shot support is not raster-valid coverage; RMS is not a safety threshold.
6. **Run settings:** Hiba + team must approve analysis scale, relief window, minimum valid fraction, slope classes, steep threshold, connectivity and any coverage warning threshold. The values in exploratory pilot/matching config are assumptions, not official standards.
7. **Canonical input records:** Each site must have an analysis-ready DEM, matching AOI, CRS, units, vertical-reference statement, source/version/date/URL, quality/effective-resolution notes and stable ID.

The current `config/terrain_fingerprint_run.template.json` is intentionally null/empty. Do not replace its blanks with pilot defaults to make the command execute.

## 4. Run sequence once the gates are met

### Step A — Confirm inputs

For every site, check:

- DEM and AOI paths exist;
- AOI CRS is explicitly known (the extractor defaults to EPSG:4326 only when that is true);
- DEM is already projected, metric, north-up and at the declared pixel size;
- elevation values are metres;
- vertical-reference metadata is explicit and supported by source documentation;
- AOI pixel-centre coverage and NoData are reported;
- source quality layers and uncertainty notes are retained.

### Step B — Configure

Copy the template:

```bash
cp config/terrain_fingerprint_run.template.json config/terrain_fingerprint_run.json
```

Populate only the team-approved values and one record per approved site. Required site fields include `site_id`, `planet`, `source_id`, `dem_path`, `aoi_path`, `elevation_unit`, `vertical_reference`; include `aoi_crs` when not truly WGS84 and all available provenance/quality fields.

### Step C — Verify CLI and run

```bash
python -m src.features.terrain_fingerprint --help
python -m src.features.terrain_fingerprint --config config/terrain_fingerprint_run.json --output data/processed/terrain_fingerprints_canonical.csv --maps-dir data/processed/terrain_maps_canonical
```

Keep canonical outputs separate from exploratory pilot files.

### Step D — Validate and inspect

```bash
pytest -q tests/test_terrain_fingerprint.py
```

Then inspect every row for:

- contract validation errors;
- one unique row per site and common `analysis_scale_m`;
- `nodata_pct + valid_coverage_pct ≈ 100`;
- class percentages sum to approximately 100%;
- no missing required metrics silently replaced by zero;
- sensible units, relief window and TRI definition;
- quality flags, direct support and uncertainty caveats;
- maps visually aligned to the approved AOIs.

Run scale comparison only after producing a second valid run at a separately approved scale. Record actual changes; do not predict results.

### Step E — Hand off

Deliver to Omar and Mohammed:

- `terrain_fingerprints_canonical.csv`;
- per-site Slope, TRI and Local Relief GeoTIFF maps;
- exact run config (no secrets);
- source manifest and checksums;
- per-site quality/uncertainty notes;
- test/validation log;
- scale-sensitivity table, if two valid scale runs were completed;
- this method/readiness documentation.

## 5. Test and CI evidence

- PR #103 added the Hiba method/validation package and additional synthetic tests; PR CI run [#43708031319](https://github.com/MohammadJabr/area-67/actions/runs/43708031319) passed.
- PR #103 was merged to main as commit `873ba8aa5773cf4cf7f9900f92914ea33d1bd626`.
- Post-merge full test run [#43708208185](https://github.com/MohammadJabr/area-67/actions/runs/43708208185) passed.
- A subsequent main test run for PR #104 was in progress at the time of this report; it is separate from the verified PR #103 and post-merge results.

A passing test suite proves the tested software behaviours on the tested inputs. It does not prove the scientific correctness of unapproved AOIs, coordinate frames or cross-source comparability.

## 6. Final handoff verdict

**Software and method documentation: ready.**  
**Synthetic validation and CI for this package: passed.**  
**Canonical fingerprints/maps for the frozen study shortlist: not yet produced.**  
**Remaining dependencies:** approved Earth/lunar AOIs, lunar ROI frame evidence, common metric grid and resampling/NoData policy, approved run settings, and the canonical extraction itself.

This is the accurate state to report to the project lead. The workstream is not blocked by missing fingerprint code; it is blocked at the scientific input/approval boundary.
