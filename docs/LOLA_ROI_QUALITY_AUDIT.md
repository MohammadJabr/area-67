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

- The shapefile must declare a CRS. Exact CRS equivalence is checked first; for custom projected lunar WKT, the audit also accepts a narrowly defined mathematical equivalence when the body ellipsoid, prime meridian, projection method/parameters, and axis units/directions match despite differing placeholder metadata names. It does not guess a CRS or reproject a lunar ROI.
- The five raster layers must have one band each and exactly matching CRS, dimensions, and affine transform.
- Null, empty, invalid, unsupported, or non-overlapping geometries are reported and not automatically repaired.
- No raster data are altered, resampled, clipped to disk, or exported.
- All statistics are descriptive summaries in the source product's declared units. They are not accuracy thresholds or approval cutoffs.

## Interpretation

This audit helps compare the observation support and uncertainty context of provider ROIs within a single LOLA site. It can identify ROIs where the interpolated fraction or RMS uncertainty differs from the site-wide average. It does not answer whether one ROI is more suitable for a lunar base: that also requires terrain hazards, illumination, temperature, resources, communications, mission requirements, and engineering constraints.

Do not compare absolute lunar and Earth elevations as if their vertical reference frames were interchangeable. Do not infer effective terrain resolution from the 5 m pixel posting. Keep direct observations, interpolated cells, raster validity, and RMS uncertainty as separate evidence dimensions.

NASA PGDA source: https://pgda.gsfc.nasa.gov/products/78
