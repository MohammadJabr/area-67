# AREA 67 GIS handoff: provisional LOLA Site04

## Status and data available

The provisional lunar study area is NASA LOLA **Site04 (Shackleton rim)**. The
team has not officially finalized this target. Five local NASA GSFC PGDA
GeoTIFF assets are available under `data/raw/moon/site04/`:

| Alias | Local file suffix | Meaning / units stated by PGDA |
|---|---|---|
| `elevation` | `Site04_final_adj_5mpp_surf.tif` | Surface-interpolated LDEM surface height Z, meters |
| `counts` | `Site04_final_adj_5mpp_ldec.tif` | LDEC: number of LOLA spots per pixel |
| `slope` | `Site04_final_adj_5mpp_slp.tif` | Slope, degrees |
| `z_uncertainty` | `Site04_final_adj_5mpp_toterr.tif` | Total elevation uncertainty, RMS error in meters |
| `slope_uncertainty` | `Site04_final_adj_5mpp_slperr.tif` | Slope uncertainty, RMS error in degrees |

The authoritative catalog is <https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/>. It
describes these products as 5 m/pixel GeoTIFFs in south polar stereographic
X/Y coordinates (meters) and the MOON_ME frame of JPL DE421. Barker et al.
(2021) describe the adjusted Site04 product and uncertainty approach:
<https://doi.org/10.1016/j.pss.2020.105119>.

The local files are single-band float32 and each is 3200 × 3200. They share an
identical transform, bounds, CRS WKT, and valid mask. Their embedded CRS uses
an unnamed spherical datum and explicitly says datum unknown; the catalog's
MOON_ME/DE421 frame statement should not be misrepresented as a fully verified
vertical datum. The NoData sentinel is NaN; the GDAL mask marks zero pixels
invalid, and all 10,240,000 values per raster are finite and unmasked. The 5 m
posting is nominal pixel spacing, not demonstrated effective terrain
resolution or accuracy.

LDEC is critical to interpreting coverage: **9.1541%** of valid cells have a
positive LOLA spot count; **90.8459%** have zero count and interpolated LDEM
elevation. A 100% valid-data mask therefore does not mean complete direct
instrument observation. The uncertainty layers are RMS estimates, not
guaranteed per-cell error bounds. See the reports for full distributions and
spatial screening. The current five local rasters total 204,903,932 bytes;
keep them local and out of Git.

## Reproduce acquisition, inspection, and QA

Run from the repository root using the project environment. The acquisition
script refuses to overwrite existing data and only accepts the listed asset
aliases. It does not select optional clone products.

```powershell
.\.venv\Scripts\python.exe src/data/lola_site04.py download --assets elevation counts slope z_uncertainty slope_uncertainty --confirm-download
.\.venv\Scripts\python.exe src/data/lola_site04.py inspect --assets elevation counts slope z_uncertainty slope_uncertainty --report data/metadata/site04_inspection.json
.\.venv\Scripts\python.exe src/data/lola_site04_qa.py
.\.venv\Scripts\python.exe -m pytest -q
```

If the five rasters already exist, download reports them as present and leaves
them unchanged. The inspect command reports file/grid metadata and descriptive
statistics. The QA command requires all five assets and checks exact grid
metadata alignment, valid masks, finite values, layer value screens, LDEC
support, and relative uncertainty/support tiles.

## Reports and source record

- `data/metadata/data_manifest.csv`: catalog metadata plus verified local
  NoData and valid coverage; unknown release/version/datum fields are not
  guessed.
- `data/metadata/site04_inspection.json`: local per-raster metadata and basic
  statistics.
- `data/metadata/site04_qa.json`: detailed machine-readable QA, grids, masks,
  distributions, LDEC classes, and tile rankings.
- `data/metadata/site04_qa.md`: human-readable QA summary and main tile tables.
- `docs/LOLA_SITE04_WORKFLOW.md`: source and processing notes.

The JSON/Markdown reports are small derived metadata artifacts. The large
source GeoTIFFs, archives, partial downloads, environments, and caches are
excluded from Git by `.gitignore`.

## Downstream handoff

### Hiba: terrain analysis and validation

- Confirm feature definitions, physical neighborhood sizes, slope classes,
  and scale-sensitivity plan before deriving slope distributions, TRI, local
  relief, terrain classes, or spatial pattern.
- Decide how zero-count/interpolated cells and uncertainty will affect each
  feature and validation. Preserve the LDEC and RMS layers alongside the DEM.
- Treat `5 m/pixel` as posting only; do not imply 5 m effective terrain
  resolution. Validate derived features with synthetic surfaces and document
  comparison limitations because the exact catalog slope operator/window is
  not specified.

### Omar: similarity and mission planning

- A mission profile, selected Earth candidates, their DEM sources, and
  comparable physical analysis scales are still needed before matching.
- Match terrain descriptors at compatible effective scales and account for
  the lunar interpolated fraction and uncertainty. Do not compare raw lunar
  and Earth elevations or treat a score as mission-success probability.
- No Earth candidate DEMs have been collected by this GIS contribution.

### Mohammed: application integration

- Use the stable local raster paths and JSON report structures above during
  development; do not expect the large GeoTIFFs to be present in a Git
  checkout. Agree whether app ingestion uses local paths, generated summaries,
  or a later managed data source.
- Keep the provisional-site label, data provenance, and quality caveats visible
  wherever derived results are presented.

## Still missing / unresolved

- Official team approval of the target and a specific exploration task.
- Earth candidate DEMs and source manifests; no Earth data are included here.
- A final sub-area/ROI definition within the Site04 product footprint.
- Product release/version and exact source access date in the manifest.
- An unambiguous embedded lunar datum/vertical reference; the raster WKT says
  unknown, while PGDA identifies the catalog frame as MOON_ME/DE421.
- Exact numerical method/window used for the catalog slope product and a
  demonstrated effective-resolution/accuracy estimate for this footprint.
- Usage/license terms were not verified in this workflow and should be
  checked against the source before redistribution.
- Terrain fingerprints, Earth–Moon matching, mission routes, and Analog
  Passports are downstream work, not outputs of this GIS contribution.
