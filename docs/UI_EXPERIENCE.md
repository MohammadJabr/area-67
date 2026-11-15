# AREA 67 — Interactive Mission Console

## Experience structure

The Streamlit application is organized as a mission-oriented workspace:

1. **Mission Control** — selected target/body/profile, current capability map, and the current mission workflow.
2. **Analog Radar** — matcher-supplied Earth candidate ranking, candidate-card/table switch, relative-index chart, five-group evidence, single-parameter explorer, Earth-only candidate map, ranking explanations, and data-quality/provenance table.
3. **Analog Passport** — selectable target/candidate, feature evidence, target-to-candidate comparison, source lineage, quality caveats, matching assumptions, and Markdown export.

Target and mission-profile controls live in the sidebar. Options are populated only from the loaded ranking CSV. The interface does not add synthetic target choices or recompute the matching model.

## Visual system

- Deep-space background with layered gradients, glass-like panels and restrained cyan/lime highlights.
- Consistent spacing, rounded cards, clear typographic hierarchy, and responsive layouts for narrow screens.
- Ranking cards foreground rank, matcher-supplied relative index, weighted distance and supplied ranking notes.
- Plotly charts use a dark transparent canvas and retain pan/zoom/hover controls.
- The theme is stored locally in `app/theme.css`; no external font, image or runtime network dependency is required.

## Scientific integrity in the UI

- Real-data rows remain labelled **EXPLORATORY REAL-DATA PILOT** until AOIs, frames, grid/scale policies and study settings are approved.
- Synthetic fallback is labelled **SYNTHETIC DEMO · NOT MEASURED**.
- The existing warning states the Haughton/Yungay/Mauna Kea historical set differs from the frozen Haughton/Askja/Mauna Kea shortlist.
- Map points remain reference-window anchors, not AOI polygons.
- Similarity index is not shown as a probability, certification or rover-safety measure.
- Missing features and unknown provenance remain missing; the interface does not fill gaps.

## Implementation notes

- This is a Streamlit theme and layout enhancement. It does not change the data contracts, source rasters, fingerprint formulas, matching weights, tolerances, candidate IDs or tracked ranking values.
- Candidate-card values are rendered directly from the matcher output.
- The detailed table remains available as an alternate view.
- The five terrain groups, single-parameter explorer, Earth map, Passport comparison and Markdown export remain part of the application.
- Local entry point: `python -m streamlit run app/main.py`.
