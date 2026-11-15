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

### Implemented in main
- Streamlit app with Mission Setup, Results & Comparison, Site Passport and clearly labelled paired synthetic DEMO MODE fixtures.
- NASA LOLA Site04 acquisition/structural QA workflow; Site04 is provisional.
- Multi-site NASA PGDA south-pole LOLA acquisition and inspection for Site01, Site04, Site06, Site07 and Site11, including five raster layers (elevation, LDEC counts, slope, Z RMS uncertainty, slope RMS uncertainty).
- Safe download/extraction and geometry inventory for the five provider-linked ROI archives; polygon-level QA reports raster-valid coverage, positive-shot direct support, zero-count/interpolated share, and elevation/slope plus RMS-uncertainty summaries. The archive batch downloader continues past provider errors and preserves successful files.
- Five provisional Copernicus GLO-30 Earth DSM source tiles: Haughton, McMurdo, Askja, Mauna Kea and Yungay, with manifest/checksum/structural QA; a separate Mauna Kea USGS 3DEP 1 m alternative is documented.
- Five-group DEM terrain fingerprint extraction and synthetic/GeoTIFF tests.
- CSV-driven target-aware matching, candidate ranking, feature contributions, Slope-only baseline and weight sensitivity utilities.
- Integration contracts, data provenance and judging-readiness gates.
- Latest full main CI at commit `2a64c90` (2026-11-15): **128 passed, 66 warnings**.

### Partially implemented / not scientifically complete
- The five provider-defined lunar ROI archive and five-layer audit tools are implemented, but the real archives/rasters still need to be downloaded and inspected locally; provider polygons are not approved AREA 67 study AOIs.
- No lunar target sub-AOI, Earth candidate AOIs, common analysis grid, or source harmonization policy has been approved.
- Real `terrain_fingerprints.csv` and `candidate_rankings.csv` are still absent; polygon-level tooling does not itself create terrain fingerprints.
- Cross-site real-data validation, feature-correlation/double-counting audit, approved tolerances, weights and completeness gates remain pending.
- End-to-end real-data app/Passport flow remains pending.
- Rover Gauntlet/A* remains separate optional work; it must be assessed before integration and only used on a documented real ROI.
- Real global Earth discovery/search is not yet implemented; current five Earth regions are provisional source packages, not a global scan.
- Thermal context (MODIS/Diviner/THEMIS), SPICE/ShadowTwin, mineralogy/geology fusion, water/ice, dust/process, subsurface and biological evidence are not integrated in the MVP score or a validated end-to-end product.

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
- Obtain analysis-ready target and 3–5 Earth candidates with manifest, footprints, QA and checksums.
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
1. Download and inspect the official Site01/Site04/Site06/Site07/Site11 ROI archives; compare their actual features/attributes and run the polygon-level support/uncertainty audit for sites with complete local inputs.
2. Decide which lunar provider ROI(s) to carry forward; use Site01's published illumination context as a research lead, not as an overall base-site ranking.
3. Finalize 3–5 Earth candidate landform AOIs, stable IDs, and authoritative boundary evidence; the whole 1° DEM tiles are not study ROIs.
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
