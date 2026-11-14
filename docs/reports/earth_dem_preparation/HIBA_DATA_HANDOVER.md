# Earth DEM data handover for Hiba — Phase 2

**Status:** source data and reference points remain provisional. No site, AOI, common analysis scale, or source mix is approved.

## Available now

- Five local Copernicus GLO-30 DSM tiles and their structural QA, hashes, and manifest entries under `data/raw/earth/copdem_glo30/` and `data/metadata/earth_dem_qa/`. Product heights are EGM2008 meters; quality companion layers are not local.
- Two Mauna Kea USGS 3DEP 1m bare-earth tiles, both QA-inspected:
  - x86y220, `data/raw/earth/mauna_kea/usgs_3dep/1m/USGS_1M_4_x86y220_HI_Hawaii_Island_Lidar_NOAA_2017_B17.tif`, 270,812,447 B, SHA-256 `27d730f77f276bad0755ee2b9ab153a5461539b8dd0142bc619b13fc9f8f8b8c`, EPSG:26904.
  - x24y220, `data/raw/earth/mauna_kea/usgs_3dep/1m/USGS_1M_5_x24y220_HI_Hawaii_Island_Lidar_NOAA_2017_B17.tif`, 224,245,197 B, SHA-256 `7d5b7020995ee5557bde2129d3a8b3ec25ebe3249ea41ed7e2ee6a9969f6d7f1`, EPSG:26905.
  - Both use 1m grids and product metadata identifies NAVD88 meters. They geometrically overlap around the provisional point, but their grids/CRSs differ. Any pipeline handoff needs an approved CRS and preparation method. Raw files are gitignored.
- Haughton ArcticDEM v4.1 item `29_29_2_2_2m_v4.1` was remotely inspected: DEM and MAD/count/date/datamask COG windows read successfully by HTTP ranges. No raster was saved locally.
- McMurdo REMA v2.0 items `18_35_1_1_2m_v2.0` and `17_35_2_1_2m_v2.0` were remotely inspected with DEM and MAD/count/date windows. Wright reference lies in the first item's geometry; Victoria reference lies in the second; the stated Taylor reference lies in neither. No raster was saved locally. Please choose the intended valley before we make candidate-coverage claims.
- Askja has a remotely inspected 500×500 window from the official ÍslandsDEM v1.0 10m national GeoTIFF. Horizontal CRS is EPSG:8088. The filename says zmasl and official metadata says IceGeoid was used; a formal vertical CRS is not confirmed in the file. Its lidar-date companion had no valid Askja sample and its WKT says Islands_Net_1993 despite an isn2016 filename. The direct 2m source-tile ID remains unresolved.
- Yungay SRTMGL1 v003 catalog granule S25W070 covers the provisional coordinate, but was not downloaded. The exact field plot is unconfirmed. The regional ALOS Atacama product excludes the provisional coordinate.

## Reports, imagery and QA

See [existing-data audit](existing_data_audit.md), [source comparison](source_comparison.md), [coverage assessment](coverage_assessment.md), [alternative-data and remote QA](alternative_data_qa.md), [site location verification](site_location_verification.md), and [candidate review](candidate_area_review.md). Figures are under `figures/`. The machine-readable inventory is `data/metadata/earth_dem_source_inventory.csv`; remote window metadata is `data/metadata/earth_dem_qa/remote/targeted_cog_access_2026-11-15.json`.

Structural QA is not scientific validation. A 100% valid mask does not prove accuracy. Product posting is not effective terrain resolution. Elevations from the different datums were not compared.

## Decisions requested from Hiba/team

1. Which terrain variables will the future pipeline require?
2. What exact geographic extent/landform is required at each site, and who confirms the location? For McMurdo, name the valley. For Yungay, confirm the exact field station/plot.
3. What analysis scale is appropriate? No value is assumed here.
4. What local uncertainty and quality evidence are acceptable?
5. Are DSM products acceptable, or does a site require a bare-earth DTM?
6. Which common horizontal CRS and vertical reference are required? What authoritative transformations should be used?
7. Must all five sites use the same provider/surface type, or can sources differ by site?
8. Should the Iceland 10m national product be retained for preliminary screening while the exact 2m Askja tile is resolved?

Until these decisions are made, the local tiles and remote previews are provenance/availability evidence only. Do not treat display windows as analysis inputs or derive fingerprints from the full tile extents.
