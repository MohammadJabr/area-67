# AREA 67 — Product Architecture and 24-Hour MVP

**Team:** AREA 67  
**Project:** Planetary Analog Discovery & Mission Planning  
**Challenge:** Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars  
**Tagline:** Discover Earth. Explore Other Worlds.

## Product purpose

AREA 67 is a mission-specific decision-support platform. It uses elevation data to describe planetary and terrestrial regions, compare their local terrain characteristics, rank Earth candidates for a defined engineering task, and record the evidence and limits of each analogy.

An analog is useful for selected characteristics; it is not a perfect reproduction of another world. Similarity rankings guide investigation. They are not site certifications or probabilities of mission success.

## Search directions

- **Space-to-Earth:** start with a Moon or Mars terrain region and rank Earth candidates. This is the active 24-hour MVP workflow.
- **Earth-to-Space:** start with an Earth region and identify Moon/Mars terrain with selected similar characteristics. This remains part of the product vision, but is not required for the first MVP.

The prototype should use one space target and 3–5 Earth candidate windows, chosen for data availability and documented coverage rather than visual appeal alone.

## Core data and Terrain Fingerprint

Elevation data is the primary data source:

| Body | Primary source in the project plan | Notes |
|---|---|---|
| Moon | NASA LOLA / LRO products | Select a supported target area and inspect product coverage/quality |
| Mars | NASA MOLA; local USGS CTX DTM where suitable | MOLA for broader context; CTX DTM for local detail when coverage is available |
| Earth | SRTM or a suitable documented local DEM | Candidate sites must have source metadata and quality notes |

The Terrain Fingerprint is the core of AREA 67. Every target and candidate is described using the same five groups, with documented definitions, units, spatial scale, windows, and NoData handling.

1. **Slope** — continuous slope-angle distribution. MVP summaries: median and P90; P95/histogram optional.
2. **Ruggedness (TRI)** — local elevation variation. Use one declared formulation (the Hiba playbook specifies Riley's eight-neighbour formulation) and document the neighbourhood. MVP summaries: median and P90.
3. **Local relief** — local/relative elevation variation, not absolute planetary elevation. MVP statistic: P95–P5 within a declared window of fixed physical size; median/other summaries optional.
4. **Terrain distribution** — valid-area percentages in declared slope/terrain classes. Hiba's output labels are low/mid/high; the earlier integration draft also used flat/moderate/steep. Thresholds are analytic choices for this experiment, not universal safety boundaries. Class percentages should sum to about 100%.
5. **Spatial pattern** — where difficult terrain occurs. Hiba's preferred MVP statistic is the percentage of the valid area occupied by the largest connected high-slope patch; document threshold and 4- or 8-neighbour connectivity. A generic documented spatial statistic is accepted as an alternative.

The five groups are related, not statistically independent. Terrain Distribution is derived from Slope, so the matcher must test for double counting. TRI and Slope may also be correlated. Do not assign equal or large independent weights automatically.

## Five connected product capabilities

These are the five capabilities shown in the approved 11-slide presentation:

| Capability | Purpose | MVP scope |
|---|---|---|
| **Analog Radar** | Discover and rank candidate regions | Core Space-to-Earth ranking flow |
| **Mission Matching** | Change feature importance according to the engineering task | One agreed profile: Rover Navigation / Terrain Traversal |
| **Rover Gauntlet** | Compare hypothetical rover routes using terrain-cost assumptions and A* | Optional extension; only after matching works, using a small DEM |
| **ShadowTwin** | Explore terrain illumination/shadow conditions | Optional extension requiring terrain inputs and SPICE Sun-position context |
| **Analog Passport** | Package data sources, terrain evidence, comparison, provenance, suggested experiments and limitations | Core deliverable for at least one real candidate |

The **Single-Parameter Explorer** is an analysis feature within the comparison experience: it lets a user inspect one metric (for example, slope, TRI, temperature context or shadow duration) without pretending that an unimplemented parameter has been calculated.

The project report also lists thermal context sources: MODIS (Earth), Diviner (Moon), and THEMIS (Mars). These can complement the topographic fingerprint when their products, scales, units, timing, and quality are compatible. They do not replace the five terrain groups and must not be blended into the MVP similarity score unless the data and method are independently checked.

## Matching and explainability

Omar's matching workstream computes the rankings; the app reads and explains those outputs.

- Normalize feature-group distances before combining them. Do not compare raw degrees, elevation units, and percentages directly.
- Use a documented scaling/tolerance method. A robust scaler fitted on only three candidates is not automatically a scientific standard.
- Compute group-level distances and combine them using the selected mission weights.
- Normalize weights to sum to one (or document equivalent normalization).
- Check the correlation/double-counting between Slope and Terrain Distribution.
- Show each available group's contribution to the overall distance/relative score.
- Missing metric groups must not be replaced with zero. Exclude the affected group or use a documented missing-data policy and show reduced completeness.
- Report similarity, data completeness, and ranking stability as three distinct outputs.
- A ranking-stability frequency in Top-3/Top-5 under actual sensitivity runs is a robustness summary, not a probability of analogy or mission success.

The MVP profile is **Rover Navigation / Terrain Traversal**. Its initial weights are team hypotheses to be documented and tested, not NASA standards or rover manufacturer limits.

## Data and processing safeguards

- Record provider, exact product ID/version, source URL, access/acquisition date when available, CRS, vertical reference, horizontal pixel size, elevation units, NoData value, valid coverage, quality/uncertainty layers, processing steps, and usage terms.
- Preserve original rasters; work on documented clipped/processed copies.
- Use appropriate projected/metre grids for distance-based neighbourhood calculations. Do not treat longitude/latitude degrees as metres.
- Use comparable physical analysis scales and window sizes where the products support them. Resampling does not create new information.
- Do not compare absolute elevations across Earth, Moon, and Mars as if their vertical datums were equivalent. Compare local/relative terrain descriptors.
- NoData is not elevation zero. Keep masks and calculate statistics over valid area only.
- Large DEMs and downloaded archives remain outside Git unless the team explicitly agrees otherwise.

## Validation plan

Minimum scientific checks:

1. **Synthetic flat surface:** slope and TRI approximately zero; local relief approximately zero, within numerical tolerance.
2. **Synthetic tilted plane:** slope calculation recovers the known angle within stated tolerance.
3. **Synthetic bump/pit:** TRI and local relief respond as expected around the feature.
4. **Terrain distribution:** valid-area class percentages sum to approximately 100%.
5. **Spatial-pattern check:** a single connected high-slope patch is distinguished from dispersed patches.
6. **Reference comparison:** compare slope or DEM-derived metrics with a compatible official/independent product when available; document method/resolution differences.
7. **Scale/window sensitivity:** repeat at two supported scales/windows if inputs permit.
8. **Weight sensitivity:** vary plausible mission weights and report how often each site appears in Top-3/Top-5.
9. **Baseline:** compare the multi-feature ranking with a Slope-only ranking and explain the added value of the other groups.

Code correctness, source-data accuracy, and ranking reliability are separate questions. Do not claim a universal accuracy percentage without a defined reference and measured error.

## Team responsibilities

- **Mohammed Jabr:** team lead, repository coordination, application integration, shared data contracts, Passport, end-to-end testing and demo.
- **Ghassan Al-Shoubi:** source acquisition, GIS, DEM preparation, footprints, metadata manifest, quality/coverage notes.
- **Hiba Sbouh:** the five Terrain Fingerprint groups, method definitions, maps/statistics, synthetic tests and scale/NoData validation.
- **Omar Salous:** weighted group distances, one mission profile, ranking, per-group explanations, baseline and sensitivity; A* only after the core pipeline works.

Each workstream must deliver usable files/code and a short README, not screenshots alone.

## 24-hour minimum viable product

- One documented lunar or Martian target.
- Three to five documented Earth candidates (or transparently explain how many are available).
- One mission profile: Rover Navigation / Terrain Traversal.
- All five feature groups, at least one documented operational metric per group.
- One explainable candidate ranking using real outputs.
- Three Streamlit screens: Mission Setup, Results & Comparison, Site Passport.
- One real-data Analog Passport with sources, coverage/quality, values, match explanation, gaps and limitations.
- At least one scientific validation and one sensitivity check.
- Reproducible setup/run instructions and an end-to-end demo.

Synthetic data is permitted only to develop and smoke-test the interface. It must always be labelled synthetic and must never be shown as NASA-derived evidence.

## 24-hour checkpoints

| Time | Checkpoint |
|---|---|
| H0–1 | Freeze target, mission, AOIs/candidates and data choices |
| H1–3 | Repository, branches, dependencies, data contract, runnable app shell |
| H3–6 | Source rasters inspected; UI shell uses labelled fixtures |
| H6–10 | Analysis-ready DEMs and initial source manifest; contract fixed |
| H10–14 | Five-group fingerprints for target/candidates |
| H14–17 | Real ranking, contribution explanation, baseline/sensitivity |
| H17–19 | Optional route/quality outputs only if core is stable |
| H19–21 | Real Analog Passport |
| H21–22 | Clean-environment end-to-end test |
| H22–24 | Feature freeze, runbook, demo scenario and evidence summary |
