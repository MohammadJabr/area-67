# GIS preprocessing specification for approved pilot inputs

**Status:** reproducible workflow specification only. No AOI, CRS, scale, grid alignment, vertical transformation, resampling method, mask policy, or output raster is selected here. Raw data must remain immutable.

## 1. Inputs and immutable provenance

For each site, record the exact source path and `source_id`, provider/product/version, source URL, access date, licence/attribution, file size, SHA-256, product date/epoch, surface type (DSM/DTM/unknown), horizontal CRS, pixel grid, NoData/mask, band/unit tags, authoritative elevation units, vertical reference evidence, and quality/uncertainty companion IDs. Preserve source evidence separately from raster tags; never infer a vertical datum from the horizontal CRS. Reuse verified checksum records unless a file change is indicated; otherwise hash the exact input before processing.

Run read-only structural checks with `src/data/raster_inventory.py`, `src/data/earth_dem_qa.py`, and `src/data/raster_preflight.py`. Record readability, CRS, transform, dimensions/bands, pixel spacing and units, masks/valid counts, NoData, raster bounds, tags, supplied metadata, missing fields, and quality-layer grid relationships. A `PASS` is structural only; no status means scientific approval.

## 2. AOI validation (only after written approval)

Keep the approved AOI GeoJSON, its source/author, approval date, version/hash, geometry CRS, and intended site ID with the run record. Validate JSON and GeoJSON structure; require a polygonal geometry, closed rings, valid topology, longitude/latitude coordinate order when RFC 7946 WGS84 is used, and explicit declaration if another CRS is supplied. Check geographic bounds and geometry plausibility without silently repairing invalid geometry.

Transform AOI geometry for checks only using a declared horizontal CRS. Test its full geometry—not just centroid or bounding box—against source raster footprint and valid-data mask. Separately test every quality/uncertainty/mask asset for coverage and alignment. Record uncovered fractions, holes, edge effects, and whether proposed AOI needs surrounding source context for derivative neighborhoods.

The required source edge margin is **UNDECIDED**. Hiba/Ghassan/team must define it from the selected algorithms, windows, reprojection behavior, and AOI boundary treatment; do not invent a distance.

## 3. CRS, vertical reference, and target grid

Once a pilot AOI and comparison policy are approved, write down before processing:

- Target projected CRS and rationale/area of use.
- Whether a vertical datum transformation is needed; source/target vertical references, geoid model/grid, software, and transformation pipeline. Horizontal reprojection and vertical transformation are separate operations. If no defensible transformation is available, document incompatibility and stop rather than infer or silently shift heights.
- Common physical pixel scale, grid origin/alignment, extent/snapping rule, orientation, output dimensions, and numeric type.
- Resampling operator chosen for elevation values and its scientific reason. Define any distinct rules for categorical masks and continuous quality layers.
- AOI crop/mask ordering, any edge support required, and NoData propagation behavior.

The result must be projected, metric, north-up and non-rotated for Hiba's current extractor. The exact CRS, pixel scale, grid origin, resampling, extent and vertical treatment are **parameters awaiting team/Hiba approval**. No default is supplied by this specification. Avoid mosaicking the two USGS tiles until their cross-zone transform/grid policy and source continuity have been approved and validated.

## 4. NoData, support, and quality

Before and after preparation, preserve source NoData and masks; distinguish invalid samples from valid zero elevations. Do not fill missing cells with zero or interpolate unless a separate explicit method is approved and fully recorded. Inspect for non-finite values, unexpected gaps, reprojection-edge loss, AOI valid-coverage percentage, and changes in support between source and output.

Where available, retain and inspect source-specific land/water/ice, editing/fill, height-error, count, MAD, date, data-mask, direct-observation, and uncertainty layers. Do not treat asset availability as quality validation. Record companion footprint, grid match, units/encoding, interpretation, missing cells, and known caveats. Site04 direct observation support remains distinct from valid elevation coverage. Any accepted coverage threshold or uncertainty gate is **UNDECIDED**.

## 5. Output and manifest structure

Create derived products under a separate path, never under `data/raw/`:

```text
data/processed/earth/<site_id>/<run_id>/
  dem_analysis.tif
  aoi_approved.geojson
  processing_manifest.json
  qa.json
  qa.md
  provenance.md
```

`run_id` should be a stable date/version or content-addressed identifier, not a mutable `latest` alias. Do not create placeholder rasters. The processing manifest records exact source and AOI hashes; software/library versions; command/config; target CRS/grid; horizontal and vertical operations; resampling; mask/NoData policy; quality companions; source/output checksums; processing time; and operator. QA reports include structural checks, AOI/source/quality coverage, valid/NoData counts, grid properties, warnings, and unresolved limitations.

## 6. Hiba handoff gate

Before fingerprint extraction, provide one approved AOI and one analysis-ready DEM per included site; stable IDs and exact source IDs; product/surface/source records; explicit vertical reference and metre elevation unit; projected metric north-up non-rotated grid; common approved scale; and recorded mask, coverage, quality and processing evidence. Hiba's `relief_window_m` and `local_relief_min_valid_fraction` remain explicitly configured study parameters. Run Hiba's documented preflight and validation only after those values and AOIs are approved. The current Copernicus geographic source tiles cannot be passed directly to Hiba's metric-grid input; this is a future preparation workflow, not authorization to process now.
