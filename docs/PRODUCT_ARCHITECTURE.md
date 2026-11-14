# AREA 67 — Agreed Product Architecture

**Team:** AREA 67  
**Project:** Planetary Analog Discovery & Mission Planning  
**Tagline:** Discover Earth. Explore Other Worlds.

## Mission

AREA 67 helps engineers and researchers discover and characterize Earth environments that are useful analogs for selected lunar or Martian locations and exploration tasks. An analog is useful for specific characteristics or processes; it is not a perfect reproduction of another planetary environment.

## Search directions

- **Space-to-Earth:** start with a lunar or Martian target and rank Earth candidate environments. This is the active 24-hour MVP direction.
- **Earth-to-Space:** start with an Earth location and search for similar lunar or Martian environments. Retained in the architecture; not required for the first prototype.

## Core Terrain Fingerprint

All five groups remain central:

1. **Slope distribution** — at minimum median slope and a high-percentile slope statistic.
2. **Terrain Ruggedness Index (TRI)** — document the exact formulation and neighborhood/window.
3. **Local relief** — document the statistic, physical window, and vertical units.
4. **Terrain distribution** — fractions of valid area in documented terrain/slope classes.
5. **Spatial pattern** — one interpretable, documented spatial statistic.

Use the same definitions and comparable physical analysis scales across the target and candidates. Cross-body absolute elevations must not be directly compared when vertical references differ. Missing values are not zero.

## Multi-dimensional evidence layers

The wider architecture keeps these layers separate:

- **Core Terrain Fingerprint:** the primary MVP input to matching.
- **Thermal layer:** temperature and environmental extremes; potential sources include Diviner, THEMIS, and MODIS.
- **Geological layer:** rocks, minerals, and surface materials.
- **Environmental layer:** water, ice, dust, wind, and related processes.
- **Subsurface layer:** caves, lava tubes, and other subsurface environments.
- **Mission evaluation:** rover mobility, landing, illumination, and human/robotic operations.

Thermal and geological/environmental context must not be blended into the similarity score until sources, scale, units, timing, and quality have been checked. A strong terrain analog may be a weak thermal or geological analog; keep layer findings distinct.

## Main product modules

| Module | Purpose | 24-hour status |
|---|---|---|
| Weighted Similarity & Mission-Based Matching | Compare candidates against one mission profile and explain rankings | Core path; computed by Omar's module |
| Single-Parameter Explorer | Inspect each fingerprint metric independently | Included in the app |
| ShadowTwin | Compare illumination/shadow conditions | Planned unless compatible data and validated calculations arrive |
| Rover Gauntlet | Evaluate rover mobility/path costs; possible A* path demonstration | Planned unless a tested route output arrives |
| Analog Gap Analysis | Surface missing or weakly matched characteristics and analogy limits | Basic missing-data and limitation display in the MVP |
| Analog Passport | Record identity, sources, quality, metrics, matching evidence, gaps, and proposed experiment | Core path; generated from supplied data |

## 24-hour MVP acceptance target

- One selected lunar or Martian target.
- Three to five Earth candidates, or an explicit statement of how many valid candidates are available.
- One mission profile.
- All five terrain fingerprint groups, with at least one documented metric for each.
- Real, provenance-tracked data for the scientific demonstration.
- An explainable candidate ranking from the matching module.
- A Streamlit journey with three screens: Mission Setup, Results & Comparison, and Site Passport.
- One initial Analog Passport based on real supplied rows.
- At least one validation/sensitivity check from the science/matching workstreams.
- A reproducible run command, end-to-end check, and concise demo scenario.

Synthetic fixtures are permitted for parallel interface development only. They must remain clearly labelled and must never be presented as scientific findings.

## Mohammed's integration responsibilities

- Freeze one target, one mission, and the initial candidate set.
- Maintain repository branches, issue/PR workflow, dependencies, and README.
- Agree the data contract before integration.
- Integrate Ghassan's source metadata/coverage, Hiba's fingerprint table, and Omar's rankings/explanations.
- Keep the app read-only with respect to upstream scientific calculations.
- Produce and export the Analog Passport from actual supplied rows.
- Coordinate end-to-end tests, demo readiness, and truthful status reporting.

## 24-hour checkpoints

| Time | Required state |
|---|---|
| Hour 0–1 | Scope, target, mission, candidates, and source choices fixed |
| Hour 1–3 | Repository/environment and runnable app shell |
| Hour 3–6 | Three-screen interface and labelled development fixtures |
| Hour 6–10 | Data contract finalized; first source metadata/fingerprint outputs received |
| Hour 10–14 | Target/candidate feature comparison and map where coordinates exist |
| Hour 14–17 | Matcher ranking and feature-level explanation integrated |
| Hour 17–19 | Optional route/quality indicators only if supplied |
| Hour 19–21 | Passport generated from actual data |
| Hour 21–22 | End-to-end test on a clean/shared environment |
| Hour 22–24 | Feature freeze, final runbook, demo, evidence summary |

## Scientific safeguards

- A similarity score is a relative comparison, not a probability of mission success or a certification.
- Do not claim global novelty because a site is absent from one catalog.
- Spatial resolution is not measurement accuracy; resampling does not create information.
- Preserve source IDs, product versions, access dates, CRS, vertical reference, units, scale, coverage, NoData, quality flags, and usage terms.
- Earth cannot reproduce lunar vacuum, reduced gravity, radiation, or every atmospheric/thermal condition. State where analogy breaks down.
- Mark non-implemented functions as **Concept / Planned**.
