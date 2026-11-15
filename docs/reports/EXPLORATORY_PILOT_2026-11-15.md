# AREA 67 — Exploratory Space-to-Earth MVP pilot

**Status: EXPLORATORY / NOT APPROVED FOR SCIENTIFIC SITE CERTIFICATION**

This pilot connects real NASA LOLA and Copernicus DEM source rasters to the project's five-group terrain fingerprint and mission-matching concepts. It is an engineering demonstration of an evidence pipeline, not a final planetary-analog study.

## Pilot scope

- **Target:** NASA PGDA Site01 / Connecting Ridge. A 990m × 990m sampling window was selected inside the earlier 1km read-only screening square. The provider ROI's local frame has not been independently proven to be the correct physical Moon-fixed frame.
- **Mission:** Rover Navigation / Terrain Traversal.
- **Earth windows in the ranking:** Haughton central-basin published crater-centre reference, Yungay published hyper-arid-core study reference, and Mauna Kea USGS HVO summit reference.
- **Askja:** held out of ranking. The selected Smithsonian reference-centred 990m window is dominated by near-flat/equal-elevation samples. This is not a conclusion about all Askja terrain; select a geomorphic caldera/lava-field AOI before retesting.
- Each Earth window is **990m × 990m (0.9801 km²)** and is centred on a published/reference point. None is an approved AREA 67 geomorphic AOI.

## Terrain Fingerprint results

| Window | Slope P50 | Slope P90 | TRI P50 | TRI P90 | Local relief summary | Low / Mid / High slope | Largest steep patch |
|---|---:|---:|---:|---:|---:|---:|---:|
| Site01 pilot window | 4.55° | 9.46° | 6.07m | 12.28m | 9.88m | 93.34 / 6.66 / 0.00% | 0.00% |
| Haughton reference | 3.23° | 5.88° | 4.34m | 7.75m | 7.24m | 99.58 / 0.42 / 0.00% | 0.00% |
| Yungay reference | 1.85° | 4.80° | 2.59m | 6.67m | 3.98m | 99.06 / 0.94 / 0.00% | 0.00% |
| Mauna Kea reference | 21.65° | 27.60° | 29.10m | 38.18m | 46.71m | 12.38 / 57.86 / 29.76% | 13.94% |

*The local-relief column is the median over the map of moving P95–P5 values; it is not absolute elevation.*

## Exploratory matching result

| Rank | Candidate reference window | Relative similarity index | Weighted distance | Top-1 across 11 weight scenarios |
|---:|---|---:|---:|---:|
| 1 | Haughton | 73.79 / 100 | 0.3553 | 11 / 11 |
| 2 | Yungay | 66.13 / 100 | 0.5121 | 0 / 11 |
| 3 | Mauna Kea | 27.39 / 100 | 2.6510 | 0 / 11 |

The score is 100 divided by (1 + weighted distance). It is a relative ranking index under the selected features, tolerances, and mission weights. It is **not** a probability, percentage of physical equivalence, rover-safety score, or site certification.

The Slope-only baseline gives the same ordering for these three windows (Haughton 1, Yungay 2, Mauna Kea 3). This indicates that the multi-feature ordering did not change the ordering in this small pilot; it does not prove that the extra dimensions improve predictive validity.

## Data quality and source constraints

- Site01 positive LOLA LDEC support in the 990m window is **9.235%**. The sampled surface raster has 100% valid mask coverage, but most cells have zero LDEC and therefore no positive direct-shot bin support. Raster validity and direct instrument support are different.
- Product 90 bounded Site01 inspection: EFFRES P50 **15.78m**, P90 **24.08m**. The nominal 5m LOLA posting is not evidence of 5m effective terrain resolution.
- Site01's local south-polar WKT datum label is unknown. No frame relabelling, reprojection, or coordinate offset was applied to the lunar target.
- Earth windows use Copernicus GLO-30 DSM inputs, resampled by bilinear elevation interpolation to a provisional 30m metric grid. Effective terrain resolution was not independently established and no per-pixel quality/uncertainty companions were retrieved.
- Product documentation describes Earth elevation heights in EGM2008 metres. No absolute cross-body elevation comparison or vertical offset was applied.
- All three Earth windows remain provisional reference-centred samples. Haughton's published crater-centre is not a digitized basin boundary; Yungay's published study point is not yet confirmed as the team's exact plot; Mauna Kea's volcano reference is not a chosen summit/flank landform.

## Provisional analysis and matching settings

The exploratory configuration used 30m analysis cells, a 150m requested local-relief window (rounded to five cells with a 120m centre-to-centre span), an 0.80 minimum local-neighbour fraction, Riley eight-neighbour TRI (one-cell radius), slope classes below 10°, 10–25°, and at least 25°, and an eight-connected steep-patch metric. The mission weights were 0.30 Slope, 0.25 TRI, 0.20 Local Relief, 0.20 Spatial Pattern, and 0.05 Terrain Distribution. The tolerances were 5°, 10m, 15m, 20 percentage points, and 15 percentage points, respectively. Weight sensitivity perturbed one weight at a time by ±20%, producing 11 scenarios including baseline.

These settings are **provisional team assumptions**, not official NASA or rover-manufacturer standards. They still require Hiba, Omar, and Ghassan's review against effective resolution, AOI geometry, source support, and scale/window sensitivity.

## Files and handoff

- data/processed/terrain_fingerprints.csv — app-facing four-row exploratory fingerprint table (one target + three Earth windows).
- data/processed/candidate_rankings.csv — three ranked candidate windows with per-group contributions and explicit caveats.
- data/processed/ranking_robustness.json — slope-only baseline and weight-sensitivity summary.
- data/metadata/pilot_2026-11-15/ — the run configuration and native/projected sampling-window metadata.
- data/processed/pilot_2026-11-15/earth_sampling_windows.geojson — Earth window polygons only. The Moon window is retained in JSON in its native unknown-datum frame and is intentionally not transformed to WGS84.

## Required before promoting this to the validated MVP

1. Ghassan and Hiba must approve or replace the sample windows with source-backed geomorphic AOIs and confirm all CRS/vertical/mask decisions.
2. Hiba must independently rerun the repository's canonical five-group extraction and validate the provisional metrics/settings, including scale/window sensitivity and data-support notes.
3. Omar must independently rerun the repository matching workflow using approved tolerances/completeness gates and verify the CSV and robustness sidecar.
4. The team must agree whether the three provisional Earth regions are the final pilot candidates; Askja requires a new specific AOI before it can be ranked.
5. Only after those reviews should the app stop describing results as exploratory.


## Local-relief window sensitivity (exploratory)

The same five 30m sample grids were recomputed with the requested local-relief window changed while all other feature calculations, sample extents, weights, and tolerances were held constant. The configured windows round to odd cell widths:

| Requested window | Cells | Actual centre-to-centre span | Haughton | Yungay | Mauna Kea |
|---:|---:|---:|---:|---:|---:|
| 90m | 3×3 | 60m | Rank 1 · 74.08 | Rank 2 · 67.10 | Rank 3 · 28.63 |
| 150m | 5×5 | 120m | Rank 1 · 73.79 | Rank 2 · 66.13 | Rank 3 · 27.39 |
| 210m | 7×7 | 180m | Rank 1 · 73.23 | Rank 2 · 64.51 | Rank 3 · 26.01 |

The relative rank order remains unchanged across these three local-relief windows. Score values change because the Local Relief feature changes. This is a one-parameter window sensitivity check at a fixed 30m grid, **not** a full analysis-scale sensitivity test and not AOI approval. See `ranking_robustness.json` for the detailed values and configuration notes.

