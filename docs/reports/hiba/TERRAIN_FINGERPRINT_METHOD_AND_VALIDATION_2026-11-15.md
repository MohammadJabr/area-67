# Hiba Terrain Fingerprint — Method, Validation and Handoff Package

**Prepared:** 2026-11-15  
**Repository:** `MohammadJabr/area-67`  
**Scope:** Hiba's terrain-fingerprint extraction, software validation and handoff requirements.

## 1. Executive status

The repository contains a working, tested terrain-fingerprint implementation for the five groups specified in Hiba's playbook:

1. Slope
2. Terrain Ruggedness Index (TRI)
3. Local Relief
4. Terrain Distribution
5. Spatial Pattern

The implementation and synthetic test suite are present. The full repository CI has passed on earlier main revisions, and this handoff branch adds further explicit configuration, NoData and threshold tests. The CI result for this branch must be checked before treating these additions as verified.

**This package closes the method documentation and software-test reporting work. It does not claim that canonical planetary fingerprints have been produced.** The canonical run still requires approved AOIs, documented coordinate frames and a common analysis grid. Do not substitute exploratory reference-centred windows for those inputs.

## 2. Source files and responsibilities

| File | Role |
|---|---|
| `src/features/terrain_fingerprint.py` | Calculation, GeoTIFF/AOI processing, metadata and derived-map export |
| `tests/test_terrain_fingerprint.py` | Synthetic calculations, raster pipeline, NoData, configuration and contract checks |
| `src/features/validation.py` | Fingerprint row validation, scale-run comparison and feature-correlation audit |
| `config/terrain_fingerprint_run.template.json` | Deliberately unfilled canonical-run template |
| `docs/CANONICAL_TERRAIN_RUN_CHECKLIST.md` | Approval gates and canonical execution checklist |
| `docs/INTEGRATION_CONTRACT.md` | Handoff schema consumed by the Streamlit application |

## 3. Calculation method implemented

The extractor accepts a pre-cropped DEM on a projected metric grid. It does not silently reproject rasters, choose an AOI, reconcile vertical datums, or resample inputs.

### 3.1 Slope

- Central differences estimate horizontal elevation derivatives in the x and y directions.
- Slope is reported in degrees:
  `degrees(arctan(hypot(dz_dx, dz_dy)))`.
- The output includes median, P90 and P95.
- A cell is calculated only when its centre and the four axial neighbours are valid. Edges and cells whose required neighbours include NoData remain missing.
- Units: degrees.

### 3.2 Terrain Ruggedness Index (TRI)

- Uses the Riley-style eight-neighbour definition:
  `sqrt(sum((z_neighbour - z_centre)^2))`.
- The neighbourhood is the eight immediately adjacent cells (one-cell radius).
- The output includes median and P90.
- A cell is valid only when its centre and all eight neighbours are valid.
- Units: same vertical unit as the DEM; the input contract requires metres.

### 3.3 Local Relief

- A moving square neighbourhood calculates P95 minus P5 of valid elevation values.
- The requested physical window is converted to an odd cell-sized kernel. The actual centre-to-centre span is recorded in the output so rounding is visible.
- A configurable minimum fraction of valid cells is required in each window. A NoData centre remains NoData even if surrounding cells are valid.
- The CSV field `local_relief_p95_p5` is the **median of the per-cell local P95–P5 relief map**, not one global AOI-wide P95–P5 statistic.
- The output also includes P90 of the local-relief map.
- Units: metres.

### 3.4 Terrain Distribution

Slope values are partitioned into the current configured analytical classes:

- Low: slope < 10°
- Mid: 10° ≤ slope < 25°
- High: slope ≥ 25°

The percentage denominator is valid slope cells. The three percentages should sum to approximately 100%. These are study thresholds, not universal rover-safety limits. Because this group is derived from slope, matching weights should account for possible redundancy.

### 3.5 Spatial Pattern

- Identifies cells at or above the configured steep-slope threshold (default 25°).
- Labels connected components using configured 4- or 8-neighbour connectivity (default 8).
- Reports the largest connected steep patch as a percentage of valid slope area.
- The measure depends on AOI extent, cell size, threshold and connectivity. It is not a standalone hazard or traversability score.

## 4. Input and quality controls

Before calculation, the GeoTIFF pipeline requires:

- stable `site_id`, `source_id`, and `planet` (Earth, Moon or Mars);
- an explicitly populated vertical-reference field. If unresolved, the value must say so; a non-empty label is not proof that the reference is correct;
- elevation units in metres;
- a projected CRS with metre linear units;
- north-up, non-rotated/non-sheared grid geometry;
- pixel dimensions matching the configured analysis scale;
- an AOI GeoJSON whose CRS is supplied through `aoi_crs` (default EPSG:4326).

AOI rasterization uses pixel-centre inclusion (`all_touched=False`). Valid coverage and NoData percentage are calculated over pixel centres inside the AOI. The source mask is preserved; NoData is never filled with zero.

Quality concepts must remain separate:

- **valid raster coverage**: fraction of AOI pixel centres with valid raster elevation;
- **direct observation support**: a source-specific support measure, such as positive LOLA LDEC count;
- **RMS uncertainty**: a separate uncertainty descriptor.

The extractor can carry a site-level `direct_observation_coverage_pct` value and quality notes, but it does not currently propagate per-pixel LDEC/RMS layers into the terrain statistics or matching score. A supplied aggregate direct-support percentage must not be interpreted as valid raster coverage.

Quality flags identify missing per-pixel quality-layer reporting and missing effective-resolution notes. A quality status of REVIEW is not a scientific approval.

## 5. Synthetic validation evidence

The test module exercises the following behaviours:

| Test case | Expected behaviour |
|---|---|
| Flat synthetic surface | Slope, TRI and local relief are approximately zero |
| Analytic plane | Central-difference slope matches the known gradient |
| Synthetic bump | TRI responds positively; unsupported edge cells remain missing |
| NoData cell | Derivatives do not interpolate through the gap; source NoData is preserved |
| Terrain distribution | Class percentages sum to approximately 100% |
| Connected vs separated steep regions | Largest-patch statistic distinguishes the spatial arrangements |
| Analysis-scale mismatch | Extractor rejects a DEM whose pixel size differs from the configured scale |
| Relief-window rounding | Actual odd kernel and physical span are recorded |
| Fingerprint contract | Inconsistent class percentages are rejected |
| Too few sites for correlation | Correlation audit reports insufficient sites rather than claiming a correlation |
| Scale comparison | Reports absolute and relative changes between supplied scale runs |
| GeoTIFF/AOI integration | Writes contract-ready metrics and derived GeoTIFF maps |
| Geographic-degree grid | Rejected; projected metric CRS is required |
| Missing vertical-reference metadata | Rejected before raster processing |
| Integer DEM | Accepted after safe conversion for calculation |
| Missing relief support fraction | Rejected |
| Optional coverage threshold | Null/omitted threshold remains optional; explicit threshold is preserved |
| Invalid configuration | Invalid scale/window/fraction/connectivity/threshold/coverage settings are rejected |
| Derived-map NoData | All three output maps preserve a NoData centre |
| Terrain class boundary contract | Exact configured class labels and percentage closure are checked |

These are software correctness tests on synthetic inputs. They do **not** demonstrate real-world elevation accuracy, lunar geodetic registration, source comparability, or scientific validity of a candidate ranking.

## 6. Output schema and deliverables

The canonical run is intended to write:

- `data/processed/terrain_fingerprints.csv`: one row per approved site;
- `data/processed/terrain_maps/<site_id>/`: slope, TRI and local-relief GeoTIFFs;
- a short run record describing input files/checksums, AOIs, CRS, vertical-reference statements, scale, relief window, class thresholds, connectivity, NoData/coverage and quality notes.

The integration contract expects the fingerprint CSV to carry stable IDs, planet/source metadata, valid coverage and NoData, the five feature groups, and method/provenance fields. Missing metrics remain null; do not write zero as a substitute.

## 7. What is complete vs. what remains

### Completed in software/documentation

- Five feature groups are implemented.
- Synthetic tests cover expected mathematical behaviour and key failure cases.
- GeoTIFF/AOI extraction, quality metadata, and map export are implemented.
- App-facing fingerprint field contract is documented.
- This handoff package documents calculations, assumptions, test coverage and limitations.

### Still required for canonical scientific delivery

1. Ghassan/team approves source-backed Earth AOI geometries for Haughton, Askja and Mauna Kea.
2. Team/Hiba resolves the lunar ROI coordinate-frame handling and selects the valid, supportable target footprint.
3. Team approves a common projected metric grid, scale(s), resampling method, mask policy and vertical-reference handling. No cross-planet absolute-elevation subtraction is permitted.
4. Hiba fills a run config with approved values and site paths, runs the extractor for the lunar target and frozen Earth shortlist, and reviews all outputs.
5. Quality evidence (valid coverage, direct-observation support, RMS/other quality layers, effective-resolution caveats) is attached without conflation.
6. Scale sensitivity and any independent reference comparison are run only where suitable data exist, and the actual outcomes are recorded.
7. Omar reruns matching from this canonical CSV and approved matching settings; Mohammed verifies the paired outputs in the app.

The canonical template remains intentionally blank until these decisions are made. Do not invent geometry or parameters merely to make the command run.

## 8. Handoff checklist for Hiba

- [ ] Review this method description against the approved study configuration.
- [ ] Receive approved AOI files and source manifest from Ghassan/team.
- [ ] Confirm the CRS, vertical-reference statement, units, common scale and resampling/mask policy for every input.
- [ ] Populate `config/terrain_fingerprint_run.json` from the template with approved values and site entries.
- [ ] Run:
  
  ```bash
  python -m src.features.terrain_fingerprint --config config/terrain_fingerprint_run.json --output data/processed/terrain_fingerprints.csv --maps-dir data/processed/terrain_maps
  ```

- [ ] Review CSV validation, coverage, NoData, quality flags and map outputs for each site.
- [ ] Run the relevant synthetic and scale-sensitivity checks; record actual outputs, not expected outcomes.
- [ ] Deliver the CSV, derived maps, run config (without secrets), provenance/quality notes and this report to Omar and Mohammed.

## 9. Scientific communication limits

- A terrain fingerprint is a compact description, not proof that two planetary locations are equivalent.
- Similarity is relative to the selected candidates, features, scales and weights.
- The score is not a probability, mission-success estimate, safety rating or site certification.
- Copernicus GLO-30 is a DSM; nominal posting is not effective terrain resolution.
- Do not compare absolute elevations across incompatible planetary vertical references.
- Do not treat zero LOLA LDEC as NoData; it indicates no binned direct shot support in that cell, not missing raster elevation.
- Do not present exploratory reference-centred pilot windows as approved geomorphic AOIs.

**Handoff verdict:** The method and software-validation package is prepared. Canonical scientific fingerprints remain blocked by explicit upstream data/geometry/grid approvals and the subsequent real-data run.
