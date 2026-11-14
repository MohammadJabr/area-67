# AREA 67

**Planetary Analog Discovery & Mission Planning**  
**Discover Earth. Explore Other Worlds.**

AREA 67 is a NASA Space Apps Challenge project exploring how open Earth, Moon, and Mars observations can identify and characterize terrestrial environments that are useful analogs for specific planetary exploration tasks.

An analog is useful for selected characteristics or processes; it is not a perfect replica. Results should explain both where an analogy is useful and where it breaks down.

## Agreed architecture

- **Search directions:** Space-to-Earth (active MVP) and Earth-to-Space (future direction).
- **Core Terrain Fingerprint:** Slope distribution, Terrain Ruggedness Index (TRI), Local Relief, Terrain Distribution, and Spatial Pattern.
- **Context layers:** thermal, geological/mineralogical, environmental (water/ice/dust/wind), and subsurface evidence. Keep them separate until source compatibility and measurement methods are validated.
- **Mission modules:** Weighted Similarity & Mission-Based Matching, Single-Parameter Explorer, ShadowTwin (illumination), Rover Gauntlet (rover mobility/A*), Analog Gap Analysis, and Analog Passport.

See docs/PRODUCT_ARCHITECTURE.md and docs/INTEGRATION_CONTRACT.md.

## Initial 24-hour prototype scope

1. Select one lunar or Martian target, one mission profile, and 3–5 Earth candidates.
2. Acquire documented, compatible elevation datasets and record source/quality metadata.
3. Derive at least one documented metric for each of the five Terrain Fingerprint groups.
4. Rank candidates using explainable mission-weighted similarity.
5. Display target, candidates, feature evidence, ranking explanations, and data-quality notes in Streamlit.
6. Generate one initial Analog Passport from actual data rows.
7. Validate the workflow and freeze a reproducible demo.

Thermal/geological layers, Earth-to-Space search, ShadowTwin simulation, and A* route analysis are extensions. Mark each as Concept / Planned until its inputs and calculations have been tested.

## Scientific safeguards

- Do not interpret similarity as a probability of mission success or site certification.
- Do not claim global novelty because a candidate is absent from one catalog.
- Spatial resolution is not measurement accuracy; resampling does not create new information.
- Keep source provenance, units, scale, quality flags, assumptions, and limitations with every result.
- Do not compare absolute elevations across bodies with incompatible vertical references.
- Missing values are not silently replaced with zero.

## Team

- Mohammed Jabr — Team Lead & System Integration
- Ghassan Al-Shoubi — Data Collection & GIS
- Hiba Sbouh — Terrain Analysis & Validation
- Omar Salous — Similarity Matching & Mission Planning

## Repository structure

    area-67/
    ├── app/                 # Streamlit application
    ├── data/
    │   ├── raw/             # Large source data (not committed)
    │   ├── processed/       # Team-produced outputs (not committed if large)
    │   └── sample/          # Small, labelled development fixtures
    ├── docs/                # Scope, architecture, contracts, sources
    ├── notebooks/           # Exploration and validation notebooks
    ├── src/
    │   ├── data/            # Loading and contracts
    │   ├── features/        # Terrain fingerprint calculations
    │   ├── matching/        # Similarity and mission profiles
    │   ├── routes/          # Optional route analysis
    │   ├── illumination/    # Optional shadow analysis
    │   └── reporting/       # Analog Passport generation
    ├── tests/               # Unit and integration tests
    ├── .github/workflows/   # Automated checks
    ├── .gitignore
    └── requirements.txt

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

Run tests with pytest -q.

## Data integration

The application expects:

- data/processed/terrain_fingerprints.csv
- data/processed/candidate_rankings.csv

When both real files are absent, the app may use the clearly labelled synthetic fixtures in data/sample/ for interface development. The app refuses to mix one real file with one synthetic file. Synthetic values must never be described as NASA observations or scientific findings.

## Current status

The Streamlit integration and initial Analog Passport are on feature/mohammad-app-integration, proposed for review in draft PR #5. Scientific rankings remain pending on real outputs from the GIS, terrain-analysis, and matching workstreams.
