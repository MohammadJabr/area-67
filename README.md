# AREA 67

**Planetary Analog Discovery & Mission Planning**  
**Discover Earth. Explore Other Worlds.**

AREA 67 is a NASA Space Apps Challenge project: a mission-specific decision-support platform that uses elevation data to compare terrain regions on Earth, the Moon and Mars, and identify Earth sites useful for engineering experiments.

An analog is useful for selected characteristics; it is not a perfect reproduction of another world. Similarity rankings guide investigation. They are not site certifications or probabilities of mission success.

## Full challenge ambition

AREA 67 is designed as a multi-dimensional planetary-analog discovery platform, not a rover-only terrain matcher. The long-term scope covers global Earth discovery and evidence dimensions including terrain, geology/materials, thermal extremes, illumination/shadow, water/ice/resources, dust and surface processes, biology/habitability context, caves/subsurface, and mission-specific operations. These dimensions remain separate evidence layers until compatible datasets and validated methods justify comparison. The current implemented MVP is narrower: a single-target lunar pilot (Site01 / Connecting Ridge), one Rover Navigation / Terrain Traversal profile, five terrain groups, and an exploratory ranking of three Earth sample windows. Site04 is retained as a LOLA QA/comparator site, not a second ranked target. See [the full challenge roadmap](docs/FULL_CHALLENGE_ROADMAP.md) for current implementation status, workstreams, evidence requirements, and release gates.

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

AREA 67 is intended to grow beyond a single lunar target and one rover-navigation profile. The working lunar MVP target is NASA PGDA Site01 (Connecting Ridge), the primary illumination/A306 SDEM evidence anchor. Site04 (Shackleton rim) is retained as a LOLA QA/comparator site, not a second ranked target. Neither provider ROI set is an approved AREA 67 study AOI, and no permanent-base ranking is claimed. The frozen sprint's intended Earth shortlist is Haughton Crater, Askja and Mauna Kea. The current exploratory app ranking instead uses Haughton, Yungay and Mauna Kea because the sampled Askja reference-centred window was held out as near-flat/equal-elevation. Yungay's substitution for Askja is provisional and requires team approval; none of these sample windows is an approved geomorphic AOI. McMurdo/Taylor Valley remain on hold pending named-landform/reference-coordinate clarification. See the [Science Execution Decision](docs/SCIENCE_EXECUTION_DECISION_2026-11-15.md), [Lunar Target Catalogue](docs/LUNAR_TARGET_CATALOG.md), [LOLA ROI / multi-site workflow](docs/LOLA_ROI_AND_MULTI_SITE_WORKFLOW.md), and [ROI-level LOLA support audit](docs/LOLA_ROI_QUALITY_AUDIT.md). The official PGDA catalogue also publishes additional south-pole sites and ROI archives for Site01, Site04, Site06, Site07, and Site11.

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

The current science pilot uses a Site01/Site04 lunar comparison pair and three primary Earth candidates selected for source readiness and AOI feasibility; the app remains configurable for other target/candidate sets.

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
python -m src.matching.cli --fingerprints data/processed/terrain_fingerprints.csv --target-site-id SITE_ID_FROM_APPROVED_FINGERPRINT_CSV --tolerances-json config/matching_tolerances.json --min-feature-group-completeness <TEAM_APPROVED_FRACTION> --min-data-completeness <TEAM_APPROVED_FRACTION>
```

Replace `SITE_ID_FROM_APPROVED_FINGERPRINT_CSV` with the exact target `site_id` present in the validated fingerprint CSV. Replace both completeness placeholders with team-approved fractions between 0 and 1; the CLI refuses to run if they are omitted. A value of `0.0` explicitly disables that gate and must not be used for a real study without team approval. The command writes the canonical `data/processed/candidate_rankings.csv` and a `data/processed/ranking_robustness.json` sidecar. Start from `config/matching_tolerances.template.json`, but replace its null values only with study-specific tolerances agreed by the team. See [the matching runbook](docs/MATCHING_RUNBOOK.md) for input requirements, configuration, outputs and limitations.

## Current implementation status

The following software and data-management components are merged into `main`:

- Streamlit MVP, Analog Passport, application contracts, and paired synthetic demo fixtures.
- NASA LOLA Site01 and Site04 acquisition and structural QA workflows. Site01 is the primary illumination/A306 evidence anchor and Site04 is the LOLA comparison target; both provider ROI sets remain provisional and are not approved AREA 67 study AOIs. See the [Science Execution Decision](docs/SCIENCE_EXECUTION_DECISION_2026-11-15.md), [GIS pilot execution decision](docs/reports/gis_pilot_execution_decision_2026-11-15.md), and [multi-site ROI candidate screening report](docs/reports/lunar_roi/MULTI_SITE_ROI_CANDIDATE_SCREENING_2026-11-15.md).
- Earth DEM acquisition, raster inventory, structural QA, candidate screening, and local-raster audit tooling for five provisional Copernicus GLO-30 DSM source tiles. The current pilot shortlist is Haughton, Askja and Mauna Kea; McMurdo and Yungay remain on hold pending AOI/reference-coordinate clarification.
- Two adjacent Mauna Kea USGS 3DEP 1 m bare-earth tiles are recorded. The western tile has EPSG:26904 / NAVD88 / metres in its source record; the eastern tile is EPSG:26905, but its vertical reference and elevation units remain unverified. They must not be mosaicked or treated as a harmonized replacement for the Copernicus DSM.
- Read-only remote COG inspection using HTTP byte-range preflight and bounded 500 × 500 pixel windows for ArcticDEM Haughton, REMA McMurdo, and ÍslandsDEM Askja catalog assets; no full high-resolution raster assets were downloaded.
- Structural raster preflight checks and provisional Earth reference-point GeoJSON. The points are source/landmark checks, not approved candidate AOI polygons.
- Site01 (Connecting Ridge) has now received local five-layer raster QA, seven-feature ROI support/uncertainty review, invalid-geometry sensitivity preview, and 607-vertex pixel-registration audit. Its provider ROIs remain provisional; see the [Site01 evidence review](docs/reports/lunar_roi/SITE01_COORDINATE_AND_SDEM_REVIEW.md).
- Target-aware terrain-matching engine plus a CSV loader/CLI, canonical ranking export, Slope-only baseline, and weight-sensitivity report.
- Five-group terrain-fingerprint extraction and validation pipeline, including synthetic/GeoTIFF tests, explicit method/provenance metadata, and optional derived feature maps.

### Current data status

- The five Copernicus products are full source tiles, not selected candidate AOIs. The named points and landforms remain provisional.
- Mauna Kea's USGS 3DEP 1 m data now includes two adjacent tiles in different UTM zones (EPSG:26904 and EPSG:26905). The east tile's vertical reference and elevation units are unverified; do not mosaic or compare it until cross-zone and vertical handling are approved.
- Targeted remote COG probes show accessible ArcticDEM v4.1 Haughton and REMA v2 McMurdo DSM assets with MAD/count/date companions, plus an ÍslandsDEM Askja asset. These are limited 500 × 500 window reads and metadata checks, not full-tile validation or local downloads.
- data/metadata/earth_candidate_reference_points.geojson records 13 provisional/alternative reference points. The Haughton, McMurdo and Yungay markers have documented discrepancies or unresolved location identity; none is an approved AOI.
- Source manifests, checksums, QA JSON/Markdown, remote-access summaries and screening previews are tracked. Large raw DEM rasters remain gitignored and must be acquired locally using the documented tools.
- The frozen study shortlist is Haughton, Askja, and Mauna Kea; the tracked exploratory ranking is still Haughton, Yungay, and Mauna Kea reference-centred windows. Yungay is held out from the canonical study, and the current Askja sample window was held because it is near-flat/equal-elevation; that does not assess all Askja terrain. Do not present Yungay as an approved substitute for Askja. No AOI boundaries, common physical analysis scale, reprojection/resampling policy, or target sub-area have been approved.
- The canonical Site01 exploratory builder, app-facing `data/processed/terrain_fingerprints.csv` and `candidate_rankings.csv`, and `ranking_robustness.json` are present in `main`. These contain real-raster-derived exploratory measurements, not approved study results. The raw Site01 inputs are not committed.

### Running the matching workflow

The matching CLI refuses to run unless the operator explicitly supplies `--candidate-site-ids` (an allowlist; unlisted Earth rows are excluded), `--min-feature-group-completeness`, and `--min-data-completeness`. Their values, along with the five feature tolerances, must be approved for the chosen study. The software does not select scientific cutoffs for the team. A value of `0.0` explicitly disables a gate and must not be treated as a recommendation.

### Application and optional route status

- The application loads the tracked Site01 exploratory result pair and labels it **EXPLORATORY REAL-DATA PILOT**. If the complete real pair is unavailable, it uses a clearly labelled synthetic demo pair; it refuses to mix one real file with one synthetic file.
- The five-group terrain-fingerprint extraction pipeline is merged into `main` and includes 16 focused synthetic/GeoTIFF tests. These verify the implementation against constructed surfaces, not actual lunar or Earth reference terrain.
- The matching workflow has produced an exploratory real-raster Site01-to-Earth ranking through the canonical matching functions, with 11 weight-sensitivity and 11 tolerance-sensitivity scenarios. These scenarios are descriptive checks on the same provisional fingerprints, not scientific validation or probability. The ranked rows still use Yungay instead of the frozen Askja shortlist.
- A* Rover Gauntlet is outside the frozen MVP. [Draft PR #9](https://github.com/MohammadJabr/area-67/pull/9) was closed without merge; its branch is retained for future work because no approved real AOI, compatible route rasters, or team-approved cost settings exist. No real route or rover-safety claim is made.
- Latest post-merge `main` CI after PR #107: [workflow run #43708208185](https://github.com/MohammadJabr/area-67/actions/runs/43708208185) passed **231 tests** in 5.93s (518 warnings, primarily geospatial-library deprecations); dependency installation, source/test compilation and the geospatial artifact ignore-policy check passed.

The repository has a working, reproducible **exploratory presentation MVP**, but **it does not yet have a validated planetary-analog result**. See [the MVP method and results](docs/FINAL_MVP_METHOD_AND_RESULTS_2026-11-15.md) and [judge demo script](docs/JUDGE_DEMO_SCRIPT_2026-11-15.md). The next priority is approval of study areas and common physical settings, followed by independent fingerprint validation and matching review.
