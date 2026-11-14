# AREA 67

**Planetary Analog Discovery & Mission Planning**

Area 67 is a NASA Space Apps Challenge project exploring how open Earth, Moon, and Mars observations can be used to identify and characterize terrestrial environments that are useful analogs for specific planetary exploration tasks.

Our approach is evidence-based and multi-dimensional. We begin with a terrain fingerprint built from five groups of topographic characteristics:

- Slope distribution
- Terrain Ruggedness Index (TRI)
- Local relief
- Terrain distribution
- Spatial pattern

We compare candidate locations for a stated mission objective rather than claiming that one Earth location perfectly reproduces the Moon or Mars. Results should explain both where an analogy is useful and where it breaks down.

## Initial prototype scope

The first working prototype will focus on a limited, reproducible case study:
1. Select one lunar or Martian target area and one mission profile.
2. Obtain compatible, documented elevation datasets for the target and a small set of Earth candidate areas.
3. Check coordinate systems, units, spatial resolution, coverage, NoData values, and available quality/uncertainty layers.
4. Derive the five terrain fingerprint feature groups.
5. Rank Earth candidates using an explainable, mission-weighted similarity method.
6. Validate calculations and test sensitivity to resolution and feature weights.
7. Present evidence, limitations, and provenance in an initial Analog Passport.

Route analysis (A*), illumination/shadow analysis, thermal and geological layers are extensions. They must only be presented as implemented after their data and calculations have been tested.

## Scientific principles

- An analog is useful for selected characteristics or processes; it is not a perfect replica.
- Do not interpret a similarity score as a probability of mission success.
- Do not claim a site is globally undiscovered merely because it is absent from one catalog.
- Spatial resolution is not the same as measurement accuracy. Resampling does not create new information.
- Keep source provenance, units, scale, quality flags, and assumptions with every result.
- Clearly distinguish measured values, derived metrics, assumptions, and future work.

## Team

- Mohammed Jabr — Team Lead & System Integration
- Ghassan Al-Shoubi — Data Collection & GIS
- Hiba Sbouh — Terrain Analysis & Validation
- Omar Salous — Similarity Matching & Mission Planning

## Suggested repository structure

```
area-67/
├── app/                 # Interactive application
├── data/
│   ├── raw/             # Downloaded source data (not committed if large)
│   ├── processed/       # Derived data (not committed if large)
│   └── sample/          # Small reproducible examples only
├── docs/                # Scope, methodology, sources, decisions
├── notebooks/           # Exploration and validation notebooks
├── src/
│   ├── data/            # Loading and preprocessing
│   ├── features/         # Terrain fingerprint calculations
│   ├── matching/         # Similarity and mission profiles
│   ├── routes/           # Optional route analysis
│   ├── illumination/     # Optional shadow analysis
│   └── reporting/        # Analog Passport generation
├── tests/               # Unit and integration tests
├── .gitignore
├── README.md
└── requirements.txt
```

## Data sources to investigate

- NASA LOLA / LRO products for lunar topography.
- NASA PDS MOLA products and suitable local CTX-derived terrain models for Mars.
- USGS and other documented DEM sources for Earth candidates.
- NASA/USGS analog-site catalogs as references for known sites, not as exhaustive proof of novelty.

Record the exact product identifier, version, access date, spatial resolution, coordinate reference system, vertical reference, units, coverage, quality flags, and license/usage terms for every dataset.

## Development workflow

Use feature branches and pull requests. Keep `main` runnable. Do not commit large rasters, credentials, API keys, or unlicensed data. Commit small synthetic/sample data and scripts or instructions that reproduce processing.

## Current status

The repository now includes:
- A provisional NASA LOLA Site04 acquisition, inspection, and raster-QA workflow. Site04 is not an officially finalized team target.
- A tested, explainable Space-to-Earth matching implementation with five feature-group distances, mission-weighted ranking, missing-data handling, a Slope-only baseline, weight sensitivity, and canonical ranking export.
- A CSV loader and command-line workflow that connect Hiba's terrain-fingerprint table to Omar's ranking and robustness outputs.

The matching code has been tested with synthetic fixtures. **No real Earth–Moon/Mars candidate ranking or validated analog conclusion is claimed yet.** Real Earth candidate DEMs/fingerprints, team-approved feature tolerances, method/scale confirmation, and an end-to-end run with the actual upstream files are still required. See [the matching runbook](docs/MATCHING_RUNBOOK.md), [the matching method](docs/MATCHING_METHOD.md), and [the GIS handoff](docs/GIS_HANDOFF.md).
