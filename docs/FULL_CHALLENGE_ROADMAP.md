# AREA 67 — Full NASA Challenge Roadmap

**Purpose:** Preserve the complete challenge ambition while separating implemented software, planned capabilities, evidence-backed results, and unresolved scientific decisions.

**North star:** Discover and characterize useful terrestrial analog environments and processes for lunar bases and Mars exploration using open Earth, Moon, and Mars data. AREA 67 is not limited to rover terrain traversal. It is a multi-dimensional planetary-analogue discovery and mission-planning platform.

## 1. Challenge requirements translated into product outcomes

| Challenge dimension | AREA 67 product outcome | Evidence required before scientific claims |
|---|---|---|
| Global discovery of new Earth analogs | Earth-wide candidate discovery and screening; support known and less-characterized environments | Reproducible geographic search coverage, candidate-generation criteria, catalog/context review, and uncertainty about novelty |
| Moon and Mars targets | Independent target libraries and target AOIs for lunar and Martian regions | Exact source products, stable IDs, spatial footprints, product versions, coordinate systems, units and quality records |
| Terrain/topography | Five-group Terrain Fingerprint: slope, ruggedness/TRI, local relief, terrain distribution, spatial pattern | Compatible physical scale and windows, validated extraction, masks, coverage, uncertainty, reference/sensitivity tests |
| Geology, mineralogy, surface materials | Surface-material and composition evidence layers; compare materials/processes separately from morphology | Traceable instrument products, calibrated units/classifications, spatial resolution, provenance and confidence/limitations |
| Temperature/environmental extremes | Thermal/environmental analogue profiles for Earth, Moon and Mars | Compatible temporal/spatial products, day/night/season context, units, uncertainty and carefully defined metrics |
| Illumination/shadow | ShadowTwin: time-dependent illumination, shadow duration and solar geometry for DEMs | Ephemeris/SPICE context, body-specific solar geometry, DEM/coordinate validation and temporal sampling tests |
| Water, ice, permafrost/resources | Resource-context layers and evidence summaries | Sensor/product-specific detection semantics, uncertainty, observation time, spatial support and no unsupported presence/absence claims |
| Dust, wind, erosion and surface processes | Process analog library and event/process comparison | Observational or model products with temporal coverage, compatible variables and causal limits stated |
| Biology/habitability/biosignatures | Optional habitability/extreme-environment context, not a proxy for extraterrestrial life | Valid biological/environmental datasets, scale/time matching and strict distinction between Earth biology and planetary habitability inference |
| Caves, lava tubes and subsurface | Subsurface analog catalog and feature-level passports | Georeferenced cave/lava-tube/structural evidence, survey provenance and explicit coverage gaps |
| Landing, mobility, robotics, construction, human operations | Mission Matching profiles for different engineering/science objectives | Objective-specific metrics, independently reviewed weights/tolerances and no safety certification claims |
| Communication and education | Interactive maps, comparisons, site/process passports and reproducible reports | Data citations, readable caveats, downloadable evidence packages and demo reproducibility |

## 2. Product architecture — do not collapse everything into one score

### Discovery and comparison core
1. **Analog Radar** — discover and rank Earth environments from a selected Moon/Mars target; long-term Earth-to-Space and global Earth discovery.
2. **Mission Matching** — choose the question first, then select only scientifically relevant features and weights. The current MVP profile is Rover Navigation / Terrain Traversal; it is not the only future profile.
3. **Multi-Dimensional Evidence Stack** — keep terrain, geology/materials, thermal, illumination, volatile/resource, atmospheric/process, biological and subsurface evidence as distinct, provenance-aware layers. Combine only when spatial/temporal compatibility and method are justified.
4. **Analog Passport** — a dossier per candidate and target: what matches, what does not, source provenance, coverage, uncertainty, comparison metrics, practical experiment use, limitations and lineage.
5. **Global Discovery Atlas** — Earth map/search over candidate windows and known analogs, including transparent screening of under-characterized areas. A catalog absence is not proof of novelty.

### Mission and environment tools
6. **Rover Gauntlet** — hypothetical least-cost routes and terrain-cost scenarios, not rover-safety certification.
7. **ShadowTwin** — time-dependent illumination and shadow analysis using terrain geometry and appropriate ephemeris/SPICE data.
8. **Thermal Twin** — compare thermal regimes and extremes across Earth/Moon/Mars with explicit temporal/spatial compatibility.
9. **Resource & Volatile Lens** — map available water/ice/volatile indicators and observation support without treating proxy measurements as confirmed extractable resources.
10. **Geology & Materials Lens** — connect mineralogical/geochemical evidence to terrain candidates and experiments.
11. **Process Analog Library** — dust, wind, erosion, volcanic, impact, sedimentary, glacial/permafrost and other process analogs.
12. **Subsurface Explorer** — caves, lava tubes, pits, voids and underground environments where evidence exists.

These are product capabilities, not claims that all corresponding algorithms or datasets are already implemented.

## 3. Mission profiles are a framework, not a single hard-coded mission

Candidate profiles to design and validate independently:
- Rover Navigation / Terrain Traversal (current MVP only).
- Landing / Hazard Assessment (requires landing-specific evidence and validated limits; not inferable from a general terrain rank).
- Lunar Base Site Characterization (multi-dimensional surface, illumination, thermal, resource, construction/logistics context).
- Resource Prospecting / ISRU Context (resource evidence, not extraction feasibility).
- Geology / Science Traverse (materials, stratigraphy, landforms and process context).
- Human Surface Operations (environmental exposure and operational context; Earth analog limitations explicit).
- Mars Robotic Exploration (terrain, atmospheric/process and seasonal context when reliable products are available).
- Cave / Lava-Tube Exploration (subsurface evidence and access constraints).

Do not populate selectable profiles with empty or misleading results. A profile becomes selectable only when its input contract, metrics, assumptions, tests and explanation are implemented. The app should clearly label planned profiles.

## 4. Evidence model and comparison rules

- Each observation is an evidence record with body/site, stable site ID, exact source/product/version, instrument, acquisition/observation time, footprint, native and analysis resolution, CRS/coordinate reference, units, quality flags, uncertainty, processing lineage and license/access details.
- Distinguish direct observation, interpolation, model output, derived product, expert interpretation and synthetic test fixture.
- Preserve NoData/nulls; never turn missing observations into zero or an absence claim.
- Keep spatial scale, temporal support and physical meaning explicit. Resampling does not create resolution.
- Never compare absolute elevation across planetary bodies as if vertical references were interchangeable. Prefer documented local/relative descriptors when appropriate.
- Do not force heterogeneous dimensions into a single score. Report dimension-specific matches and evidence coverage first; any composite score requires an objective-specific, reviewed method.
- Report similarity, evidence completeness, uncertainty, ranking stability and operational constraints separately.
- Explain where the analogy works, where it breaks, what it can help test, and what it cannot represent (e.g. gravity, vacuum, radiation and atmosphere differences).
- A route is not a safety certification; a thermal proxy is not a habitat guarantee; a resource indicator is not a confirmed mineable reserve.
- Never claim global novelty from one catalog's absence. Describe novelty as a documented discovery hypothesis with search coverage and prior-work review.

## 5. Current repository state — verified 2026-11-15

### Presentation MVP release snapshot (2026-11-15)

The current in-repository demonstration is a **reproducible exploratory software pilot**, not a validated planetary-analog result. It uses one Site01 target context window and three Earth reference windows (Haughton, Yungay, Mauna Kea); every footprint and analysis/matching setting remains provisional. Site04 is excluded from the ranked demo. Askja is held out because its current sampled window is near-flat/equal-elevation dominated, not because all Askja terrain has been assessed.

The app-facing four-row fingerprint CSV, three-row ranking CSV, and robustness sidecar are checked in under `data/processed/`. The canonical raw-raster builder is `src/data/build_exploratory_pilot.py`; it invokes the existing fingerprint, matching, and robustness implementations and writes a checksum-bearing run manifest. Use the non-overwriting output-path example in [the MVP method and results](FINAL_MVP_METHOD_AND_RESULTS_2026-11-15.md). The [judge demo script](JUDGE_DEMO_SCRIPT_2026-11-15.md) keeps the narration aligned with the actual caveats.

The tracked results do not approve an AOI, scale, resampling/mask policy, coordinate/vertical frame, weight, tolerance, or candidate's suitability. Site01 direct LDEC support in the pilot window is 9.235%; it is distinct from raster-valid coverage. Site04's separate 8.292% operational-window figure is not comparable as a cross-target ranking metric. Generated rasters and raw inputs remain outside Git.

The follow-up AOI implementation check found no defensible, reproducible geometry source for the four selected target/candidate areas in the current checkout: Site01 provider ROI source files are absent locally and their recorded frame caveat remains; Haughton's cited geology map has not been georeferenced/digitized; Yungay's reference point differs from the published field locality by about 5.81 km; and Mauna Kea's geomorphic unit is not selected. No AOI polygons or new fingerprints were fabricated. The extractor now validates polygon geometry and rejects AOIs extending beyond DEM bounds before calculating features; see [AOI implementation status](reports/AOI_MVP_IMPLEMENTATION_2026-11-15.md). The existing five-group ranking remains the primary exploratory output; Slope-only is diagnostic.

### Implemented in main
- Streamlit application with five workspaces: Mission Control, Analog Radar, Terrain Lab, Planetary Atlas, and Analog Passport. The live app is documented at https://area-67.streamlit.app/ and the repository deployment instructions identify `main` / `app/main.py` as the Streamlit Community Cloud configuration.
- Analog Radar includes a PyDeck/CARTO Earth reference-anchor map with dark/light/voyager basemaps, rank-coloured markers, hover details, candidate filtering, map focus, and optional labels. These are reference-window anchors only, not AOI polygons.
- Terrain Lab includes the five-group evidence tables, single-parameter exploration, matcher-supplied feature-contribution visualization, and side-by-side source-quality metrics.
- Planetary Atlas links to NASA Moon Trek and Mars Trek as external map explorers. Those pages are not integrated into AREA 67's matching engine; Mars still has no target fingerprint in the current MVP.
- Analog Passport has readable evidence tables, source-product links, Markdown export, and a ZIP evidence bundle containing the Passport, JSON metadata, fingerprint CSV and matching row. Raw source rasters remain excluded from the bundle and repository.
- Paired synthetic DEMO MODE fixtures remain clearly labelled; the integrated four-row **real-raster exploratory pilot** (Site01 target + three Earth candidate windows) remains prominently labelled exploratory and not-approved AOI.
- NASA LOLA Site04 acquisition/structural QA workflow; Site04 is provisional.
- Multi-site NASA PGDA south-pole LOLA acquisition and inspection for Site01, Site04, Site06, Site07 and Site11, including five raster layers (elevation, LDEC counts, slope, Z RMS uncertainty, slope RMS uncertainty).
- Safe download/extraction and geometry inventory for the five provider-linked ROI archives; polygon-level QA reports raster-valid coverage, positive-shot direct support, zero-count/interpolated share, and elevation/slope plus RMS-uncertainty summaries. Both ROI-archive and five-layer raster batch downloaders continue past individual provider errors, preserve successful files, and report failed items.
- Five provisional Copernicus GLO-30 Earth DSM source tiles: Haughton, McMurdo, Askja, Mauna Kea and Yungay, with manifest/checksum/structural QA. Two adjacent Mauna Kea USGS 3DEP 1 m DTM tiles are recorded in EPSG:26904 and EPSG:26905; the eastern tile's vertical reference and elevation units are unverified, and the pair is not approved for mosaicking.
- Read-only Earth raster inventory and structural preflight, local block-wise raster audit, and remote COG/STAC inspection using HTTP byte-range checks and bounded windows.
- Exploratory Site01-to-Earth pilot: four app-facing fingerprint rows, three relative candidate rankings, Slope-only baseline, 11 weight-sensitivity scenarios, source checksums, Earth sample-window GeoJSON, and an evidence report under `docs/reports/EXPLORATORY_PILOT_2026-11-15.md`. The requested 150m local-relief window is rounded to 5 cells with an actual 120m centre-to-centre span.
- Site01 A306 SDEM + LOLA + Product 90 bounded quality-screen tooling. The locally reported 2026-11-15 run sampled 10 local raster layers and all 3 Product 90 windows (20 m EFFRES/LDEC/height-error products); the result is a screening report only, not AOI approval or a final scale decision.
- The LOLA multi-site acquisition CLI now supports package and direct-script invocation; the regression test for both entry points is merged (PR #70). The GIS acquisition workflow is manual-dispatch only, avoiding repeated large downloads on every `main` push. Remote probes cover ArcticDEM Haughton, REMA McMurdo and ÍslandsDEM Askja; full remote rasters were not downloaded.
- Provisional Earth landmark/reference-point GeoJSON with 13 records; these are not AOI boundaries and include unresolved Haughton, McMurdo and Yungay location differences.
- Five-group DEM terrain fingerprint extraction and synthetic/GeoTIFF tests.
- CSV-driven target-aware matching, candidate ranking, feature contributions, Slope-only baseline and weight sensitivity utilities.
- Integration contracts, data provenance and judging-readiness gates.
- Latest verified post-merge `main` CI after PR #116: [workflow run #43720384275](https://github.com/MohammadJabr/area-67/actions/runs/43720384275) completed successfully on commit `8ea623a0db3294612c1752760b7971fff1ae7b09`. Dependency installation, geospatial artifact ignore-policy check, source/test compilation, and the full test suite all passed.

### Partially implemented / not scientifically complete
- **Map layers are not yet a complete planetary GIS integration.** Earth map pins are reference-window coordinates; NASA Moon Trek and Mars Trek open as external resources. There are no approved polygon AOIs or validated/hosted raster tiles for native elevation, hillshade, slope, TRI, local-relief, 3D terrain, lunar overlays or Mars overlays. Do not represent the external NASA map links as ingested AREA 67 evidence.
- **The public URL is configured for a main-branch Streamlit deployment, but the post-merge app page was not independently fetched by the repository audit.** Verify https://area-67.streamlit.app/ in a private browser after each Streamlit rebuild and inspect its app logs if the previous release remains visible.
- The five provider-defined lunar ROI archives and five-layer audit tools are implemented. Local Site01 and Site04 provider ROI archives and all five native raster layers have now been inspected with polygon-level support/uncertainty QA, read-only invalid-geometry previews, and pixel-registration audits. Site01 has seven features (five valid, two invalid); all 607 source vertices align with its raster pixel-centre lattice. Site04 has four features (two valid, two invalid); all 325 source vertices align with its raster pixel-centre lattice. The invalid features remain excluded from official native-geometry ROI statistics. Equivalent site-level review remains for Site06, Site07 and Site11. Provider polygons are not approved AREA 67 study AOIs; see the [Site01 review](reports/lunar_roi/SITE01_COORDINATE_AND_SDEM_REVIEW.md) and [Site04 review](reports/lunar_roi/SITE04_COORDINATE_AND_SDEM_REVIEW.md).
- The working lunar pair remains Site01 (primary illumination/A306 evidence anchor) and Site04 (LOLA comparator). The first app-facing exploratory ranking uses Site01 against Haughton, Yungay and Mauna Kea 990m reference-centred windows; Askja is held out because its current reference-centred window is flat/equal-elevation dominated. All windows are explicitly NOT APPROVED AOIs, and Earth DEM effective resolution remains unvalidated. No absolute cross-body elevations or unverified lunar datum transformations are used.
- The reference-point GeoJSON contains points only. Haughton has a ~1.47 km marker/reference difference; McMurdo's provisional point is not a named valley and alternatives may fall outside the local Copernicus tile; Yungay's marker differs by ~5.81 km from a published field reference. Askja and Mauna Kea reference points align at recorded precision but do not define the target landform.
- Remote COG 500 × 500 windows prove only that selected assets can be queried and return values in those windows; they do not establish full-tile coverage, effective resolution, or candidate suitability.
- `data/processed/terrain_fingerprints.csv` and `candidate_rankings.csv` now contain an **exploratory four-row fingerprint / three-candidate ranking** from real NASA LOLA Site01 and Copernicus GLO-30 reference-centred windows. These are not yet canonical Hiba/Omar-approved study outputs because the sample windows are not approved geomorphic AOIs and the scale/weights/tolerances remain provisional.
- Cross-site real-data validation, feature-correlation/double-counting audit, approved tolerances, weights and completeness gates remain pending.
- The app/Passport now runs end-to-end on the exploratory real-data pair. The validated end-to-end scientific release remains pending until Ghassan/Hiba approve AOIs and harmonisation, Hiba independently reruns the canonical feature CLI and sensitivity checks, and Omar independently reruns matching/robustness with approved settings.
- Rover Gauntlet/A* remains separate optional work; it must be assessed before integration and only used on a documented real ROI.
- Real global Earth discovery/search is not yet implemented; current five Earth regions are provisional source packages, not a global scan.
- Thermal context (MODIS/Diviner/THEMIS), SPICE/ShadowTwin, mineralogy/geology fusion, water/ice, dust/process, subsurface and biological evidence are not integrated in the MVP score or a validated end-to-end product.

### Site04 ROI evidence update — 2026-11-15

The local Site04 review now includes the original provider shapefile, all five matching LOLA rasters, the polygon support/uncertainty audit, the 325-vertex pixel-registration audit, and a read-only `make_valid` sensitivity preview.

- Original source features 0 and 1 are invalid because of ring self-intersections; features 2 and 3 are valid. The invalid source features remain excluded from the official native-geometry ROI statistics.
- All 325 source ring vertices lie exactly on the local Site04 raster's pixel-centre lattice. No half-pixel shift is indicated for this specific shapefile/raster pair. This does not identify the physical lunar body-fixed frame.
- Valid feature 2 has 102 pixel centres, 100% elevation coverage, and 14.71% positive LDEC direct-shot support; feature 3 has 101 centres, 100% elevation coverage, and 13.86% positive direct-shot support. Their remaining valid LDEC cells are zero-count/interpolated support, not NoData.
- The in-memory repair preview splits invalid feature 0 into two polygon components and feature 1 into three polygon components plus three LineString remnants. All statistics for these repaired candidates are preview-only; they do not establish provider intent or AOI approval.
- The legacy ROI shapefile's physical lunar datum/frame remains unknown. Do not apply a guessed ME/PA shift or generalize the local pixel-registration result to external lunar products.


### Site01 ROI evidence update — 2026-11-15

The local Site01 (Connecting Ridge) review now includes the provider ROI shapefile, all five matching LOLA raster layers, polygon-level support/uncertainty QA, an in-memory `make_valid` sensitivity preview, a 607-vertex pixel-registration audit, and valid-polygon geometry inventory.

- All five rasters are 3200 × 3200 Float32 layers with a common 5 m posting, affine transform, CRS and bounds. Each reports 10,240,000 finite/mask-valid pixels; exact-grid QA passed.
- Site-wide positive LDEC support is 9.4942%. This is not full direct observation: zero-count cells are interpolated LDEM support, not NoData.
- Five of seven original ROI features (features 0–4) are valid. Their pixel-centre counts range from 135 to 484, direct LDEC support from 4.73% to 17.78%, and all have 100% elevation coverage at included pixel centres.
- Original features 5 and 6 are invalid due to ring self-intersections. Their in-memory repair previews are diagnostic only: feature 5 produces two polygon components, including a 12.5 m² fragment with one pixel centre; feature 6 produces one polygon plus two LineString remnants. Do not replace source geometry or mix preview statistics into native-geometry ROI QA.
- All 607 source vertices across all seven features lie exactly on the local raster's pixel-centre lattice (0 m maximum residual). This does not resolve the physical lunar ME/PA frame or fix topology.
- Among the five valid polygons, Site01 feature 2 has the highest direct LDEC support (17.78%) and lowest median Z RMS (0.2658 m); it is not thereby an approved or overall superior target. Site04's valid features have lower median slope RMS (1.604° and 1.473°). These dimensions remain separate and do not establish a site ranking.

The source rasters and machine-readable QA/preview outputs remain local and gitignored. The detailed measurements, paths and reproduction commands are recorded in [the Site01 review](reports/lunar_roi/SITE01_COORDINATE_AND_SDEM_REVIEW.md).


Detailed measurements and provenance are recorded in `docs/LOLA_ROI_QUALITY_AUDIT.md` and `docs/reports/lunar_roi/SITE04_COORDINATE_AND_SDEM_REVIEW.md`. The immediate scientific decisions are to test a Site01/Site04 two-target pilot pair (Site01 as primary illumination/A306 anchor; Site04 as LOLA comparator), select candidate polygons only after neighbourhood-support analysis, resolve the intended topology/provenance of invalid provider features where relevant, and agree a common physical analysis scale and neighborhood/window policy before real fingerprint extraction. The working Earth pilot shortlist is Haughton, Askja and Mauna Kea; McMurdo and Yungay remain held pending location clarification.

### Important review note
The application currently exposes the only supplied target and profile from the loaded ranking CSV. Seeing only MOON_DEMO_01 and Rover Navigation / Terrain Traversal is therefore a property of the synthetic fixture, not proof that the product is scientifically limited to one target/profile. Do not add fake selectable entries. Real target/profile options should be driven by validated datasets and implemented profile contracts.

## 6. Workstreams and handoffs

| Workstream | Owner (current team assignment) | Deliverables / handoff | Blocker / dependency |
|---|---|---|---|
| System integration, product and app | Mohammed Jabr | Contracts, app integration, global product workflow, end-to-end demo, release evidence | Validated input data and workstream outputs |
| Earth/Moon/Mars data and GIS | Ghassan Al-Shoubi | Source manifest, AOIs, analysis-ready rasters, coverage/quality/uncertainty reports, coordinate and vertical-reference handling | Team AOI/source/scale decisions; source coverage and license checks |
| Terrain fingerprints and scientific validation | Hiba Sbouh | Five-group CSV, optional maps, test/validation report, real-scale sensitivity/correlation results | Approved AOIs, prepared grids, common scale and explicit method settings |
| Matching and mission planning | Omar Salous | Objective-specific metrics, group distances, rankings, baselines, sensitivity, route planning handoff | Real fingerprints, approved tolerances/weights/completeness |
| Cross-dimension research (shared extension) | Team assignment to be agreed | Thermal, geology/materials, resource/volatile, process and subsurface evidence contracts | Product selection, scientific ownership, compatible datasets and validation |

Every handoff should include the exact commit, input manifest, output paths, commands, tests, caveats and explicit decisions still needed. A screenshot alone is not a data handoff.

## 7. Release gates — the order matters

### R0 — Scientific study design
- Confirm target question(s): lunar base region, Moon landing/operations, Mars landing/operations, or separate study tracks.
- Confirm stable target/candidate AOI IDs and polygons; distinguish the site name from its actual analysis ROI.
- Decide whether baseline uses a single consistent DEM family or carefully justified mixed regional sources.
- Approve comparable physical scale, processing/reprojection/resampling policy, windows, vertical-reference treatment, uncertainty representation and quality rules.
- Keep all unresolved decisions explicit; no invented values.

### R1 — Real terrain baseline
- Obtain analysis-ready Site01/Site04 lunar comparison inputs and three primary Earth candidates with manifest, footprints, QA and checksums.
- Produce one real five-group fingerprint row per site.
- Run independent validation, coverage review, real correlation audit and at least one supported scale/window sensitivity study.
- Do not release a ranking until comparability and missingness are reviewed.

### R2 — Real mission matching
- Agree objective-specific metrics, weights, tolerances and completeness gates.
- Produce ranked Earth candidates, rejected-candidate reasons, feature contributions, baseline comparisons and robustness sidecar.
- Have a reviewer inspect whether correlated features are double-counted and whether source uncertainty could change conclusions.

### R3 — Evidence-rich Passport and map
- For at least one candidate, show target-vs-Earth evidence, spatial map, source lineage, dimensions of analogy, mismatch/unknowns, suggested experiment and operational relevance.
- Export reproducible report and data citations.
- Never hide missing dimensions behind a single composite score.

### R4 — Differentiating extensions
Prioritize one vertical at a time, with separate data contracts and tests:
1. ShadowTwin and thermal context for a carefully selected lunar polar question.
2. Geology/materials and resource/volatile context when instrument products can be compared.
3. Process analogs (dust, wind, erosion, volcanic, impact, ice) with time-aware evidence.
4. Subsurface analogs using independently verified cave/lava tube data.
5. Global Earth discovery and Earth-to-Space search after the evidence model and candidate tiling strategy are ready.
6. Add mission profiles only with their own scientific/engineering contract and validation evidence.

### R5 — Judge-ready demonstration
- A real target-to-Earth result with transparent strengths and mismatches.
- Map and visual evidence for selected candidate(s), not demo-only rankings.
- Reproducible pipeline and provenance trail.
- Clear statement of NASA data used, what is measured vs modeled/interpreted, uncertainty, limitations and what each analog helps prepare for.
- A stable demo fallback clearly marked as synthetic if real data is unavailable.

## 8. Immediate next actions (not silently assigned as approvals)
1. Site01 and Site04 local ROI/raster reviews are recorded; seven-candidate screening also covers selected Site07 and Site11 features. Complete the full archive, five-layer support/uncertainty, topology and registration review for Site06, and full Site07/Site11 review only if those sites remain in scope.
2. Execute the Site01/Site04 comparison pilot in `docs/SCIENCE_EXECUTION_DECISION_2026-11-15.md`; use Site01 for the A306/illumination evidence anchor and Site04 as the LOLA comparator. Delineate and approve AOI(s) only after source, frame and neighbourhood-support checks.
3. Finalize three primary Earth candidate landform AOIs (Haughton, Askja, Mauna Kea), stable IDs and authoritative boundary evidence; keep McMurdo and Yungay held until named-landform/reference-coordinate issues are resolved. Whole 1° DEM tiles are not study ROIs.
4. Approve a common physical analysis scale, projection, resampling/reprojection policy, vertical-reference treatment, windows, and quality/uncertainty policy.
5. Have Ghassan hand over analysis-ready target/candidate rasters and manifests; have Hiba produce and validate the real fingerprint CSV.
6. Agree and document feature tolerances and completeness thresholds; run real matching, inspect correlations/sensitivity, then connect outputs to the app.
7. In parallel, evaluate the open Rover Gauntlet branch and decide whether to merge it as a demonstrable extension or keep it out of the scientific MVP.
8. Scope the first differentiating cross-dimension demonstration (e.g. lunar polar illumination + thermal context) only after source product compatibility is verified.

## 9. Definition of done for AREA 67
AREA 67 is not "done" because the UI loads or tests pass. A release is complete only when a user can:
- choose a documented Moon/Mars target and an explicit mission/science question;
- discover Earth candidates through a reproducible, documented search process;
- inspect dimension-specific similarities and differences backed by traceable data;
- understand coverage, uncertainty, missing evidence and limits of analogy;
- see why a candidate is useful for a stated experiment and what it cannot validate;
- reproduce the evidence package from versioned inputs/configuration;
- export a map, comparison, and Analog Passport with citations and caveats.

This roadmap is ambitious by design but evidence-gated: expand the science without fabricating measurements, scores or capabilities.
