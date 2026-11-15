# Site01 / Site04 provider ROI support and uncertainty audit

**Audit run:** GitHub Actions #43702408661 (15 November 2026)  
**Status:** provider polygon support/uncertainty inventory complete for geometrically valid features; both site audit summaries remain `review_required`. This is not AREA 67 AOI approval, a terrain fingerprint, or a site ranking.

## Source and processing

The audit used the official NASA PGDA Site01 and Site04 ROI archives together with the corresponding five native LOLA raster layers: surface elevation, LDEC spot counts, slope, total elevation RMS uncertainty, and slope RMS uncertainty. Statistics count native raster pixel centres inside each source polygon (`all_touched=false`). No geometry repair, reprojection, resampling, or vertical-reference transformation was applied.

The five layers within each site have matching 3200 × 3200 dimensions, 5m nominal posting, and matching grid metadata. Their embedded lunar WKT uses an unknown-datum placeholder, but NASA PGDA Product 78 states that the GeoTIFF products (excluding XYZI point clouds and ROI shapefiles) use south-polar stereographic X/Y coordinates in metres in the MOON_ME reference frame of ephemeris DE421. The raster frame is therefore source-documented at product level; the ROI shapefile frame remains unverified because PGDA explicitly excludes those shapefiles from its frame statement. No raw WKT was rewritten and no coordinate transformation was applied. See https://pgda.gsfc.nasa.gov/products/78.

## Site01 — Connecting Ridge

| Feature | Pixel centres | Pixel-centre area proxy (km²) | Raster-valid coverage | Positive LDEC support | Zero-count / interpolated | Median Z RMS (m) | Median slope RMS (°) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 317 | 0.007925 | 100% | 4.73% | 95.27% | 0.4397 | 2.1188 |
| 1 | 270 | 0.006750 | 100% | 11.48% | 88.52% | 0.3103 | 1.8234 |
| 2 | 135 | 0.003375 | 100% | 17.78% | 82.22% | 0.2658 | 1.6642 |
| 3 | 484 | 0.012100 | 100% | 9.09% | 90.91% | 0.3492 | 1.9321 |
| 4 | 362 | 0.009050 | 100% | 11.05% | 88.95% | 0.3036 | 1.7799 |
| 5 | — | — | — | — | — | — | — |
| 6 | — | — | — | — | — | — | — |

Features 5 and 6 are invalid and remain excluded from native-geometry statistics. No automatic repair was attempted.

**Review priority, not approval:** Feature 2 has the highest positive-shot share and lowest median Z RMS and slope RMS among the five valid Site01 features, but it is also the smallest (135 pixel centres). Feature 4 has a larger footprint (362 centres) with 11.05% positive LDEC support and median Z RMS 0.3036m. Feature 3 is the largest valid feature (484 centres), but its direct-support share is 9.09%. These are trade-offs for Hiba/Ghassan to assess; they do not identify a final AOI.

## Site04 — Shackleton rim

| Feature | Pixel centres | Pixel-centre area proxy (km²) | Raster-valid coverage | Positive LDEC support | Zero-count / interpolated | Median Z RMS (m) | Median slope RMS (°) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | — | — | — | — | — | — | — |
| 1 | — | — | — | — | — | — | — |
| 2 | 102 | 0.002550 | 100% | 14.71% | 85.29% | 0.2656 | 1.6038 |
| 3 | 101 | 0.002525 | 100% | 13.86% | 86.14% | 0.2678 | 1.4734 |

Features 0 and 1 are invalid and remain review-required. Of the two valid features, Feature 2 has slightly higher positive LDEC support and lower median Z RMS; Feature 3 has lower median slope RMS. Both are very small provider regions and require geomorphic/context review before any use as a project AOI.

## Interpretation rules

- **100% raster-valid coverage is not 100% direct observation.** LDEC-positive percentages are the direct LOLA shot-support measure reported here.
- **Zero LDEC is not NoData.** It denotes a cell without a binned LOLA shot; the LDEM elevation there is interpolated.
- **RMS fields are uncertainty descriptors**, not a per-pixel guarantee or a vehicle safety threshold.
- Pixel-centre area proxies are counts × 25m² at 5m posting. They are not replacements for vector polygon area calculations.
- Provider ROI polygons are not automatically AREA 67 study AOIs.
- The raster GeoTIFF frame is source-documented as MOON_ME/DE421 by PGDA Product 78 even though its embedded WKT uses a placeholder. The ROI shapefile frame remains unverified; do not assign the raster frame to the shapefile or reproject/relabelling from matching polar-stereographic math alone.

## Handoff

Ghassan and Hiba should inspect Site01 Features 2, 3 and 4 as separate candidate regions, and Site04 Features 2 and 3 as separate comparator regions, against A306 illumination/SDEM coverage and source geology/landform context. Record the reason for the chosen polygon and keep rejected/invalid features explicit. Any selected polygon still requires independent confirmation of the provider ROI shapefile frame, an approved scale/uncertainty policy, and documented AOI approval before it is used for canonical terrain fingerprints.
