# NASA LOLA provider ROI candidate screening — 2026-11-15

## Purpose and status

This is a diagnostic comparison of seven valid provider-defined ROI features across Site01, Site04, Site07 and Site11. It is **not** an AOI approval, final terrain fingerprint, cross-site ranking, landing/base suitability assessment, or mission certification.

The local screening sampled native raster pixel centres inside each provider polygon (all_touched=False). It read the five native layers: elevation, LDEC counts, slope, Z RMS uncertainty and slope RMS uncertainty. All seven candidates had 100% valid coverage at sampled pixel centres in each of the five layers.

No reprojection, resampling, geometry repair, area weighting, or source-file modification was performed. The output is based on the local read-only screening run dated 2026-11-15; large source rasters and machine-readable raw outputs remain local and gitignored.

## Candidate measurements

| Candidate (zero-based feature index) | Pixel centres | Nominal area (m²) | Positive LDEC (%) | Slope P50 / P90 (°) | Z RMS P50 / P90 (m) | Slope RMS P50 / P90 (°) |
|---|---:|---:|---:|---:|---:|---:|
| Site07 F1 | 612 | 14,737.5 | 9.48 | 1.582 / 3.081 | 0.303 / 0.479 | 1.790 / 2.122 |
| Site01 F4 | 362 | 8,587.5 | 11.05 | 2.046 / 3.826 | 0.304 / 0.445 | 1.780 / 2.109 |
| Site01 F2 | 135 | 3,137.5 | 17.78 | 2.311 / 4.143 | 0.266 / 0.505 | 1.664 / 2.229 |
| Site11 F2 | 155 | 3,637.5 | 10.32 | 1.727 / 3.464 | 0.245 / 0.419 | 1.533 / 1.873 |
| Site01 F3 | 484 | 11,900.0 | 9.09 | 2.334 / 3.840 | 0.349 / 0.558 | 1.932 / 2.321 |
| Site04 F3 | 101 | 2,437.5 | 13.86 | 3.549 / 7.193 | 0.268 / 0.575 | 1.473 / 2.539 |
| Site04 F2 | 102 | 2,400.0 | 14.71 | 3.117 / 5.836 | 0.266 / 0.494 | 1.604 / 2.474 |

All candidates show 100% sampled-pixel coverage in elevation, counts, slope, Z RMS and slope RMS. This is coverage at the sampled ROI pixel centres, not a statement about all polygon area or effective terrain resolution.

## What the measurements do and do not say

- **Site07 F1** has the largest sample (612 pixel centres; 14,737.5 m²). Its positive LDEC support is 9.48%.
- **Site01 F4** has 362 centres, 11.05% positive LDEC support, median Z RMS 0.304 m and median slope RMS 1.780°. It is a useful compromise between sample size and the Site01 illumination/SDEM evidence.
- **Site01 F2** has the highest positive LDEC support (17.78%) but a smaller sample (135 centres).
- **Site11 F2** has the lowest median Z RMS (0.245 m) and lowest median slope RMS among these seven candidates (1.533°), but only 155 centres.
- **Site04 F3** has the lowest median slope RMS (1.473°), but only 101 centres and a higher slope distribution (P50 3.549°, P90 7.193°).
- **Site01 F3** has a larger sample (484 centres), but lower positive LDEC support (9.09%) and higher median uncertainty values than Site01 F4.

These are separate diagnostics, not a composite score. The Site01 working-baseline decision is **not** based on Site01 winning every terrain or uncertainty metric. It is based on the mission-relevant published illumination context for Site01 plus the availability of the corresponding A306 Connecting Ridge SDEM product family. Site07 and Site11 remain meaningful comparison targets if later study design or data evidence changes.

NASA PGDA Product 78 describes Site01 RoIs 4–6 as generally having favorable illumination. The local screening's feature indices are zero-based: **Site01 F4 is provider feature index 4 (the fifth feature / RoI 5)**. This correspondence is a useful screening lead, not an AOI approval.

## Interpretation limits

- Positive LDEC counts indicate direct LOLA shot support. Zero-count cells are counted separately; they are interpolated LDEM support, not NoData.
- Z RMS and slope RMS are the provider uncertainty layers. They are not independent validation of the elevation/slope estimates.
- The reported elevation P90–P10 is the within-ROI elevation distribution spread. It is **not** the moving-window local-relief metric used by the terrain-fingerprint pipeline.
- Nominal 5 m posting is not proof of 5 m effective terrain resolution.
- The ROI geometries and rasters have nominally matching polar-stereographic projection parameters, but their CRS objects/WKT labels are not identical and the physical Moon-fixed ME/PA reference frame is not independently resolved. The screen used raw native coordinates and did not transform them.
- Cross-site terrain/uncertainty comparisons remain provisional until the lunar reference frame, vertical reference, product comparability and common analysis scale are resolved.
- Provider polygons remain candidate footprints, not AREA 67-approved study AOIs.

## Provenance

- Local output: data/metadata/lola_candidate_screening_20261115/
- Local screening utility used: src/data/screen_lola_roi_candidates.py (local working copy at the time of screening; the utility is being versioned separately).
- Machine-readable local outputs: candidate_screening.csv and candidate_screening.json.
- Related visual QA: preview_manifest.json, which records the raw-coordinate overlay limitation and the 0-pixel vertex-to-raster-centre registration residual for the valid Site01/Site04/Site07/Site11 features.