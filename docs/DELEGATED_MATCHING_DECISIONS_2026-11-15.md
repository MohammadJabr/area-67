# AREA 67 — delegated execution decisions for Omar's matching baseline

**Decision date:** 2026-11-15  
**Decision owner:** Delegated project execution agent  
**Status:** Operational baseline selected for implementation and sensitivity testing. This is not scientific certification or validation of final study AOIs.

The user explicitly delegated selection of remaining project defaults. The choices below are adopted as the working baseline; unresolved evidence gates remain explicit.

## 1. Target and candidate set

- **Primary lunar target:** NASA PGDA LOLA Site01 / Connecting Ridge. Site01 is the only ranked lunar MVP target.
- **Site04 / Shackleton rim:** LOLA QA and comparison context only; not a second ranked target.
- **Frozen Earth shortlist:** Haughton Crater (impact/polar desert), Askja (named caldera/lava-field unit), and Mauna Kea (named summit/flank volcanic unit).
- **Yungay and McMurdo/Taylor Valley:** held out. Yungay has an unresolved field-reference mismatch; McMurdo/Taylor Valley lacks a selected named landform/AOI in the current source footprint.

This resolves the ambiguity in favour of the frozen sprint shortlist, not the later exploratory Haughton/Yungay/Mauna Kea sample set.

## 2. AOI selection policy

- Site01: Connecting Ridge landform. Use valid provider ROI Feature 4 as primary registration/quality anchor and Feature 2 as independent high-direct-support cross-check. Neither small provider polygon is itself the final operations AOI.
- Haughton: crater final rim and immediately associated rim-slope terrain. Do not merge central basin, ejecta blanket, or faulted terraces.
- Askja: one contiguous caldera-floor/lava-field unit, excluding the whole volcano footprint and unrelated lake/ice surfaces.
- Mauna Kea: one contiguous summit/flank volcanic unit within the available Copernicus source tile; do not mix summit and distant flank terrains.

**Geometry status:** these are adopted geomorphic selection instructions, but final polygon coordinates are not approved until the GIS owner exports, source-documents, and validates bounded polygons. Site01 ROI shapefile frame remains unresolved; no coordinate transformation or datum relabelling is authorised. Haughton's selected final-rim unit must be digitized against cited geological mapping, not approximated by a circle.

## 3. Analysis scale and relief window

- Primary grid experiment: **30 m**.
- Scale sensitivity: **60 m**.
- Primary local-relief physical window: **150 m** (5 cells at 30 m; 120 m centre-to-centre span).
- Window sensitivity: **90 m and 210 m**, with odd cell counts documented at each grid scale. Record actual cell count and centre-to-centre span.
- Minimum-valid-neighbour fraction: retain **0.8** provisionally; report resulting valid-cell counts and NoData. This is not a universal scientific threshold.
- Terrain classes: low <10°, mid 10–25°, high ≥25°; analytical bins, not rover safety thresholds.
- Spatial pattern: largest 8-connected patch of slope ≥25° as percentage of valid slope area; 4-connectivity is a sensitivity check.

Rationale: Copernicus GLO-30 is the common Earth baseline, while lunar 5 m posting is not equivalent to effective resolution. Site01 pilot Product 90 effective-resolution P90 is around 24.08 m, making 30 m a defensible first experiment, not a proven optimum. The 60 m run and Product 90/A306 quality checks remain mandatory before final scale selection.

## 4. Matching profile and tolerances

Mission: **Rover Navigation / Terrain Traversal**.

Weights: Slope 0.30; TRI 0.25; Local Relief 0.20; Spatial Pattern 0.20; Terrain Distribution 0.05.

Deterministic pilot tolerances: Slope 5 degrees; TRI 10 m; Local Relief 15 m; Terrain Distribution 20 percentage points; Spatial Pattern 15 percentage points.

Completeness and safeguards: minimum feature-group completeness **1.00**; minimum conservative data completeness **0.95**; scale-relative tolerance **0.01**; distribution-sum tolerance **0.5 percentage points**; one-at-a-time ±20% weight sensitivity with renormalization, plus Slope-only baseline.

These are delegated prototype assumptions to make the run deterministic, not NASA, rover-manufacturer, or universal thresholds. Omar's report must additionally include tolerance sensitivity (at minimum 0.5×, 1×, 1.5× each tolerance or documented equivalent), candidate rejection reasons, group contributions, missing groups, completeness, Slope-only rank changes, and weight sensitivity. Scenario counts are descriptive, not probabilities.

## 5. Gates before canonical ranking

1. Source-backed AOI polygon and stable ID; no reference-centred placeholder window.
2. Common projected metric grid with documented resampling and mask/NoData policy.
3. Comparable 30 m and 60 m runs; selected scale supported by Product 90 EFFRES/A306 checks and ranking stability.
4. Hiba's five-group fingerprint with full method metadata: Riley eight-neighbour TRI, physical relief window and actual span, class thresholds, largest steep-patch definition/connectivity.
5. Direct LOLA support, RMS uncertainty, raster-valid coverage and NoData reported separately. Zero LDEC is not NoData.
6. Earth DSM effective-resolution limitations and absent per-pixel quality companions stated explicitly.
7. No absolute Earth–Moon elevation comparison without defensible vertical-reference transformation.
8. Matching run records exact configuration and input checksums; application consumes paired outputs with provenance intact.

If a gate fails, exclude the affected site/group with a reason or retain the exploratory label. Never impute missing values.

## 6. Handoffs

- **Ghassan:** digitize/export the selected geomorphic polygons; provide citations, stable IDs, frame/CRS/vertical reference, common-grid QA and quality summaries. Site01 Features 4/2 are anchors only.
- **Hiba:** canonical five-group fingerprints for Site01 and Haughton/Askja/Mauna Kea at 30 m and 60 m; test 90/150/210 m relief windows; report quality, NoData, direct support and uncertainty separately.
- **Omar:** apply the explicit baseline after Hiba's canonical CSV; run tolerance/weight sensitivity, Slope-only baseline, exclusions and contributions.
- **Mohammed:** integrate only canonical paired outputs after gates pass; keep the exploratory warning until then.

## 7. Existing pilot status

The Haughton/Yungay/Mauna Kea ranking remains an exploratory reference-window pilot, preserved for reproducibility and regression testing only. It is not relabelled as the frozen three-candidate result. Replace it only after the selected Haughton/Askja/Mauna Kea AOIs and Hiba fingerprints exist.
