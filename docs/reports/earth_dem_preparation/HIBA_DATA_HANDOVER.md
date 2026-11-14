# Earth DEM data handover for Hiba

**Status:** provisional Earth data package. No candidate coordinates, AOIs, analysis scale, or source combination is approved.

## Available now

- Five local Copernicus GLO-30 DSM tiles with matching manifest checksums and QA reports. Their paths and hashes are in `data/metadata/earth_dem_manifest.csv`; tiles are under `data/raw/earth/copdem_glo30/`. Product vertical reference is EGM2008. Quality companions are absent.
- One additional Mauna Kea USGS 3DEP 1 m bare-earth DEM at `data/raw/earth/mauna_kea/usgs_3dep/1m/USGS_1M_4_x86y220_HI_Hawaii_Island_Lidar_NOAA_2017_B17.tif`, SHA-256 `27d730f77f276bad0755ee2b9ab153a5461539b8dd0142bc619b13fc9f8f8b8c`. Horizontal CRS EPSG:26904, NAVD88, meters. The provisional point is only ~150 m from the east edge.
- Haughton ArcticDEM v4.1 and McMurdo REMA v2 STAC coverage candidates, both DSM products with quality/date assets and ellipsoidal heights; neither raster was downloaded.
- ÍslandsDEM v1.0 is documented as a 2 m national product, but exact Askja tile CRS/datum/epoch/terms remain unresolved.
- Yungay ALOS regional coverage excludes the provisional point; SRTMGL1 v003 catalog granule covers it, but was not downloaded.

## Reports and reproducibility records

Read [existing-data audit](existing_data_audit.md), [source comparison](source_comparison.md), [coverage assessment](coverage_assessment.md), [alternative-data QA](alternative_data_qa.md), [candidate-area review](candidate_area_review.md), and `data/metadata/earth_dem_source_inventory.csv`. The existing local Copernicus QA is structural. The alternative USGS QA is structural too and does not prove accuracy. No fingerprints, derived analysis surfaces, or cross-datum elevation comparisons were made.

## Decisions requested from Hiba/team

1. Which terrain variables will the pipeline require?
2. What spatial extent is needed at each candidate site, and who confirms exact site coordinates and landform boundaries?
3. What analysis scale is appropriate? No scale is assumed here.
4. What uncertainty and data-quality evidence are acceptable?
5. Are DSMs acceptable, or is a bare-earth DTM required?
6. Which common horizontal coordinate reference and vertical reference are required, and what transformation sources are acceptable?
7. Must all sites use one source/product type, or may provider and surface type vary by site?

Until these decisions are made, use the source metadata for pipeline interface planning only. Do not treat nominal pixel posting as effective terrain resolution or infer comparable local quality from a common product label.
