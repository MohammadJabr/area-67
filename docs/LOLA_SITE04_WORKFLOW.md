# Provisional lunar DEM workflow: LOLA Site04

**Study-area assumption:** NASA LOLA Site04, identified by the source catalog as
the Shackleton rim. This is a provisional working choice, not an officially
approved AREA 67 team decision.

## Verified source and products

NASA GSFC's Planetary Geodesy Data Archive (PGDA) catalog lists Site04 products
at <https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/>. It describes these GeoTIFFs as
5 m/pixel, with south polar stereographic X/Y coordinates in meters and the
MOON_ME reference frame of JPL DE421. The catalog describes the LDEM as a
surface-interpolated elevation map whose values give surface height Z in
meters. Those catalog statements are source metadata; the actual downloaded
file's CRS, dimensions, NoData value, coverage, and values must be inspected
locally before being reported as verified for that file.

| Script asset | Catalog file | Meaning stated by PGDA |
|---|---|---|
| `elevation` | `Site04_final_adj_5mpp_surf.tif` | Surface-interpolated elevation (LDEM) |
| `counts` | `Site04_final_adj_5mpp_ldec.tif` | Number of LOLA spots per pixel (LDEC) |
| `slope` | `Site04_final_adj_5mpp_slp.tif` | Slope in degrees |
| `z_uncertainty` | `Site04_final_adj_5mpp_toterr.tif` | Total Z uncertainty, RMS error in meters |
| `slope_uncertainty` | `Site04_final_adj_5mpp_slperr.tif` | Slope uncertainty, RMS error in degrees |

The catalog also lists XYZI point clouds and 100 elevation clones. The current
workflow deliberately excludes those optional products; it never downloads
them implicitly. Product URLs are constructed only from the catalog-listed
base URL and filenames above.

## Download

Run from the repository root after reviewing the assets that will be fetched.
Downloads are streamed to `data/raw/moon/site04/` and are ignored by Git. There
is no default download selection, and the explicit acknowledgement flag is
required:

```powershell
.venv/Scripts/python.exe src/data/lola_site04.py download --assets elevation --confirm-download
```

To include the catalog's quality layers, name them explicitly, for example:

```powershell
.venv/Scripts/python.exe src/data/lola_site04.py download --assets elevation counts z_uncertainty slope_uncertainty --confirm-download
```

The slope layer is also catalog-listed, but should only be fetched if needed;
it is a derived layer, while this project's terrain metrics should generally
be computed from the elevation raster under documented parameters. The NASA
catalog listing reviewed for this workflow does not state individual file
sizes. The script reports actual byte counts after download; no size is
assumed here. Handled failures and Ctrl+C remove the partial file. If the
process is forcibly terminated, a `.part` file may remain; the script
preserves it and refuses to overwrite it. Existing completed files are left
unchanged.

## Inspect

Inspection requires `numpy` and `rasterio`, both listed in `requirements.txt`.
It reads rasters block-by-block and reports actual file size, dimensions,
bands, dtype, NoData, CRS, transform, bounds, pixel spacing, valid coverage,
and band-1 summary statistics. It does not modify source rasters or resample
them.

```powershell
.venv/Scripts/python.exe src/data/lola_site04.py inspect --assets elevation counts slope z_uncertainty slope_uncertainty
```

The JSON report is written to `data/metadata/site04_inspection.json`. It uses
strict JSON (`NaN` NoData is serialized as the string `"NaN"`) and includes
separate GDAL-mask and non-finite counts. Inspection results must not be
described as downloaded or verified until the command has been run
successfully against local files.

## Quality assurance

After all five assets are present, run the QA stage from the repository root:

```powershell
.venv/Scripts/python.exe src/data/lola_site04_qa.py
```

It compares CRS WKT, dimensions, transform, and bounds exactly; checks the
GDAL masks and finite-value masks pixel by pixel; summarizes NoData, non-finite
values, layer distributions and physical-value flags; interprets LDEC positive
and zero cells separately; and ranks 500 m tiles by direct count support and
uncertainty. It writes `data/metadata/site04_qa.json` and
`data/metadata/site04_qa.md`. The tile and p95 rankings are relative QA aids,
not scientific acceptance thresholds. Synthetic-raster tests run with:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_lola_site04_qa.py -q
```

## Current manifest status

`data/metadata/data_manifest.csv` records catalog-stated source/product
information and locally inspected NoData and valid coverage. Product version
and release/access date remain blank because they were not verified. The
embedded raster CRS is unnamed and identifies the datum as unknown; the
catalog separately states the MOON_ME/DE421 frame. Do not treat these as proof
of a fully identified vertical datum.

## Limitations and reproducibility

- The named source describes Site04 as the Shackleton rim; confirm that the
  product's footprint suits the team's final area-of-interest definition.
- The raster posting is 5 m/pixel; that is not proof of 5 m effective terrain
  resolution or measurement accuracy. The count map shows only about 9.15% of
  valid pixels contain a positive LOLA spot count; zero-count LDEM cells are
  interpolated.
- Keep elevation and uncertainty/count layers paired during later processing.
- Preserve the original rasters; record any masks, clipping, reprojection,
  resampling, or derived features separately.
- This workflow acquires and inspects the provisional lunar target. No Earth
  candidate DEMs have been collected, and AREA 67 terrain fingerprints have
  not been computed by this GIS contribution.
