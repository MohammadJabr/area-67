# AREA 67

**Planetary Analog Discovery & Mission Planning**  
**Discover Earth. Explore Other Worlds.**

AREA 67 is a NASA Space Apps Challenge project: a mission-specific decision-support platform that uses elevation data to compare terrain regions on Earth, the Moon and Mars, and identify Earth sites useful for engineering experiments.

An analog is useful for selected characteristics; it is not a perfect reproduction of another world. Similarity rankings guide investigation. They are not site certifications or probabilities of mission success.

## Approved product architecture

The project supports two search directions:

- **Space-to-Earth:** start with a lunar or Martian target and rank Earth candidates. This is the 24-hour MVP workflow.
- **Earth-to-Space:** start with an Earth location and find Moon/Mars terrain with selected similar characteristics. This remains in the product vision, not the first MVP.

The five connected capabilities from the approved presentation are:

1. **Analog Radar** — discover and rank candidate regions.
2. **Mission Matching** — weight terrain features for the engineering task.
3. **Rover Gauntlet** — hypothetical rover least-cost routes using A* (optional after the core pipeline).
4. **ShadowTwin** — terrain illumination/shadow exploration using DEM and SPICE Sun-position context (optional).
5. **Analog Passport** — evidence, provenance, comparison, suggested experiment, caveats and data lineage.

The **Single-Parameter Explorer** is an analysis utility in the comparison experience.

See [Product Architecture](docs/PRODUCT_ARCHITECTURE.md) and [Application Integration Contract](docs/INTEGRATION_CONTRACT.md).

## Core Terrain Fingerprint

All five groups are required:

- **Slope:** median and P90 at minimum; P95/histogram optional.
- **Ruggedness (TRI):** one declared formulation and neighbourhood; median and P90 at minimum.
- **Local relief:** P95–P5 within a declared physical window.
- **Terrain distribution:** valid-area percentages in documented low/mid/high classes (or the earlier flat/moderate/steep labels).
- **Spatial pattern:** for the MVP, Hiba's preferred metric is largest connected high-slope patch percentage, with threshold and 4/8-neighbour connectivity documented.

Use compatible physical scales/windows, record units and NoData, preserve nulls, and avoid double-counting correlated Slope and Terrain Distribution.

## MVP mission and data

The personal team playbooks recommend one **Rover Navigation / Terrain Traversal** mission profile for the first prototype. Its feature weights are team hypotheses that must be documented and tested; they are not NASA or rover-manufacturer standards.

Project data sources:
- Moon: NASA LOLA / LRO products.
- Mars: NASA MOLA for broad context, or local USGS CTX DTM when suitable coverage exists.
- Earth: SRTM or an appropriate documented local DEM.
- Thermal context in the project report: MODIS (Earth), Diviner (Moon), THEMIS (Mars). These are supporting context only and are not part of the MVP topographic score unless their compatibility and method are checked.

The prototype should use one space target and 3–5 Earth candidates selected for real data availability and quality.

## Scientific integrity

- Do not compare absolute elevation values across planetary bodies with different vertical references.
- Do not treat NoData as zero.
- Do not claim that resampling creates new detail.
- Keep data source, product/version, CRS, vertical reference, units, scale, coverage and processing choices with each result.
- Check feature correlations and avoid double counting.
- Report similarity, data completeness and ranking stability separately.
- Do not say a site is globally undiscovered because it is absent from one catalog.
- Label hypothetical routes as least-cost paths under stated DEM cost assumptions, not rover-safe routes.
- Label all synthetic fixtures and non-implemented capabilities as such.

## Team

- Mohammed Jabr — Team Lead & System Integration
- Ghassan Al-Shoubi — Data Acquisition & GIS
- Hiba Sbouh — Terrain Fingerprint & Scientific Validation
- Omar Salous — Weighted Similarity & Mission Planning

## Repository layout

    area-67/
    ├── app/                 # Streamlit application
    ├── data/
    │   ├── raw/             # Large source data (not committed)
    │   ├── processed/       # Team-produced outputs
    │   └── sample/          # Small synthetic fixtures, labelled as such
    ├── docs/                # Scope, architecture, contracts, sources
    ├── notebooks/           # Exploration and validation
    ├── src/
    │   ├── data/            # Loading, schemas and validation
    │   ├── features/        # Terrain fingerprint calculations
    │   ├── matching/        # Mission-based similarity and explanations
    │   ├── routes/          # Optional Rover Gauntlet/A*
    │   ├── illumination/    # Optional ShadowTwin
    │   └── reporting/       # Analog Passport
    ├── tests/
    └── .github/workflows/

## Run locally

    python -m venv .venv
    # Windows PowerShell:
    .venv\Scripts\Activate.ps1
    # Git Bash on Windows:
    source .venv/Scripts/activate
    # macOS / Linux:
    source .venv/bin/activate

    pip install -r requirements.txt
    streamlit run app/main.py

Run tests with:

    pytest -q

## Data integration

The app reads:

- data/processed/terrain_fingerprints.csv
- data/processed/candidate_rankings.csv

The fingerprint contract accepts Hiba's documented low/mid/high and largest-steep-patch fields, as well as the earlier integration-draft flat/moderate/steep and generic spatial metric names. The ranking reader accepts both the app's canonical field names and Omar's documented site_id / relative_similarity / similarity_distance aliases. target_site_id is required to preserve traceability.

Synthetic CSVs are used only when neither real file exists. The app refuses to mix one real file with one synthetic file.

## Current implementation status

The Streamlit MVP, Analog Passport, provisional LOLA Site04 GIS acquisition/QA workflow, and target-aware terrain-matching software are merged into `main`.

- The application runs in clearly labelled **DEMO MODE** while no complete real processed-data pair exists.
- The demo fixtures are synthetic interface/test data, not NASA observations or scientific results.
- The GIS contribution is a provisional lunar Site04 acquisition/QA workflow; it does not yet provide Earth analog candidates.
- The matching engine is tested with synthetic fingerprints. Real analysis still requires Hiba's validated terrain fingerprints, at least three suitable Earth candidate sites, team-approved tolerances, and an end-to-end run.
- Direct LOLA observation support, valid raster coverage, and uncertainty are distinct quality concepts; the app and methodology must not conflate them.

The current scientific result status is therefore **pending real Earth-candidate data and validated terrain fingerprints**.
