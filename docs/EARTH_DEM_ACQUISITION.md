# Earth DEM acquisition and preparation

**Branch:** `feature/ghassan-earth-dem-ingestion`
**Status:** Candidate source inventory and reproducible source-tile acquisition. The named places and downloaded 1° tiles are provisional coverage checks, not approved study ROIs or processed analysis rasters.

## Candidate coverage check

The following landmark coordinates are only used to identify a source tile. The complete source tiles are much larger than a future candidate ROI; they must not be treated as candidate boundaries or sent to fingerprint calculations without team decisions.

| Candidate | Coordinate used to identify tile | Tile ID | Provisional source product | Strength / limitation |
|---|---|---|---|---|
| Haughton Crater, Devon Island | 75°22′N, 89°41′W (Planetary Science Institute) | `Copernicus_DSM_COG_10_N75_00_W090_00_DEM` | Copernicus GLO-30 | GLO-30 covers the location; ArcticDEM v4.1 is a more local high-resolution alternative. SRTM does not cover this latitude. |
| McMurdo Dry Valleys | approximately 77°30′S, 162°00′E (Antarctic Treaty management plan) | `Copernicus_DSM_COG_10_S78_00_E162_00_DEM` | Copernicus GLO-30 | GLO-30 provides a common global product. REMA v2 is the regional high-resolution alternative. SRTM does not cover Antarctica. |
| Askja, Iceland | 65.033°N, 16.783°W (Smithsonian Global Volcanism Program) | `Copernicus_DSM_COG_10_N65_00_W017_00_DEM` | Copernicus GLO-30 | Global coverage and public AWS COG access; DSM surface includes vegetation/buildings where present. |
| Mauna Kea, Hawaiʻi | 19.82°N, 155.47°W (USGS Volcano Hazards Program) | `Copernicus_DSM_COG_10_N19_00_W156_00_DEM` | Copernicus GLO-30 | Uniform global-product option. USGS 3DEP is a potentially higher-detail national alternative; exact product coverage/metadata must be checked for the eventual AOI. |
| Yungay, Atacama | 24°05′24″S, 69°55′48″W (published field-site coordinate) | `Copernicus_DSM_COG_10_S25_00_W070_00_DEM` | Copernicus GLO-30 | Global product coverage and public AWS COG access; product is a DSM, and exact site boundary remains unset. |

The candidate coordinates point to named landmarks or research locations; they do not establish the best terrain sub-area for AREA 67. The tiles use a 1° geographic grid. The retrieved tile sizes were 11,558,351; 13,702,247; 20,729,649; 31,714,695; and 37,362,492 bytes, respectively. These figures were verified from HTTP headers before download. Tile extents are broad; no clipping, reprojection, or resampling was performed.

## Product source comparison

Access and product information was reviewed on 2026-11-14. A product-level statement is not a substitute for inspecting the exact downloaded tile metadata and quality assets.

| Product | Coverage / posting | Horizontal and vertical reference / units | Quality and limitations | Access and use |
|---|---|---|---|---|
| **Copernicus DEM GLO-30** | Global land coverage; 1 arc-second grid (nominal GLO-30; east-west ground spacing varies with latitude); 1° tiles. TanDEM-X source imagery was acquired 2011–2015, with other DEMs used for gap filling. | DGED/DTED: WGS84-G1150 geographic coordinates (EPSG:4326); vertical EGM2008 (EPSG:3855); meters. | DSM includes buildings and vegetation. Product documentation reports absolute vertical accuracy <4 m at 90% linear error and relative accuracy <2 m on slopes ≤20%, <4 m on steeper slopes, at 90% within 1°×1° areas. Editing, filling, height-error, and water-body masks are described; companion files were not part of these five tile downloads. A tile’s exact package/release metadata must be recorded from its metadata, not inferred from its filename. | Public GLO-30 COG objects were available in AWS `copernicus-dem-30m`; the public AWS listing says no AWS account is required. Follow Copernicus licence/attribution terms. The CDSE portal has separate registration/access rules. |
| **NASA SRTMGL1 v003** | Near-global land coverage from 60°N to 56°S; 1 arc-second (~30 m at equator). | Geographic coordinates, WGS84; vertical EGM96; meters. | NASA distributes a companion `NUM` layer. Acquisition is from February 2000; do not assume all terrain is bare earth or that nominal posting equals effective resolution. It does not cover Haughton or McMurdo. | LP DAAC/NASA Earthdata distribution; NASA catalog marks it public and links the U.S. Government Works licence. Cite the product DOI. |
| **ASTER GDEM v3 / ASTGTMV003** | 83°N–83°S; 1°×1° tiles; 1 arc-second (30 m) posting. | Geographic coordinates; WGS84/EGM96; DEM values stored as signed 16-bit with 1 m/DN. | Each tile has a DEM and `NUM` quality file; `NUM` counts contributing scenes and records fill source. ASTER scenes were stacked and anomalies corrected; the NASA guide cautions that limited scene counts can leave artifacts. It does not cover McMurdo. Copernicus GLO-30 also uses ASTER among possible fill sources, so these products are not necessarily independent. | LP DAAC / NASA Earthdata; cite DOI `10.5067/ASTER/ASTGTM.003`. Verify current access workflow and licence record when selecting an AOI. |
| **ArcticDEM v4.1 mosaic** | Arctic coverage; 2 m GSD mosaics in 50 km × 50 km tiles; reduced 10 m, 32 m and coarser products also exist. | EPSG:3413; WGS84 horizontal reference; heights above WGS84 ellipsoid; meters. | DSM from optical stereo imagery; seasonal snow/ice and void/artifact risks. Mosaic absolute accuracy specifications are not verified by PGC. Available companion count, MAD, dates, masks, and metadata can support quality review. | PGC HTTP, AWS STAC, and FRIDGE sources. Public data are available with PGC acknowledgement/citation requirements; Alaska data from June 2022 onward are restricted. Haughton is outside that Alaska restriction. |
| **REMA v2 mosaic** | Antarctica; 2 m GSD mosaics in 50 km × 50 km tiles; reduced 10 m, 32 m and coarser products also exist. | EPSG:3031; WGS84 horizontal reference; heights above WGS84 ellipsoid; meters. | DSM from optical stereo imagery; snow, ice, cloud/shadow, and void/artifact limitations. Absolute accuracy of current mosaics is not specified as verified. Count, MAD, date, mask, and metadata products may be available. | PGC HTTP, AWS STAC, FRIDGE, and image services. Public use requires PGC acknowledgement/citation. OpenTopography restricts 2 m access to education/research users; PGC provides other public access routes. |
| **USGS 3DEP** | United States and territories; available product resolutions vary by location. National seamless layers include 1/3 arc-second (~10 m); 1 m production is ongoing and coverage must be checked. | CRS and vertical reference depend on the specific product/tile; inspect its metadata. | Product families include bare-earth DEMs and source DSMs; do not mix surface types without a reason. Source acquisition and quality vary by project. | The National Map offers free downloads/services. Check tile availability, source, CRS, vertical datum, units, and licence/metadata for the exact Mauna Kea AOI. |

ASTER GDEM is recorded as an alternative, not selected for the downloaded common-source tile set. SRTM has partial candidate coverage but cannot support all five named locations. ArcticDEM/REMA are higher-detail regional alternatives but introduce different acquisition, surface, and datum characteristics; selecting a mixed-product final dataset requires Hiba/team review.

## Downloaded source data

Five Copernicus GLO-30 COG tiles were acquired into ignored local paths:

```text
data/raw/earth/copdem_glo30/haughton/
data/raw/earth/copdem_glo30/mcmurdo/
data/raw/earth/copdem_glo30/askja/
data/raw/earth/copdem_glo30/mauna_kea/
data/raw/earth/copdem_glo30/yungay/
```

The authoritative data source URL pattern is:

```text
https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/{tile_id}/{tile_id}.tif
```

`src/data/earth_dem_acquisition.py` downloads only the five named tiles, requires explicit site selection and `--confirm-download`, imposes a per-file size ceiling, refuses existing files/partials, verifies TIFF structure and raster metadata, and reports SHA-256. Original tile files are retained unchanged. The download was a source-availability check for provisional candidate locations, not an approved final candidate dataset.

Reproduce from repository root (review selections first):

```powershell
.\.venv\Scripts\python.exe src/data/earth_dem_acquisition.py --sites haughton mcmurdo askja mauna_kea yungay --confirm-download
```

Per-tile HTTP source IDs, sizes, checksums, CRS, dimensions, valid coverage, and statistics are recorded in `data/metadata/earth_dem_manifest.csv` and QA reports under `data/metadata/earth_dem_qa/`.

## Raster inventory and QA

- `src/data/raster_inventory.py` inventories explicit rasters without changing them. It reports raster dimensions, bands, types, CRS/WKT, transform, bounds, CRS-unit pixel spacing, NoData/masks, finite-value coverage, tags, per-band statistics, and streaming SHA-256. `inventory_many()` compares exact grid signatures; it does not reproject inputs.
- `src/data/earth_dem_qa.py` checks a primary DEM and any explicitly supplied companion quality rasters. It reports grid mismatches and structural warnings. Elevation-range screening is optional and clearly labelled a configured review screen, not a universal threshold.
- Neither utility infers vertical datum, elevation unit, effective terrain resolution, or science suitability from the horizontal CRS or pixel size. Verify those in provider metadata and record them in the source manifest.
- Report output paths are explicit CLI options. With no output arguments, QA writes JSON to stdout only.

Example:

```powershell
.\.venv\Scripts\python.exe src/data/earth_dem_qa.py data/raw/earth/copdem_glo30/askja/Copernicus_DSM_COG_10_N65_00_W017_00_DEM.tif --json data/metadata/earth_dem_qa/askja.json --markdown data/metadata/earth_dem_qa/askja.md
```

## Preparation and Hiba handoff

The acquired files are native source COGs. They are not yet AOI-clipped, projected to a common CRS, resampled, or converted to fingerprints. No final analysis scale was selected. Do not pass a full 1° tile to feature extraction as though it were the agreed candidate area.

Before deriving a fingerprint, the team must decide:

1. Which candidate regions to retain and the exact ROI boundary/area for each.
2. Whether GLO-30 DSM surface values are acceptable for each candidate, or whether regional bare-earth/high-resolution products should replace them.
3. The common physical analysis scale and corresponding preparation method after considering the lunar product’s unknown effective resolution.
4. Whether and how to use Copernicus editing/filling/height-error/water masks and any source uncertainty.
5. Whether to reproject/crop and how to preserve vertical references and source quality through preparation.

The minimal handoff is: original COG(s), `data/metadata/earth_dem_manifest.csv`, matching JSON/Markdown QA reports, and this document. Derived working rasters should be stored separately from originals and created only after the scale/ROI decision. Hiba owns the fingerprint algorithms and output `data/processed/terrain_fingerprints.csv`; GIS supplies documented source rasters and quality/provenance.
