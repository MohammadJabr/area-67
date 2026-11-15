# AREA 67 — Four-minute judge demo sequence

**Build shown:** exploratory real-data MVP (Site01 → Earth reference windows).
**Important:** keep the in-app and Passport warning visible. The displayed windows are provisional reference-centred samples, not approved geomorphic AOIs.

## 0:00–0:30 — Problem and scope
“AREA 67 compares selected terrain characteristics from a Moon/Mars target with Earth environments for mission-specific analogue research. Today we demonstrate the Space-to-Earth pilot: NASA LOLA Site01 against three Earth reference windows, for Rover Navigation / Terrain Traversal.”

## 0:30–1:00 — Mission setup
Open Mission Setup. Select `MOON_SITE01_PILOT990` and `Rover Navigation / Terrain Traversal`. Explain that the Moon target is NASA PGDA Site01 / Connecting Ridge and that the analysis window is exploratory, not a signed-off provider ROI or approved study AOI.

## 1:00–2:00 — Candidate comparison
Open Results & Comparison. Walk through:
- Haughton reference window: rank 1, similarity index 73.79.
- Yungay hyper-arid reference window: rank 2, 66.13.
- Mauna Kea reference window: rank 3, 27.39.

State that these are relative ranking indices under provisional feature tolerances and mission weights, not probabilities, percentages of equivalence, or safety ratings. Show the five feature groups and use the Single-Parameter Explorer to explain slope vs TRI vs local relief.

## 2:00–2:45 — Explain evidence quality
Show Site01's positive LDEC support (9.235%) separately from 100% valid raster mask coverage. Explain that most zero-LDEC cells are interpolated, not direct shots. Mention the bounded Product 90 screen: EFFRES P50 15.78m / P90 24.08m, so nominal 5m posting is not effective 5m detail.

Mention that the Earth inputs are Copernicus GLO-30 DSM samples with product-level EGM2008 metadata; effective terrain resolution and per-pixel quality companions were not established. No absolute cross-body elevations or lunar datum transformations are used.

## 2:45–3:30 — Analog Passport
Open the Haughton Passport. Show source, checksum, 30m pilot analysis scale, requested 150m local-relief window (five cells; 120m actual centre-to-centre span), AOI not-approved state, and source-quality caveats. Download the Markdown Passport if asked.

## 3:30–4:00 — Limits and next step
“Today we demonstrate an end-to-end real-raster exploratory workflow. The next validation step is to approve geomorphic AOIs and harmonised processing, then have the science and matching workstreams independently rerun the canonical pipelines. This tool supports analogue research; it does not certify a landing site, base location, or rover-safe route.”

## Demo recovery
- If processed CSV files are absent locally, the app falls back to clearly labelled synthetic DEMO MODE.
- If a candidate is questioned, point to the per-site source/quality note and explain that a reference window is not the final landform boundary.
- Do not switch to the optional A* route branch or claim ShadowTwin/thermal/geology fusion as implemented in this MVP.
