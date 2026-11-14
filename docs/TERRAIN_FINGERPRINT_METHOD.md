# AREA 67 — Terrain Fingerprint Method

**Owner:** Hiba Sbouh — Terrain Fingerprint & Scientific Validation  
**Status:** extraction code and synthetic validation implemented; real site fingerprints pending approved AOIs and common-scale DEMs.

This module turns one analysis-ready DEM and one approved site AOI into the five terrain feature groups consumed by the matching pipeline. It does not select candidate regions, reproject or resample DEMs, infer vertical datums, or certify mission/vehicle safety.

## Input requirements and fail-closed checks

Each site run requires:

- A stable `site_id`, `planet` (`Earth`, `Moon`, or `Mars`) and exact `source_id`.
- One DEM, one team-approved AOI polygon, source/product information and an explicit vertical-reference/elevation-unit record.
- A north-up, non-rotated, projected raster whose horizontal units are metres and whose elevation unit is explicitly metres.
- The same approved `analysis_scale_m` for every site in a comparison.
- An explicit `relief_window_m`. The code rounds this to an odd cell window and records both the cell count and actual centre-to-centre span.

The command rejects geographic-degree rasters, non-metre grids, rotated/sheared grids, and grids whose pixel sizes do not match the configured analysis scale. Reprojection, datum transformation, resampling and AOI decisions must be completed upstream and recorded; the module will not silently make them.

AOIs are read from GeoJSON. By default, coordinates are assumed to be WGS84 longitude/latitude as specified by RFC 7946. Set `aoi_crs` in a site entry when the supplied GeoJSON uses a different declared CRS.

## Five feature groups

### 1. Slope

Central finite differences are calculated in the x and y directions using the physical pixel spacing:

\[
\mathrm{slope}_{deg}=\tan^{-1}\!\left(\sqrt{(\partial z/\partial x)^2+(\partial z/\partial y)^2}\right)\frac{180}{\pi}
\]

A slope cell is emitted only when the centre and its four cardinal neighbours are valid. Edges and cells adjacent to NoData remain missing. The table reports median, P90 and P95 in degrees.

### 2. Ruggedness / TRI

The implementation uses the Riley-style eight-neighbour formulation:

\[
TRI_i=\sqrt{\sum_{j\in N_8(i)}(z_j-z_i)^2}
\]

`tri_window_cells = 1` records a one-cell radius (a 3×3 neighbourhood including the centre). TRI is in the elevation unit (metres here). A value is emitted only where the centre and all eight neighbours are valid. The table reports median and P90.

### 3. Local Relief

For each cell, local relief is the moving-window P95 minus P5 of elevation. Windows use only finite cells and require the configured minimum valid fraction (default 80%). The site summary `local_relief_p95_p5` is the median of the local P95–P5 map; `local_relief_p90` is also supplied. The requested physical window, selected odd cell count and actual centre-to-centre span are recorded. This is relative/local relief, not absolute planetary elevation.

### 4. Terrain Distribution

Valid slope cells are divided using explicitly documented analytical classes. Defaults follow the Hiba MVP playbook:

- Low: slope < 10°
- Mid: 10° ≤ slope < 25°
- High: slope ≥ 25°

The output is the percentage of valid slope area in each class. The current pipeline requires a uniform projected metric grid, so every raster cell has equal area and cell-count proportions equal area proportions. Percentages should sum to approximately 100%. These are experiment thresholds, not universal safety limits.

### 5. Spatial Pattern

The MVP spatial metric is the percentage of valid slope area occupied by the largest connected patch with slope ≥ `steep_threshold_deg` (default 25°). Connectivity is explicit: 4-neighbour or 8-neighbour (default). The threshold, connectivity and denominator are written into the output. The AOI boundary can split otherwise connected terrain; results are therefore AOI- and scale-dependent.

## Quality, missingness and provenance

The table reports `valid_coverage_pct` and `nodata_pct` from the elevation raster within the AOI. These sum to approximately 100%. Derivative maps have smaller usable footprints because neighbourhood calculations exclude edges and invalid neighbours; their individual usable-cell counts are kept separately.

Missing measurements remain blank/NaN. They are never converted to zero. `direct_observation_coverage_pct` is a separate optional field for products such as LOLA Site04. It must not be conflated with raster-valid coverage: Site04's reported 9.1541% positive LDEC spot-count support does not mean that the other valid interpolated DEM cells are NoData. Uncertainty layers and notes are provenance/quality context and are not silently treated as per-pixel error bounds.

`quality_status` is deliberately conservative: `WARN` means one or more review flags were raised; `REVIEW` means no automated threshold flag was raised, not that the site has passed scientific validation. The module does not produce an `APPROVED` status.

## Outputs

- `data/processed/terrain_fingerprints.csv`: one row per site, compatible with `docs/INTEGRATION_CONTRACT.md`.
- Optional `data/processed/terrain_maps/<site_id>/`: GeoTIFFs for slope, TRI and local relief.
- The row retains product/source identity, CRS, vertical reference, pixel size, AOI coverage, feature definitions, thresholds, window settings and quality notes.

Do not commit large DEMs. Commit only small derived artifacts when the team explicitly agrees; the app reads the canonical processed CSV, not the feature-map GeoTIFFs.

## Run

1. Obtain approved AOI polygons and prepare every site's DEM on the same approved physical grid.
2. Copy `docs/examples/terrain_run.template.json` and fill the global scale/window and each site's paths/metadata.
3. Activate the repository environment and run:

\`\`\`bash
python -m src.features.terrain_fingerprint \
  --config docs/examples/terrain_run.json \
  --output data/processed/terrain_fingerprints.csv \
  --maps-dir data/processed/terrain_maps
\`\`\`

4. Validate the output before handoff:

\`\`\`bash
python -m pytest -q tests/test_terrain_fingerprint.py
\`\`\`

5. Give the CSV and validation report to Omar and Mohammed. Do not ask the application to calculate the features a second time.

## Scientific validation implemented

- Synthetic flat surface: slope, TRI and local relief should be approximately zero.
- Synthetic plane: slope should match the analytical gradient.
- Synthetic bump: TRI should be positive around the perturbation.
- NoData audit: missing cells are not interpolated; derivative support decreases around holes.
- Terrain-class area check: percentages sum to approximately 100%.
- Spatial-pattern test: a connected steep patch is distinguished from separated patches.
- Grid-scale check: mismatched pixel spacing is rejected.
- Separate utilities provide a site-level Spearman correlation audit and a two-scale sensitivity table. They require actual comparable site runs; the functions do not fabricate those runs.

## Known limitations

- No approved target/candidate AOIs or shared analysis scale are embedded in the repository as of this implementation.
- The Earth Copernicus source tiles currently documented in the handover are geographic EPSG:4326 DSMs; they must first be clipped to approved AOIs and warped to a documented local metric grid. Their nominal GLO-30 label is not proof of effective terrain resolution.
- Site04's embedded CRS vertical datum is recorded as unknown in the GIS handover. The catalog's frame description must not be upgraded to a verified vertical datum without a documented transformation/metadata decision.
- The available 5 m LOLA posting is not evidence of 5 m effective terrain resolution or accuracy.
- There is no measured cross-site feature correlation or resolution-sensitivity result until compatible real AOI rasters are supplied.
- DEM-derived topography does not establish lithology, mineralogy, thermal behaviour, ice, subsurface conditions or rover safety.
