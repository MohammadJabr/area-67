# NASA LOLA South-Pole ROI and Multi-Site Workflow

**Status:** Acquisition and inventory tooling for source-published lunar regions of interest. The provider's boundaries are not automatically AREA 67-approved AOIs.

## Why this matters

AREA 67 initially used Site04 (Shackleton rim) as a provisional lunar target. NASA GSFC PGDA publishes high-resolution LOLA products for several south-pole candidate regions, plus ROI shapefile archives for five sites:

- Site01 — Connecting ridge
- Site04 — Shackleton rim
- Site06 — Nobile rim 1
- Site07 — Peak near Shackleton
- Site11 — de Gerlache rim

The official product page describes LDEM, XYZI point clouds, LDEC direct-shot counts, slope, total-height RMS uncertainty, slope RMS uncertainty, 100 clones, and (for these five sites) ROI archives. The GeoTIFF products are described as 5 m/pixel south-polar stereographic grids in the MOON_ME / DE421 frame. The page also explicitly notes that roughly 90% of 5 m pixels are interpolated because LOLA has gaps between tracks and shots. Thus nominal posting is not effective terrain resolution, and raster-valid coverage must not be substituted for direct-observation support.

Source: https://pgda.gsfc.nasa.gov/products/78  
Dataset index: https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/

## An important target-selection insight

The PGDA product description reports that, for the illumination analysis interval 2024-01-01 to 2026-01-01, Site01 had the largest area with average illumination above 70% at 1 m above the surface among the listed regions; it also reports longer continuous illumination at 5 m above the surface for Site01. This makes Site01 a high-value alternative to examine for sustained surface operations. It does not establish Site01 as the best base site overall: resource access, thermal conditions, topography, communications, hazards, and uncertainty still require separate evidence.

Site04 remains valuable because its rasters are already acquired and QA-inspected locally. It should not remain the only target by default.

## What is implemented in this repository branch

### ROI archive downloader and inspector

Tool: **src/data/lola_roi_acquisition.py**

- Allow-lists only the five ROI archives linked from the official PGDA page.
- Requires explicit --confirm-download.
- Enforces a configurable download-size limit and checks gzip/tar structure.
- Never overwrites an existing archive or partial download.
- Extracts regular files and directories; records relative symbolic links in an extraction manifest but never creates or follows them. Hard links and special files are rejected.
- Rejects absolute paths, parent traversal, duplicate case-insensitive paths, and extraction-manifest path collisions.
- Stages extraction and publishes only after validation. The inspection report surfaces every skipped symbolic link as a review warning.
- Inventories every .shp through GeoPandas, recording feature count, CRS, geometry types, bounds, empty/invalid geometries, fields, and native-CRS area when projected.
- Does not reproject, repair, clip, simplify or label any geometry as an approved AREA 67 AOI.

Download the five small ROI archives after reviewing the site list:

~~~bash
python src/data/lola_roi_acquisition.py download --sites Site01 Site04 Site06 Site07 Site11 --confirm-download
~~~

Safely extract and inspect them:

~~~bash
python src/data/lola_roi_acquisition.py inspect --sites Site01 Site04 Site06 Site07 Site11
~~~

Outputs:
- Original archives: data/raw/moon/roi_archives/<SiteID>/
- Extracted source shapefiles: data/raw/moon/roi_shapes/<SiteID>/
- Inspection reports: data/metadata/lola_rois/<SiteID>_roi_inspection.json
- Extraction manifest (including skipped symbolic links): data/raw/moon/roi_shapes/<SiteID>/archive_extraction_manifest.json

### Multi-site LOLA raster downloader

Tool: **src/data/lola_south_pole.py**

Supports the same five sites and the five catalog-listed raster layers:

- elevation
- counts
- slope
- z_uncertainty
- slope_uncertainty

The original Site04 rasters are recognized and left unchanged if already present. No clones or point-cloud files are downloaded.

For a first alternative-target comparison, Site01 is the recommended next acquisition because NASA's PGDA page explicitly highlights its illumination context. Review the selection and then download the five listed rasters:

~~~bash
python src/data/lola_south_pole.py download --sites Site01 --assets elevation counts slope z_uncertainty slope_uncertainty --confirm-download
~~~

Inspect and run the same exact-grid / LDEC / uncertainty QA used for Site04:

~~~bash
python src/data/lola_south_pole.py inspect --sites Site01 --assets elevation counts slope z_uncertainty slope_uncertainty
python src/data/lola_south_pole.py qa --sites Site01
~~~

Outputs:
- Raw site rasters: data/raw/moon/site01/
- Inspection and QA JSON: data/metadata/lola_south_pole/

Each file has a per-file safety ceiling (default 100 MiB), TIFF signature check, raster metadata check, SHA-256, partial-download cleanup, and no-overwrite behavior. Multi-site/multi-layer batches continue after an individual asset failure, preserve successful files, report every failed site/layer pair, and return a nonzero exit code when any asset fails. Do not commit source rasters.

## How to interpret the ROI inspection

The ROI shapefile report is an inventory, not a scientific verdict. For each ROI layer, review:

1. **CRS** — confirm the declared coordinate reference. Never guess a missing CRS.
2. **Feature count and properties** — identify whether features are candidate regions, subregions, or another provider-defined geometry class.
3. **Geometry type and validity** — inspect empty or invalid features; the tool reports them but does not repair them.
4. **Bounds and area** — area is reported only in native projected units squared. If the source uses a geographic CRS, area is left null rather than calculated in degrees squared.
5. **Raster overlap** — the next GIS step must verify that each provider ROI intersects the corresponding raster footprint and calculate valid/direct-observation/uncertainty support within each polygon.

Do not assume the archive contains one polygon, that all polygons represent comparable landforms, or that the provider's ROI is the precise AREA 67 analysis boundary. Inspect the actual attributes and geometries first.

## Target library beyond the five ROI archives

The same PGDA page also lists other south-pole products, including Site20 / Site20v2 (Leibnitz beta plateau), Site23 (Malapert massif), Site42 (de Gerlache–Kocher massif), Haworth, Shoemaker, DM1/DM2, SL2/SL3, NPA/NPB/NPC/NPD and LM1–LM8. These expand the candidate-target catalogue; the new downloader intentionally does not expose them until their exact asset/ROI availability and metadata are separately confirmed.

## Scientific safeguards

- PGDA's LDEM is surface-interpolated. Record LDEC shot counts separately from the valid raster mask.
- Preserve the RMS Z and slope uncertainty products alongside the elevation and slope layers.
- The PGDA page's track geolocation uncertainty, interpolated fraction, and reported ROI-level RMS summaries describe different things; do not collapse them into one quality score.
- Do not compare absolute lunar and Earth elevation values as though the vertical reference frames were equivalent.
- Do not infer effective resolution from the 5 m posting.
- Provider ROIs, target sites, and NASA illumination studies inform target selection; they do not certify a permanent lunar base.
- Any Earth–Moon candidate comparison still requires documented Earth ROIs, compatible analysis scales/windows, validated metrics, explicit uncertainty policy, and team-approved tolerances.

## Recommended next analytical sequence

1. Download and inspect the five ROI archive geometries.
2. Compare Site04 and Site01 ROI coverage, direct LOLA support, RMS Z uncertainty, slope uncertainty and illumination context.
3. Decide which ROI(s) and which site(s) the team wants to carry into the first terrain-fingerprint baseline.
4. Only after those decisions, prepare matching Earth ROIs and compatible analysis grids.
5. Produce real fingerprints and run the matcher; retain separate evidence dimensions and limitations in each Analog Passport.
