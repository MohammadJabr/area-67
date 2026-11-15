# LOLA ROI-Level Observation Support and Uncertainty Audit

This workflow takes the official PGDA ROI shapefiles and the five corresponding LOLA rasters, then reports how much direct laser-shot support and uncertainty evidence exists inside each provider-defined polygon.

It is an input-quality audit. It is not a terrain fingerprint, site ranking, lunar base recommendation, or AREA 67 AOI approval.

## Inputs

After running the multi-site acquisition workflow, the expected inputs for Site04 are:

- ROI shapefiles under data/raw/moon/roi_shapes/Site04/
- Five raster layers under data/raw/moon/site04/: elevation, counts (LDEC), slope, Z RMS uncertainty, and slope RMS uncertainty.

The same structure is used for Site01, Site06, Site07, and Site11. The tool requires all five rasters for the selected site and checks that they have exactly matching CRS, dimensions, and affine transform.

## Run

From the repository root:

```bash
python src/data/lola_roi_quality.py --sites Site04
```

After acquiring Site01 rasters and ROI shapes, run:

```bash
python src/data/lola_roi_quality.py --sites Site01 Site04
```

To audit all five PGDA sites after all corresponding rasters have been acquired:

```bash
python src/data/lola_roi_quality.py --sites Site01 Site04 Site06 Site07 Site11
```

The command writes one JSON report and one Markdown summary per site under data/metadata/lola_roi_quality/.

## Per-ROI outputs

Each polygon feature is reported with its source shapefile, feature index, source attributes, and:

- ROI pixel-center count, using all_touched=false.
- Elevation valid coverage within the polygon.
- LDEC valid coverage within the polygon.
- Percentage of valid finite LDEC cells with a positive shot count.
- Percentage of valid finite LDEC cells with zero shot count (interpolated LDEM support).
- Negative LDEC count and missing/invalid LDEC cell count.
- Elevation and slope descriptive summaries.
- Median, P90, P95 and maximum/minimum summaries for the Z RMS and slope RMS layers.

Direct-observation support is calculated as positive LDEC cells divided by valid finite LDEC cells within the polygon. Zero-count LDEC cells are not treated as NoData. Missing LDEC values are reported separately. The denominator is explicit in each JSON feature record.

## Fail-closed behavior

- The shapefile must declare a CRS. Exact CRS equivalence is checked first. The custom projected-lunar fallback requires compatible datum identity as well as matching body shape, prime meridian, projection method/parameters, and axis units/directions: two placeholder datum labels may match each other, and explicit names must match each other. An unknown-to-explicit match and different explicit frame names (for example, MOON_ME versus MOON_PA) are rejected even when projection mathematics match. A both-unknown match is only nominal coordinate-math compatibility; it does not identify the actual Moon-fixed frame. No CRS is guessed and no lunar ROI is reprojected.
- The five raster layers must have one band each and exactly matching CRS, dimensions, and affine transform.
- Null, empty, invalid, unsupported, or non-overlapping geometries are reported and not automatically repaired.
- No raster data are altered, resampled, clipped to disk, or exported.
- All statistics are descriptive summaries in the source product's declared units. They are not accuracy thresholds or approval cutoffs.

## Invalid-geometry repair sensitivity preview

The normal ROI quality audit deliberately does not calculate statistics for invalid source geometries. Use the separate preview tool to learn why a feature is invalid and what a Shapely `make_valid` candidate would produce, without changing the source shapefile:

```bash
python src/data/preview_invalid_roi_repairs.py --site Site04 --roi-directory data/raw/moon/roi_shapes/Site04 --output data/metadata/site04_invalid_roi_repair_preview.json
```

For invalid features, the JSON records the Shapely validity reason, `make_valid` output type, polygon component count, any non-polygon components excluded from raster statistics, candidate geometry bounds/area, separate preview-only LOLA statistics for each polygon component, and combined statistics for their union. Already-valid features are summarized from their original geometry for comparison.

The utility is diagnostic only. It never writes geometry, replaces an ROI, or treats a make-valid result as the provider's intended boundary. Repair-preview statistics must not be merged into the official ROI QA report or used as AREA 67 study-AOI evidence until the team reviews the candidate geometry and its scientific provenance.

### Previously captured Site04 make-valid preview

A local diagnostic run recorded on 2026-11-15 had already applied Shapely `make_valid` in memory to the two invalid source features and passed each polygon component separately to the existing ROI raster-statistics function. The measurements below are **preview-only**, not official ROI statistics:

| Source feature | Polygon component | Component area (m²) | Pixel centres | Positive LDEC support | Median Z RMS (m) | Median slope (°) | Median slope RMS (°) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 2,137.5 | 88 | 12.50% | 0.4134 | 2.9892 | 1.6728 |
| 0 | 1 | 3,312.5 | 133 | 8.27% | 0.4295 | 2.9562 | 1.6875 |
| 1 | 0 | 225.0 | 10 | 10.00% | 0.4651 | 3.5467 | 1.6971 |
| 1 | 1 | 37.5 | 2 | 50.00% | 0.1211 | 2.5720 | 1.1064 |
| 1 | 2 | 2,487.5 | 102 | 13.73% | 0.2478 | 2.5022 | 1.4690 |

Feature 0 therefore produced two polygon components with a combined area of **5,450 m²** and 221 raster pixel centres. Feature 1 produced three components with a combined area of **2,750 m²** and 114 pixel centres. These sums describe the polygonal output from that in-memory repair run; they do not prove that the provider intended each component to be an independent ROI, nor that the original geometry's intended topology was recovered.

The small 225 m² and 37.5 m² components from source feature 1 deserve special scrutiny. The 37.5 m² component has only two pixel centres, so its apparently high 50% positive LDEC percentage is based on just two cells and should not be compared directly with the larger components as if the support were equally stable.


## Pixel-registration diagnostic

The ROI polygons can be checked against the native raster's affine pixel lattice without changing either source. The diagnostic reports whether every polygon-ring vertex lies on the pixel-centre lattice, the pixel-corner lattice, or neither. It measures residuals in map units and also records the raster's `AREA_OR_POINT` tag.

A preliminary **bounding-box-only** check is already possible from the recorded Site04 metadata. With affine transform `[5, 0, -9000, 0, -5, 1000]`, the ROI-cluster extrema `X=[-2842.5, -2627.5] m` and `Y=[-6802.5, -5902.5] m` map to pixel-centre indices `column=[1231, 1274]` and `row=[1560, 1380]` respectively. Thus all four bounding-box extrema lie on the pixel-centre lattice. This is not yet a full vertex audit: the remaining ring vertices must still be checked by the diagnostic below. No half-pixel shift is indicated by these extrema.

Run from the repository root:

```bash
python src/data/audit_roi_pixel_registration.py --shapefile data/raw/moon/roi_shapes/Site04/Site04_ROIs.shp --raster data/raw/moon/site04/Site04_final_adj_5mpp_surf.tif --output data/metadata/site04_roi_registration.json
```

The command refuses to overwrite an existing report and does not reproject, shift, repair, rasterize, or modify the shapefile or raster. A pixel-centre alignment result demonstrates geometric agreement with the affine lattice only; it does not establish the missing lunar datum/frame or prove the scientific rule used to create the ROIs. The default 1e-6 m tolerance is numerical, not a scientific threshold.

## Interpretation

This audit helps compare the observation support and uncertainty context of provider ROIs within a single LOLA site. It can identify ROIs where the interpolated fraction or RMS uncertainty differs from the site-wide average. It does not answer whether one ROI is more suitable for a lunar base: that also requires terrain hazards, illumination, temperature, resources, communications, mission requirements, and engineering constraints.

Do not compare absolute lunar and Earth elevations as if their vertical reference frames were interchangeable. Do not infer effective terrain resolution from the 5 m pixel posting. Keep direct observations, interpolated cells, raster validity, and RMS uncertainty as separate evidence dimensions.

NASA PGDA source: https://pgda.gsfc.nasa.gov/products/78
