# AREA 67 — Interactive Mission Console

## Experience structure

The Streamlit application is organized as four mission-oriented workspaces:

1. **Mission Control** — selected planetary target and mission profile, project status, active capability overview, and a clear explanation of the current Space-to-Earth workflow.
2. **Analog Radar** — matcher-supplied Earth candidate ranking, candidate-card/table switch, relative-index chart, candidate filtering and spotlight, and the interactive Earth reference map.
3. **Terrain Lab** — side-by-side five-group terrain fingerprint tables, single-parameter exploration, supplied matcher contributions/differences, and data-quality/provenance comparison.
4. **Analog Passport** — selectable target/candidate dossier, readable terrain evidence tables, target-to-candidate comparison, source lineage, quality caveats, matching assumptions, and Markdown export.

Target and mission-profile controls live in the sidebar. Options are populated only from the loaded ranking CSV. Candidate filters operate on the supplied matcher rows; they do not recalculate scores or alter the source ranking. The candidate count shows both filtered and total available candidates so an intentional filter is not mistaken for missing data.

## Interactive geographic map

- The Analog Radar displays Earth reference-window anchors on a PyDeck map with a dark CARTO basemap.
- Markers are colored by their matcher-supplied rank and expose site name, rank, relative match index, weighted distance, and coordinates on hover.
- Users can pan and zoom the map, and the visible markers follow the candidate filter.
- The map is deliberately Earth-only. Lunar/Martian coordinate values are never plotted on an Earth basemap.
- Markers identify reference-window anchors only. They are not approved study-area boundaries or AOI polygons.
- Public CARTO basemap tiles are loaded at runtime; internet access is required for the background map.

The current dataset does not contain approved polygon boundaries or publicly served raster layers for the study areas. Therefore the application does not claim to display a terrain raster overlay, hillshade, slope heatmap, or 3D terrain surface. Those layers require approved AOI geometries and validated raster derivatives with suitable hosting.

## Visual system

- Deep-space background with layered gradients, glass-like panels and restrained cyan/lime highlights.
- Consistent spacing, rounded cards, clear typographic hierarchy, and responsive layouts for narrow screens.
- Ranking cards foreground rank, matcher-supplied relative index, weighted distance and supplied ranking notes.
- Ranking charts use candidate names, explicit rank colors, and visible numeric labels.
- The Passport uses readable field/value tables rather than exposing raw JSON as the main presentation.
- The theme is stored locally in `app/theme.css`. The map's basemap is the exception and uses public CARTO tiles.

## Scientific integrity in the UI

- Real-data rows remain labelled **EXPLORATORY REAL-DATA PILOT** until AOIs, frames, grid/scale policies and study settings are approved.
- Synthetic fallback is labelled **SYNTHETIC DEMO · NOT MEASURED**.
- The existing warning states the Haughton/Yungay/Mauna Kea historical set differs from the frozen Haughton/Askja/Mauna Kea shortlist.
- Map points remain reference-window anchors, not AOI polygons.
- Similarity index is not shown as a probability, certification or rover-safety measure.
- Missing features and unknown provenance remain missing; the interface does not fill gaps.
- Data-quality coverage and direct instrument observation support remain distinct quantities.

## Implementation notes

- This is a Streamlit layout and interaction enhancement. It does not change the data contracts, source rasters, fingerprint formulas, matching weights, tolerances, candidate IDs or tracked ranking values.
- Candidate-card values and map attributes are rendered from supplied matcher/fingerprint outputs.
- The detailed data table remains available as an alternate ranking view.
- Local entry point: `python -m streamlit run app/main.py`.
