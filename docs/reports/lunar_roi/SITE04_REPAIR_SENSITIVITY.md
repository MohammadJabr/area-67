# Site04 ROI repair and raster sensitivity note

**Run date:** 2026-11-15  
**Scope:** Local diagnostic run on the provider ROI shapefile and the five Site04 LOLA raster layers.  
**Status:** Evidence note only. No source geometry was edited, no repaired geometry was saved, and no AREA 67 AOI is approved by this analysis.

## Executive summary

The Site04 provider shapefile contains four polygon features. Features 0 and 1 are invalid because each has a ring self-intersection. A read-only Shapely `make_valid()` preview produced valid polygonal alternatives:

- Feature 0 becomes a two-part `MultiPolygon` with total polygon area unchanged at 5,450 m² and no non-polygon remnants.
- Feature 1 becomes a `GeometryCollection` containing a three-part `MultiPolygon` (2,750 m² total) and three line remnants totaling 17.07 m. Its largest polygon is 2,487.5 m².

Raster summaries were calculated in memory from the valid polygonal output only, using native raster pixel centers (`all_touched=false`). They are diagnostic comparisons, not official provider-ROI audit records or terrain fingerprints.

The small Feature 1 fragments add 12 pixel centers when included (114 versus 102). The aggregate slope and uncertainty summaries change only slightly. This suggests the largest component captures most of the measured area, but it does not prove that the fragments are semantically unintended or that the largest-only boundary is the correct interpretation.

## 1. Source geometry findings

The original source geometries and attributes remain unchanged.

| Source feature | Source X | Source Y | Shapely validity reason |
|---|---:|---:|---|
| 0 | -2812.5 | -6647.5 | Ring Self-intersection at (-2807.5, -6662.5) |
| 1 | -2757.5 | -6342.5 | Ring Self-intersection at (-2742.5, -6387.5) |

### Feature 0 repair preview

- Output: valid `MultiPolygon`, two polygon parts, no line remnants.
- Total area: 5,450 m².
- Part A: 2,137.5 m².
- Part B: 3,312.5 m².
- Total area change reported by the local diagnostic: 0%.

### Feature 1 repair preview

- Output: `GeometryCollection` containing a valid `MultiPolygon` and a `MultiLineString`.
- Polygon part A: 225 m².
- Polygon part B: 37.5 m².
- Polygon part C (largest): 2,487.5 m².
- Total polygon area: 2,750 m².
- Line remnants: three segments of 7.07 m, 5 m and 5 m (17.07 m total).
- Total area change reported by the local diagnostic: 0%.

The line remnants were not passed to raster masking. They are retained as a topology diagnostic and must not silently be converted into polygon area.

## 2. Raster sensitivity results

The five raster layers used were elevation (LDEM), LDEC counts, slope, total Z RMS uncertainty and slope RMS uncertainty. The diagnostic used the existing `inspect_feature()` routine and its pixel-center inclusion rule.

| Diagnostic geometry | Area (m²) | Pixel centers | Positive LDEC support | Zero-count / interpolated | Slope median (°) | Slope P90 (°) | Z RMS median (m) | Slope RMS median (°) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Feature 0 — all polygon parts | 5,450 | 221 | 9.95% | 90.05% | 2.977 | 6.267 | 0.4254 | 1.6875 |
| Feature 1 — all polygon parts | 2,750 | 114 | 14.04% | 85.96% | 2.570 | 5.488 | 0.2596 | 1.4870 |
| Feature 1 — largest polygon only | 2,487.5 | 102 | 13.73% | 86.27% | 2.502 | 5.491 | 0.2478 | 1.4690 |

All five diagnostic geometries/components were reported as `inventory_complete` by the in-memory calculation, with 100% valid elevation and LDEC coverage and no missing/invalid LDEC cells. This status means the configured inventory calculations completed; it is not scientific approval.

### Feature 1 sensitivity to its small fragments

Comparing all polygon parts with the largest polygon only:

- Pixel centers increase from 102 to 114 (+12).
- Positive LDEC support changes from 13.73% to 14.04% (+0.31 percentage points).
- Slope median changes from 2.502° to 2.570° (+0.068°).
- Slope P90 changes from 5.491° to 5.488° (-0.003°).
- Z RMS median changes from 0.2478 m to 0.2596 m (+0.0118 m).
- Slope RMS median changes from 1.469° to 1.487° (+0.018°).

For these summary statistics, including the small fragments has little numerical effect. However, boundary choice can affect local-relief and connected-patch metrics, and the fragment geometry still needs a source interpretation. Do not discard the fragments solely because their area is small.

## 3. Interpretation and limitations

1. NASA PGDA states that roughly 90% of the 5 m pixels in these polar LOLA DEMs are interpolated because of LOLA cross-track and inter-spot spacing. Thus, the 85.96–90.05% zero-count shares observed here are not, by themselves, evidence of defective raster coverage. Positive LDEC support, raster validity and RMS uncertainty are separate evidence fields. See [NASA PGDA product 78](https://pgda.gsfc.nasa.gov/products/78) and [Barker et al. (2021)](https://doi.org/10.1016/j.pss.2020.105119).
2. A 5 m pixel posting is not a claim of 5 m effective terrain resolution. PGDA notes that effective resolution/interpolation behaviour depends on LOLA track density and spatial gaps.
3. The provider ROI polygons are not AREA 67-approved study AOIs. The repaired components are diagnostic alternatives only.
4. No automated geometry repair has been applied to the source shapefile. No repaired geometry has been written to disk.
5. The existing two valid source features (indices 2 and 3) each contain only about 100 raster pixel centers. The repaired Feature 0 aggregate contains 221. The team has not approved a minimum AOI sample size or a physical analysis scale, so these counts cannot be turned into a pass/fail decision.
6. These summaries do not constitute the five-group terrain fingerprint. Slope, TRI, local relief, terrain distribution and spatial pattern require an approved AOI, common analysis grid, documented physical neighborhood/window settings and explicit treatment of interpolation and uncertainty.
7. Feature 0 is multipart, and Feature 1 has line remnants and small polygon fragments. Their scientific meaning should be reviewed before deciding whether to carry the repaired alternatives forward.

## 4. Recommended project disposition

- Preserve the original NASA ROI archive, extracted shapefile and current inspection report as source records.
- Keep Feature 0's two-part repair and Feature 1's all-parts/largest-only variants as diagnostic alternatives; do not overwrite the provider polygons.
- Do not rank these small provider ROIs as permanent-base or mission analog candidates from these statistics.
- Define a larger, question-driven Site04 target sub-AOI with the team. Record its polygon source, rationale, stable ID and reviewer.
- Agree the Earth candidate landforms, common physical analysis scale, projection/resampling policy, relief window, local-relief valid-neighbour fraction, slope classes and spatial-pattern settings before running the real fingerprint workflow.
- Retain LDEC and both RMS uncertainty layers alongside the elevation data. Do not convert zero counts to NoData or treat a zero-count pixel as a direct LOLA shot.

## 5. Reproduction

The local diagnostic outputs were supplied from Windows CMD runs on 2026-11-15. The read-only commands used Shapely `make_valid()`, recursively extracted polygon parts from its output, combined polygon parts with `unary_union()`, and called `inspect_feature()` on temporary in-memory geometries. No output geometry file was written.

The reproducible project methodology and required configuration are documented in [Terrain Fingerprint Method](../../TERRAIN_FINGERPRINT_METHOD.md) and [GIS Handoff](../../GIS_HANDOFF.md).
