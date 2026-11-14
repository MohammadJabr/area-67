# Existing Earth DEM audit

**Audit date:** 2026-11-14. Site coordinates and candidate areas remain provisional. This audit reads original rasters only.

Five local Copernicus GLO-30 DSM tiles were cross-checked against `data/metadata/earth_dem_manifest.csv`, each site JSON/Markdown report under `data/metadata/earth_dem_qa/`, and direct raster metadata. All five local SHA-256 values, file sizes, dimensions, EPSG:4326 CRS, one Float32 band, transforms, and bounds agree with the recorded QA. All coordinates lie within their respective raster bounds. Files have no declared NoData; the GDAL mask reports 100% valid cells, which is not evidence of physical data quality. No Copernicus quality companion layers are present locally.

| Site | Raster | Bytes | Grid | Bounds (west, south, east, north) | Elevation range (m) | Nearest tile edge |
|---|---|---:|---|---|---:|---:|
| Haughton | `data/raw/earth/copdem_glo30/haughton/Copernicus_DSM_COG_10_N75_00_W090_00_DEM.tif` | 11,558,351 | 1200×3600; 3×1 arc-sec | -90.0004167, 75.0001389, -89.0004167, 76.0001389 | -0.1999 to 413.1628 | 8.95 km west |
| McMurdo | `data/raw/earth/copdem_glo30/mcmurdo/Copernicus_DSM_COG_10_S78_00_E162_00_DEM.tif` | 13,702,247 | 1200×3600; 3×1 arc-sec | 161.9995833, -77.9998611, 162.9995833, -76.9998611 | -0.3908 to 3203.2175 | **10.1 m west** |
| Askja | `data/raw/earth/copdem_glo30/askja/Copernicus_DSM_COG_10_N65_00_W017_00_DEM.tif` | 20,729,649 | 1800×3600; 2×1 arc-sec | -17.0002778, 65.0001389, -16.0002778, 66.0001389 | 39 to 1575.9492 | 3.66 km south |
| Mauna Kea | `data/raw/earth/copdem_glo30/mauna_kea/Copernicus_DSM_COG_10_N19_00_W156_00_DEM.tif` | 31,714,695 | 3600×3600; 1×1 arc-sec | -156.0001389, 19.0001389, -155.0001389, 20.0001389 | -2.9216 to 4204.2373 | 19.94 km north |
| Yungay | `data/raw/earth/copdem_glo30/yungay/Copernicus_DSM_COG_10_S25_00_W070_00_DEM.tif` | 37,362,492 | 3600×3600; 1×1 arc-sec | -70.0001389, -24.9998611, -69.0001389, -23.9998611 | 898.7391 to 4347.0195 | 7.13 km north |

The product is a digital surface model, not a guaranteed bare-earth DTM. Product documentation identifies EGM2008 heights and meters; exact package release is not identified in local filenames. Nominal product posting is not effective terrain resolution. Source dates and local per-cell uncertainty are unavailable. Copernicus product information describes quality/editing layers, but these companion layers were not acquired.

**Coverage risks:** McMurdo's manifest coordinate is approximate and almost on the western raster boundary; it does not identify which Dry Valley is intended. Haughton and Askja candidate landforms may reach beyond their present tile margins. Mauna Kea and Yungay have larger margins but a point alone cannot establish full landform coverage. QA JSON and Markdown reports use repository-relative paths so the screening workflow is reproducible from another checkout. The source rasters themselves remain local and gitignored.

See [source inventory](../../../data/metadata/earth_dem_source_inventory.csv) for per-source provenance and `data/metadata/earth_dem_qa/` for exact hashes and raster statistics.
