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

## Full challenge vision and lunar target library

AREA 67 is intended to grow beyond a single lunar target and one rover-navigation profile. The current NASA LOLA acquisition workflow supports a provisional Site04 baseline; the official PGDA catalogue also publishes additional south-pole sites and ROI archives for Site01, Site04, Site06, Site07, and Site11. See the [Lunar Target Catalogue](docs/LUNAR_TARGET_CATALOG.md) and [LOLA ROI / multi-site workflow](docs/LOLA_ROI_AND_MULTI_SITE_WORKFLOW.md). These are provider-defined target options, not an approved ranking of permanent-base locations.

The broader challenge roadmap covers global Earth discovery and separate evidence layers for terrain, geology/materials, thermal conditions, illumination, water/ice/resources, dust/processes, biological context, and subsurface environments. These dimensions must not be collapsed into one score before their datasets and methods are compatible.

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

## Matching workflow

When the agreed `data/processed/terrain_fingerprints.csv` is available and the team has approved explicit feature tolerances, run the Space-to-Earth matching pipeline from the repository root:

```powershell
python -m src.matching.cli --fingerprints data/processed/terrain_fingerprints.csv --target-site-id MOON_SITE04 --tolerances-json config/matching_tolerances.json --min-feature-group-completeness <TEAM_APPROVED_FRACTION> --min-data-completeness <TEAM_APPROVED_FRACTION>
```

Replace both completeness placeholders with team-approved fractions between 0 and 1; the CLI refuses to run if they are omitted. A value of `0.0` explicitly disables that gate and must not be used for a real study without team approval. The command writes the canonical `data/processed/candidate_rankings.csv` and a `data/processed/ranking_robustness.json` sidecar. Start from `config/matching_tolerances.template.json`, but replace its null values only with study-specific tolerances agreed by the team. See [the matching runbook](docs/MATCHING_RUNBOOK.md) for input requirements, configuration, outputs and limitations.

## Current implementation status

The following software and data-management components are merged into `main`:

- Streamlit MVP, Analog Passport, application contracts, and paired synthetic demo fixtures.
- NASA LOLA Site04 acquisition and structural QA workflow; Site04 remains a **provisional lunar target**.
- Earth DEM acquisition, raster inventory, structural QA, and screening reports for five provisional Copernicus GLO-30 DSM source tiles: Haughton, McMurdo, Askja, Mauna Kea, and Yungay.
- A separate USGS 3DEP 1 m bare-earth DEM alternative for Mauna Kea, with its different vertical reference documented.
- Target-aware terrain-matching engine plus a CSV loader/CLI, canonical ranking export, Slope-only baseline, and weight-sensitivity report.
- Five-group terrain-fingerprint extraction and validation pipeline, including synthetic/GeoTIFF tests, explicit method/provenance metadata, and optional derived feature maps.

### Current data status

- The five Copernicus products are full source tiles, not selected candidate AOIs. The named points and landforms remain provisional.
- The Mauna Kea USGS tile is a regional alternative only; it is not a harmonized replacement for all five Copernicus sources.
- Source manifests, checksums, QA JSON/Markdown, and screening previews are tracked. Large raw DEM rasters remain gitignored and must be acquired locally using the documented tools.
- No AOI boundaries, final Earth candidate set, common physical analysis scale, reprojection/resampling policy, or target sub-area have been approved.
- Hiba's five-group terrain extraction pipeline, scientific validation utilities, methodology, and synthetic/GeoTIFF tests are now merged into `main`. The real `data/processed/terrain_fingerprints.csv` is still pending approved AOIs, a shared physical scale, and analysis-ready rasters; no real terrain measurements are claimed. The canonical `candidate_rankings.csv` and robustness report are also absent.

### Running the matching workflow

The matching CLI refuses to run unless the operator explicitly supplies both `--min-feature-group-completeness` and `--min-data-completeness`. Their values, along with the five feature tolerances, must be approved for the chosen study. The software does not select scientific cutoffs for the team. A value of `0.0` explicitly disables a gate and must not be treated as a recommendation.

### Application and optional route status

- The application remains in clearly labelled **DEMO MODE** until both real processed files exist and pass the integration contracts. It refuses to mix a single real file with synthetic fixtures.
- The five-group terrain-fingerprint extraction pipeline is merged into `main` and includes 16 focused synthetic/GeoTIFF tests. These verify the implementation against constructed surfaces, not actual lunar or Earth reference terrain.
- The matching workflow is software plumbing tested with synthetic fixtures; no real Earth–Moon/Mars ranking is claimed.
- The optional A* Rover Gauntlet work remains in [Draft PR #9](https://github.com/MohammadJabr/area-67/pull/9), not in `main`. Its updated branch rejects sheared affine grids, enforces a 250,000-cell default software resource guard, and writes a route provenance JSON sidecar. Its latest CI passed 76 synthetic tests; no real route is claimed.
- The merged terrain pipeline's latest full CI run passed **101 tests** (41 warnings) on the PR head; the post-merge `main` run is recorded in the Actions history.

The project has a working application and reproducible source/matching software, but **it does not yet have a validated planetary-analog result**. The next priority is to approve study areas and physical scales, produce validated real fingerprints, and run the complete evidence chain—not to add more optional features.
