# AREA 67 — 2026 Local Judging Readiness

**Purpose:** Turn the five categories in the NASA Space Apps 2026 Local Judging Rubric into an evidence-based release and presentation checklist for AREA 67.

**Applies to:** The active Space-to-Earth MVP: one Moon/Mars target compared with documented Earth candidates using five terrain-fingerprint groups, a transparent ranking workflow, and an Analog Passport.

**Status date:** 2026-11-14

## 1. How to use the judging rubric

The local rubric identifies five categories: **Impact, Creativity, Validity, Relevance, and Presentation**. Judges may use the categories and the local organizer's chosen weighting. This document does not invent category maxima or substitute its own scoring scale.

For every claim in the presentation, the team should be able to show the evidence behind it. A functioning interface is not, by itself, evidence that the underlying scientific comparison is valid.

## 2. Rubric-to-evidence matrix

| Rubric category | What a judge is evaluating | Evidence AREA 67 must show | Current readiness |
|---|---|---|---|
| **Impact** | The importance and potential reach of the problem being addressed; whether the work could meaningfully help or inspire others. | A clear operational problem and intended user; a concrete explanation of how finding Earth analog terrain can support analogue testing, mission preparation, or exploration planning; a defensible example of the decision the tool helps users make. Do not claim measured impact without user or stakeholder evidence. | **In progress.** The product concept and workflow exist; real candidate comparisons and user validation are still needed. |
| **Creativity** | Originality of the concept and innovation in the approach, including meaningful improvements over existing approaches. | Explain the integrated workflow: five terrain-fingerprint groups, target-to-candidate matching, inspectable feature contributions, sensitivity/baseline checks, and an Analog Passport. Show what each component adds. Compare against a simple baseline (including the existing Slope-only baseline). Do not claim global novelty merely because a feature is absent from the current repository or dataset. | **In progress.** The software architecture is implemented, but the distinctive value must be demonstrated with real, interpretable data. |
| **Validity** | Whether the method is grounded in sound principles, technically feasible, usable, and supported by evidence. | Show source provenance; product versions and units; CRS and vertical-reference caveats; analysis scale and neighborhood definitions; NoData and valid coverage; direct-observation support separately from raster validity; feature extraction validation; explicit tolerances and mission-weight assumptions; candidate rejection reasons; sensitivity/baseline results; reproducible tests; and limitations. | **Not ready for scientific claims.** Software tests pass, but the real Earth fingerprints, validated cross-site comparison, and team-approved study settings are still pending. |
| **Relevance** | How directly the submitted project addresses the challenge and its intended objectives, including meaningful use of NASA data where applicable. | Map each major feature to the exact NASA challenge requirements. Show how a Moon/Mars target leads to Earth candidate discovery and comparison. Identify the NASA source products used and explain why each supports the selected task. Keep optional extensions from distracting from the core challenge outcome. | **In progress.** The Space-to-Earth path is implemented as software; the end-to-end challenge result still depends on real Earth candidate data and validated fingerprints. |
| **Presentation** | How clearly, compellingly, and coherently the team communicates the challenge, its method, significance, and result. | A short narrative, a stable live demo, a clear comparison table/map, an Analog Passport with provenance and caveats, a concise explanation of the five feature groups, and an honest statement of what is measured versus assumed. Prepare screenshots or a recording as fallback. | **Prototype ready; final story pending.** The Streamlit screens run, but they currently use visibly labeled synthetic DEMO MODE data. |

## 3. Scientific release gates

Do not present a scientific ranking as a project result until every applicable gate below is complete.

### Gate A — Target and source data

- The team explicitly confirms the target site and the exploration/mission question.
- Ghassan supplies analysis-ready Earth candidate DEMs (target MVP: 3–5 candidates), footprints, source links, product/version/date, CRS, horizontal pixel size, vertical reference, units, NoData, valid coverage, quality/uncertainty notes, and processing history.
- The target and candidate IDs are stable and match across the manifest and fingerprint table.
- Original rasters remain outside Git; compact source manifests and QA reports are versioned.
- Nominal pixel posting is not described as effective resolution or accuracy without evidence.

### Gate B — Terrain fingerprints and validation

- Hiba supplies `data/processed/terrain_fingerprints.csv`, one row per analyzed site.
- All sites use a documented, comparable physical analysis scale and neighborhood/window definitions.
- The five groups are represented: Slope, Terrain Ruggedness Index (TRI), Local Relief, Terrain Distribution, and Spatial Pattern.
- Slope units, TRI definition/window, relief window, terrain-class thresholds, and spatial-pattern threshold/connectivity are explicit.
- Terrain-class percentages refer to valid area and sum to approximately 100%.
- Missing measurements remain null; never replace NoData or missing features with zero.
- Feature extraction is tested on synthetic surfaces with known behavior and checked against source/quality constraints.
- For lunar LOLA products, direct observation support is distinct from raster-valid coverage. The provisional Site04 QA reports 9.1541% positive LDEC spot-count support and 90.8459% zero-count/interpolated cells. These figures are not NoData percentages.

### Gate C — Matching method

- Omar's workflow consumes the validated fingerprint CSV and produces the canonical `candidate_rankings.csv` and robustness summary.
- The selected mission weights, feature tolerances, scale compatibility rule, and completeness policy are reviewed and approved by the team for this study; they are operational assumptions, not official NASA or rover-manufacturer standards.
- Candidate-level feature distances/contributions and missing/rejected groups are inspectable.
- Report both the weighted ranking and the Slope-only baseline; discuss whether correlated groups could double-count related terrain properties.
- Sensitivity analysis is included and described as a descriptive robustness check, not as a probability.
- A similarity score is described as a relative ranking index, not a probability, physical-equivalence percentage, mission-success estimate, or site certification.
- Direct-observation support and RMS uncertainty are reported separately unless a validated uncertainty-propagation method is added.

### Gate D — Application and demo integrity

- The app loads the real fingerprint and ranking files as a complete compatible pair. It must never mix one real file with one synthetic file.
- Every synthetic/demo screen, result, export, and screenshot remains clearly labeled as demo data.
- Target, candidate, mission profile, rank, score, feature contributions, provenance, data quality, assumptions, and limitations agree across the app, CSV, and Passport.
- Earth candidates alone appear on an Earth basemap; lunar/Martian coordinates are not plotted as Earth locations.
- Run the full test suite and record the commit SHA used for the demo.

### Gate E — Optional rover route

- Do not make the A* route part of the core scientific claim unless aligned elevation, slope, and TRI rasters exist for the selected site and ROI.
- Confirm projected CRS, affine grid geometry, units, masks, resolution, and source provenance.
- Record the route cost model, normalization scales, weights, connectivity, start/goal, and all assumptions.
- Benchmark the chosen ROI at its actual resolution.
- Describe the result as a hypothetical DEM least-cost path, not a rover-safety certification or proof of physical traversability.

## 4. Recommended judge-facing demo sequence

1. **Problem and relevance:** State the NASA challenge objective and the specific decision AREA 67 is designed to support.
2. **Mission setup:** Select the approved Moon/Mars target and explain the mission profile.
3. **Method:** Explain the five terrain groups and the common physical scale in plain language.
4. **Results:** Compare the Earth candidates, show the ranking and per-feature explanations, and explain any rejected candidates.
5. **Robustness and validity:** Show the baseline/sensitivity view and the source/data-quality caveats that affect interpretation.
6. **Analog Passport:** Open one candidate's provenance, measurements, assumptions, ranking, and limitations.
7. **Impact and next step:** Explain how a researcher or mission-planning team could use the result, what evidence is still needed, and what the system does not claim.

Only use real-data results in this sequence after Gates A–D pass. Until then, demonstrate the UI in DEMO MODE and call it a software prototype.

## 5. Non-negotiable communication rules

- Similar terrain descriptors do not make two locations equivalent planets.
- Do not compare absolute elevations across incompatible vertical references.
- Resampling does not create resolution.
- Do not impute missing values or NoData as zero.
- Do not confuse valid raster coverage with direct instrument-observation support.
- Do not describe relative similarity as probability, mission success, or certification.
- Do not claim global novelty from the absence of a candidate in one catalog.
- A DEM least-cost path is not a rover safety assessment.
- Clearly separate measured data, software-derived metrics, team-selected assumptions, and unresolved limitations.

## 6. Current project snapshot (2026-11-15)

- `main` contains the Streamlit MVP, Analog Passport, application contracts, provisional lunar LOLA Site04 acquisition/QA, Earth DEM source acquisition/QA/screening, and the CSV-driven Space-to-Earth matching workflow.
- The latest full test run on `main` passed **85 tests** (24 warnings) after the CSV workflow was merged. The A* route-planning feature branch separately passed 76 tests after geometry/resource/provenance safeguards; it remains a Draft PR and is not part of `main`.
- The Earth-data package records five provisional Copernicus GLO-30 DSM source tiles (Haughton, McMurdo, Askja, Mauna Kea, Yungay) and one separate Mauna Kea USGS 3DEP 1 m alternative. Large raw rasters remain gitignored.
- These source tiles and named points are **not approved candidate AOIs**. No final ROI boundaries, site IDs for the study, common analysis scale, or cross-source preparation policy have been approved. Metadata/structural QA does not prove physical accuracy or suitability.
- The matching CLI requires explicit feature tolerances and explicit minimum completeness settings. Those values are team-selected study assumptions, not NASA specifications; no approved real-study configuration is committed.
- Hiba's validated `data/processed/terrain_fingerprints.csv` is still not available on `main`; no real `candidate_rankings.csv` or validated ranking/Passport result exists.
- The Streamlit interface remains in clearly labelled **DEMO MODE** because the real processed fingerprint/ranking pair is not available. Synthetic fixtures are software/demo data only.
- Direct LOLA observation support, valid raster coverage, and RMS uncertainty remain distinct. Site04's 9.1541% positive LDEC support is not its NoData percentage.
- The optional A* route work is in Draft PR #9. Its latest branch CI passed 76 synthetic tests and adds affine-grid orthogonality checks, a default 250,000-cell software guard, and a route metadata sidecar. It has not been run on an approved real ROI and is not a rover-safety certification.

**Current verdict:** AREA 67 now has a functioning application, reproducible Earth source-screening tools, and a CSV-driven matching implementation. It is still **not ready to claim a validated planetary-analog result**. The blockers are approved AOIs/target, harmonized analysis scale and processing policy, Hiba's real validated fingerprints, team-approved tolerance/completeness settings, and a real end-to-end run.
