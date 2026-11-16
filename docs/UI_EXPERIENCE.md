# AREA 67 — Interactive Mission Console

## Experience structure

The Streamlit application is organized as five mission-oriented workspaces:

1. **Mission Control** — selected planetary target and mission profile, project status, current Earth candidate references, scientifically approved AOI count, and available Mars records.
2. **Analog Radar** — matcher-supplied Earth candidate ranking, candidate-card/table switch, relative-index chart, candidate filtering and spotlight, and the interactive Earth reference-anchor map.
3. **Terrain Lab** — side-by-side five-group terrain fingerprint tables, single-parameter exploration, matcher-supplied feature contributions/differences, focus-site quality metrics, and data-quality/provenance comparison.
4. **Planetary Atlas** — nested Earth, Moon and Mars workspaces. Earth provides bounded Copernicus reference-window overlays and a user-drawn AOI workbench; Moon provides NASA LRO WAC global tiles plus a bounded Site01 LOLA raster lab; Mars provides NASA MOLA/Viking global tiles. Visual layers are separate from scored matching inputs.
5. **Analog Passport** — selectable target/candidate dossier, readable terrain evidence tables, target-to-candidate comparison, source lineage, quality caveats, matching assumptions, and Markdown/ZIP evidence export.

Target and mission-profile controls live in the sidebar. Options are populated only from the loaded ranking CSV. Candidate filters operate on the supplied matcher rows; they do not recalculate scores or alter the source ranking. The candidate count shows filtered and total available candidates so intentional filtering is not mistaken for missing data.

## Interactive Earth map

- The Analog Radar displays Earth reference-window anchors on a PyDeck map.
- Users can switch between dark, light and voyager CARTO basemaps, focus one candidate, show or hide labels, pan/zoom, and hover over candidate markers.
- Marker attributes are taken from the supplied fingerprint and ranking outputs: site name, rank, relative match index, weighted distance and reference coordinates.
- Marker focus and filters affect the displayed view only; they do not alter the ranking.
- The map is deliberately Earth-only. Lunar/Martian coordinates are never plotted on an Earth basemap.
- Markers identify reference-window anchors only. They are not approved study-area boundaries or AOI polygons.
- Public CARTO basemap tiles are loaded at runtime; internet access is required for the background map.

## Planetary map resources

- **Earth:** the in-app Analog Radar map is the project-native view of the current Haughton, Yungay and Mauna Kea reference-window anchors.
- **Moon:** the Planetary Atlas links to [NASA Moon Trek](https://trek.nasa.gov/moon/), a public lunar surface explorer with LRO WAC mosaics, polar map views and searchable lunar data products. Some advanced analysis functions may require a registered research account.
- **Mars:** the Planetary Atlas links to [NASA Mars Trek](https://trek.nasa.gov/mars/), which provides global and regional Mars map products, including MOLA, THEMIS, Viking, HRSC and higher-resolution regional imagery where available.
- The Moon Trek and Mars Trek pages are external data-exploration resources. Opening them does not add those products to AREA 67's ranking engine.
- A layer becomes an AREA 67 analytical input only after its exact product, instrument, coordinate frame, scale, units, observation context, quality metadata and processing method are recorded and validated.

## Terrain evidence and explanations

- The Terrain Lab shows the five canonical groups: Slope, Riley 8-neighbour TRI, Local Relief, Terrain Distribution, and Spatial Pattern.
- The single-parameter explorer plots the actual supplied numeric measurement for the selected metric across the selected target/candidate rows.
- The feature-contribution chart uses only matching-engine output columns. It explains the current weighted comparison and must not be described as a percentage of physical similarity.
- Data-quality fields keep valid raster coverage, NoData and direct instrument-observation support separate. Missing direct support remains "Not supplied", not zero.
- Mission Control makes evidence gaps visible rather than adding fictional target/candidate options.

## Analog Passport and exports

- The Passport uses readable field/value tables rather than exposing raw JSON as the main presentation.
- Markdown export is available for a human-readable report.
- ZIP evidence export contains the Markdown Passport, structured Passport JSON, selected terrain fingerprint CSV, and matching-result CSV when supplied. Raw raster files are intentionally not included.
- The export documents synthetic demo mode when applicable and retains source/AOI/quality caveats.

## Scientific integrity in the UI

- Real-data rows remain labelled **EXPLORATORY REAL-DATA PILOT** until AOIs, frames, grid/scale policies and study settings are approved.
- Synthetic fallback is labelled **SYNTHETIC DEMO · NOT MEASURED**.
- The current historical ranking set contains Haughton, Yungay and Mauna Kea; it differs from the frozen intended Haughton, Askja and Mauna Kea shortlist. Yungay remains provisional.
- The Site01 analysis window is not an approved geomorphic AOI. Its positive LOLA LDEC support is distinct from valid elevation-mask coverage.
- Similarity index is not a probability, physical-equivalence percentage, certification or rover-safety measure.
- Missing features and unknown provenance remain missing; the interface does not fill gaps.
- No terrain raster overlay, hillshade, slope heatmap or 3D terrain surface is shown because the app does not currently have approved study AOIs plus validated, hosted raster derivatives.
- Do not infer a lunar map pin from an unverified local coordinate frame. The current project-native map intentionally plots only Earth reference anchors.

## Visual system

- Deep-space background with layered gradients, glass-like panels and restrained cyan/lime highlights.
- Consistent spacing, rounded cards, clear typographic hierarchy, and responsive layouts for narrow screens.
- Ranking cards foreground rank, matcher-supplied relative index, weighted distance and supplied ranking notes.
- Ranking charts use candidate names, explicit rank colors and visible numeric labels.
- The theme is stored locally in `app/theme.css`. Public CARTO tiles are the map background provider.

## Implementation notes

- The application does not change the data contracts, source rasters, fingerprint formulas, matching weights, tolerances, candidate IDs or tracked ranking values during UI rendering.
- Candidate-card values, map attributes and feature-contribution values are rendered from supplied matcher/fingerprint outputs.
- The detailed data table remains available as an alternate ranking view.
- Local entry point: `python -m streamlit run app/main.py`.


## Earth Terrain Explorer and AOI Workbench

- Candidate maps are centered on the published/provisional reference anchors in the source catalogue: Haughton, Askja, Mauna Kea and the held Yungay published-study reference.
- Optional bounded reference-window reads query public Copernicus GLO-30 COGs using GDAL/Rasterio HTTP range reads. The UI can show elevation, slope derived from that bounded preview, or hillshade derived from the same display grid.
- Preview window choices are 990 m, 1,980 m, 2,970 m or 4,950 m at a 30 m display grid. These are visualization dimensions, not approved study AOIs, and display derivatives do not update canonical fingerprints or matching CSVs.
- The image overlay is displayed in a geographic bounding envelope for usability. It is not a new analysis raster or a replacement for the exact source grid.
- Users can draw polygons/rectangles in the interactive Leaflet map. Draft export requires a named geomorphic unit, a mission/science question and optional source-map provenance.
- Draft AOI export validates Polygon/MultiPolygon type, topology, WGS84 coordinate bounds and containment inside the currently catalogued source tile bounds. It does not silently repair invalid geometry.
- Every exported feature is explicitly `DRAFT_NOT_APPROVED`, `ranking_eligible=false`, and `scientific_status=DRAFT_GEOMETRY_ONLY`. The geometry is not fed into the matching engine.
- A drawn boundary is not a scientifically defensible AOI until its map source, georeferencing, landform interpretation, GIS review, analysis-grid policy and team approval are documented. Source tile bounds are not geomorphic boundaries.

## Moon and Mars mapping workspaces

- **Moon global map:** NASA/JPL LRO WAC global mosaic served by the Moon Trek WMTS service.
- **Moon native raster preview:** bounded NASA PGDA LOLA Product 78 Site01 layers (elevation, slope, LDEC, total Z uncertainty and slope uncertainty). Reads are performed only after a user enables the preview. The panel shows local native grid coordinates and does not infer a latitude/longitude location from the unresolved frame caveat. The LDEC display is averaged during downsampling and is not raw shot-level data.
- **Mars global map:** NASA/JPL Mars Trek WMTS layers for MOLA colour hillshade and Viking MDIM 2.1 visual mosaic.
- Global NASA map layers are for exploration/context. The current product still has no Mars target fingerprint and does not use Mars visual layers as scored inputs.
- These live tile layers require browser internet access. Planetary map-service products remain separate from the CSV-driven AREA 67 matching output.

## Dependencies

- `streamlit-folium==0.27.4` is used for bidirectional interactive Leaflet maps and draw events.
- Folium draws maps and Leaflet layers; Rasterio/GDAL performs bounded COG/GeoTIFF reads; Plotly renders the local native-grid LOLA preview.
