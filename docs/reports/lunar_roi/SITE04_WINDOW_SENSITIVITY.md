# Site04 Exploratory Window Sensitivity

**Run date:** 2026-11-15  
**Status:** Exploratory raster-window comparison. These rectangles are not approved study AOIs, and this is not a terrain fingerprint.

## Purpose

Compare three square windows around the spatial cluster of the four provider-defined Site04 ROI polygons. The comparison tests whether a larger footprint changes the terrain and quality distributions before an AREA 67 target sub-AOI is proposed.

## Geometry and method

The combined provider-ROI bounds are:

- X: -2842.5 to -2627.5 m
- Y: -6802.5 to -5902.5 m

The arithmetic center of those bounds is used as the common window anchor:

- X = -2735.0 m
- Y = -6352.5 m

Three square windows were evaluated on the local Site04 raster grid, retaining the native 5 m posting and exact alignment of the five source layers. No resampling, reprojection, raster modification, polygon repair, or derived-raster writing was performed.

| Window side | Grid | Bounds (xmin, ymin, xmax, ymax) m | Contains all provider ROI bounds |
|---|---:|---|---|
| 1,200 m | 240 × 240 | (-3335, -6950, -2135, -5750) | Yes |
| 1,500 m | 300 × 300 | (-3485, -7100, -1985, -5600) | Yes |
| 2,000 m | 400 × 400 | (-3735, -7350, -1735, -5350) | Yes |

These are AOI footprint dimensions, not analysis pixel scales or terrain-neighborhood sizes. The nominal 5 m grid posting must not be described as 5 m effective terrain resolution.

## Results

| Metric | 1,200 m | 1,500 m | 2,000 m |
|---|---:|---:|---:|
| Pixel count | 57,600 | 90,000 | 160,000 |
| Elevation valid coverage | 100% | 100% | 100% |
| LDEC valid coverage | 100% | 100% | 100% |
| Slope valid coverage | 100% | 100% | 100% |
| Z RMS valid coverage | 100% | 100% | 100% |
| Slope RMS valid coverage | 100% | 100% | 100% |
| All-five-layers common valid coverage | 100% | 100% | 100% |
| Positive LDEC support | 8.911% | 8.620% | 8.480% |
| Zero-count / interpolated LDEC share | 91.089% | 91.380% | 91.520% |
| Elevation median (m) | 1679.487 | 1653.715 | 1605.683 |
| Elevation P90 (m) | 1728.725 | 1723.439 | 1712.290 |
| Elevation P95 (m) | 1733.224 | 1730.397 | 1725.186 |
| Slope median (°) | 14.713 | 16.262 | 18.048 |
| Slope P90 (°) | 28.699 | 29.497 | 30.961 |
| Slope P95 (°) | 30.268 | 30.965 | 32.574 |
| Z RMS median (m) | 0.348 | 0.358 | 0.372 |
| Z RMS P90 (m) | 0.655 | 0.669 | 0.692 |
| Z RMS P95 (m) | 0.775 | 0.790 | 0.819 |
| Slope RMS median (°) | 1.511 | 1.514 | 1.520 |
| Slope RMS P90 (°) | 2.674 | 2.703 | 2.770 |
| Slope RMS P95 (°) | 3.338 | 3.391 | 3.518 |

All five rasters were checked for identical dimensions, transform and CRS before reading. For each window, the mask and finite-value coverage was calculated separately for every layer; all were 100%. LDEC direct support is positive counts divided by valid finite LDEC cells. Zero-count cells are interpolated DEM support, not NoData.

## Interpretation

1. **All three windows contain all four provider ROI bounds.** The 1,200 m window is therefore the smallest tested square that encloses the current ROI cluster.
2. **Terrain distributions are scale/footprint-sensitive.** From 1,200 m to 2,000 m, median elevation decreases by 73.804 m, median slope increases by 3.335°, and slope P90 increases by 2.262°. The larger windows include materially different terrain, not just more samples of an unchanged distribution.
3. **The quality context is comparatively stable.** Positive LDEC support changes from 8.911% to 8.480%, while Z RMS median changes from 0.348 m to 0.372 m and slope RMS median from 1.511° to 1.520°.
4. **The LDEC support fraction is not a valid-data fraction.** The roughly 91% zero-count/interpolated share is expected context for this product and must remain separate from the 100% valid masks.
5. **A complete raster mask does not approve an AOI.** This comparison does not assess boundaries against a science question, landing/base requirements, illumination, resources, or mission objectives.

## Provisional recommendation for the next review

Use the **1,200 m square only as the leading compact-window candidate for a team review**, because it is the smallest tested footprint that encloses all four provider ROI bounds while retaining full valid coverage in all five layers. Keep the 1,500 m and 2,000 m windows as sensitivity alternatives: they include progressively broader terrain and produce noticeably different slope/elevation distributions.

This is not a scientific selection or automatic approval. Before a fingerprint is generated, the team must still approve:
- the exact lunar sub-AOI and stable site ID;
- the common physical analysis grid/scale across Moon and Earth candidates;
- source/product compatibility and any reprojection/resampling policy;
- the relief-window size and local-relief minimum-valid fraction;
- how the unknown embedded lunar vertical datum, LDEC support and RMS uncertainty are represented.

The window side length is separate from `analysis_scale_m` and `relief_window_m` in the terrain fingerprint configuration.

## Reproduction

The reported values reproduce the local Windows CMD output supplied on 2026-11-15. The calculation reads `elevation`, `counts`, `slope`, `z_uncertainty`, and `slope_uncertainty` using the Site04 asset resolver, verifies exact grid alignment, and reports descriptive statistics over each square window.

See [Terrain Fingerprint Method](../../TERRAIN_FINGERPRINT_METHOD.md), [GIS Handoff](../../GIS_HANDOFF.md), and [LOLA ROI Quality Audit](../../LOLA_ROI_QUALITY_AUDIT.md) for downstream requirements and scientific limitations.
