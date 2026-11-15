# AREA 67 — Science Execution Decision and 2026-11-15 Run Plan

**Status:** Working execution baseline, evidence-gated. This document selects the MVP direction; it does not approve a final survey AOI, certify a lunar base site, or claim a measured Earth–Moon match.

**Repository baseline:** `main` at `118a62d3f2136358bb61967f139ed22d301c4e25`  
**Verified CI:** 181 tests passed on the latest main workflow run (#269, 2026-11-15 08:47 UTC).  
**Challenge submission deadline:** 2026-11-15, 23:59 local time, per the 2026 Space Apps participant page.

## 1. MVP question and scope

**Question:** Which terrestrial environments can help prepare and test robotic mobility and surface-operation concepts for a high-illumination lunar south-polar ridge, and which dimensions of the analogy are strong, weak, or unsupported?

**MVP target:** one lunar target, four Earth candidate environments, one mission profile:

- Target: NASA PGDA LOLA Site01 — Connecting Ridge.
- Mission: Rover Navigation / Terrain Traversal.
- Earth candidates: Haughton Crater (impact/polar desert), Taylor Valley near Lake Hoare (cold polar dry valley), Yungay hyper-arid core (extreme aridity), and Askja caldera/lava terrain (volcanic landform). Mauna Kea remains a reserve candidate.
- MVP result: five-group terrain fingerprints, a transparent ranking with completeness/uncertainty caveats, an evidence-rich Analog Passport, and a map showing actual study AOIs.

This is a focused contribution to the challenge, not a claim that one Earth site reproduces the Moon. Terrain matching answers the rover-mobility question only. Thermal, illumination, geology, resources, radiation, vacuum, gravity, and human habitability remain distinct evidence dimensions.

## 2. Lunar target decision: Site01 Connecting Ridge

### Why Site01 is the lead target

NASA PGDA reports that, among the four original high-priority LOLA sites in Product 78, Site01 had the largest area with average illumination above 70% at 1 m above the surface during 2024-01-01 to 2026-01-01, and longer continuous illumination at 5 m. This is directly relevant to sustained surface-operation planning, but does not establish Site01 as the best permanent-base location overall.

A higher-detail regional dataset is available for the same named landform: Product 104's A306 Connecting Ridge Shape-from-Shading DEM (SDEM). It is a 5 m/pixel product derived from overlapping LROC NAC images registered to a LOLA-based reference. The archive includes elevation, hillshade, maximum-illumination orthomosaic, image/solar-bin coverage, best-input-resolution, SDEM–LDEM difference, multi-baseline slope and VRM roughness products.

The A306 SDEM elevation footprint reported in the local header audit is:
- X: -19,000 to -3,000 m
- Y: -20,000 to -4,000 m

These bounds exactly match the locally inspected Site01 LOLA raster bounds and grid dimensions. This makes A306 the lead higher-detail surface to test for Site01. Exact grid/CRS/registration checks are still required before using its pixels with the provider ROI geometries. The Site01 ROI shapefile's physical datum is not independently identified by its WKT; do not silently relabel it or apply an ME/PA shift.

### Provider ROI use

The valid native Site01 features are 0–4; features 5 and 6 are invalid and remain excluded unless authoritative topology provenance is obtained. Use valid features as source-defined illumination/quality anchors, not as final AREA 67 AOIs.

- **Feature 4 — primary anchor for AOI delineation:** 362 pixel centres, 11.05% positive LDEC support, median Z RMS 0.304 m, median slope RMS 1.780°.
- **Feature 2 — independent high-direct-support alternative:** 135 pixel centres, 17.78% positive LDEC support, median Z RMS 0.266 m, median slope RMS 1.664°.
- Feature 3 (484 centres) remains a larger comparison region; its uncertainty indicators are less favourable than Feature 4 in the current native-ROI audit.

The broader seven-ROI screen prevents over-interpreting these Site01 measurements: Site07 Feature 1 has the largest sample (612 centres), Site11 Feature 2 has the lowest median Z RMS (0.245 m) and slope RMS (1.533°), and Site04 Feature 3 has the lowest median slope RMS (1.473°) but only 101 centres and a steeper slope distribution. Site01 is therefore the working target because of the separate illumination/SDEM evidence, not because it wins every terrain or uncertainty metric. See the [multi-site ROI candidate screening report](reports/lunar_roi/MULTI_SITE_ROI_CANDIDATE_SCREENING_2026-11-15.md).

These are separate evidence dimensions, not an automatic score. Do not turn the small provider polygons into the final study area without evaluating the surrounding SDEM landform and the intended rover-analysis footprint.

### Initial Site01 screening window

For the first bounded visual/coverage screen only, the combined bounds of valid Site01 Features 0–4 are X=[-11,657.5, -11,002.5] m and Y=[-12,637.5, -11,857.5] m. A 1,000 m square centred on those combined bounds is:

`X=[-11,830,-10,830] m; Y=[-12,747.5,-11,747.5] m`

It encloses all five valid provider features and lies inside the A306/Site01 raster footprint. Treat it as a **screening window**, not a final AOI polygon or a claim of geomorphic homogeneity. The final AOI must be traced to a defensible landform/operations boundary using SDEM, illumination and terrain evidence.

## 3. Earth candidate shortlist

Use the five existing Copernicus GLO-30 DSM tiles as a consistent initial source family. Do not compare whole 1° tiles. Each candidate requires a named landform polygon, stable `site_id`, source citation, and a bounded AOI.

| Priority | Candidate | Analogue dimension to investigate | Current anchor / caution |
|---|---|---|---|
| 1 | Taylor Valley near Lake Hoare, Antarctica | Cold, dry polar-valley operations; permafrost/glacial and hyper-arid processes | Lake Hoare is a named search anchor inside the existing McMurdo tile. It is not itself an approved AOI; a valley-floor/bench/valley-wall unit must be selected. |
| 2 | Haughton Crater, Devon Island, Canada | Impact structure and polar-desert field operations | Use the authoritative crater reference, then distinguish rim, ejecta and floor. Do not merge those geomorphic units into one polygon. |
| 3 | Yungay, Atacama, Chile | Hyper-arid desert surface, soil/dust and extreme aridity | Use the published hyper-arid-core field reference (-69.8805°, -24.0637778°) as a search anchor; the current manifest marker is about 5.81 km away. |
| 4 | Askja, Iceland | Volcanic/caldera and lava-field landforms | Smithsonian reference coordinate is verified; select a specific caldera/lava geomorphic unit rather than the whole volcano. |
| Reserve | Mauna Kea, Hawaiʻi | Volcanic summit/flank terrain | Keep GLO-30 for the common-source baseline. Do not mix the local 1 m USGS DTM into the baseline until surface type, coverage, CRS and vertical-reference policy are harmonized. |

Copernicus GLO-30 is a DSM with EGM2008 vertical reference and no per-pixel quality companions in the current local handoff. It is a consistent starting family, not proof of bare-earth equivalence or equal effective resolution. Keep ArcticDEM and REMA as possible higher-detail source alternatives for follow-up, not as silent replacements in the initial ranking. Any source-family change requires a documented comparability review.

## 4. Terrain fingerprint protocol

Retain Hiba's implemented five groups and definitions:

1. **Slope:** continuous degrees; report P50, P90 and P95.
2. **TRI:** Riley eight-neighbour TRI; report median and P90; record radius, units and analysis scale.
3. **Local Relief:** moving-window P95–P5; report the median and P90 of the local-relief map; record physical window, cell count and actual centre-to-centre span.
4. **Terrain Distribution:** valid-area percentages for low/mid/high slope classes. The current 10°/25° thresholds are analytical experiment thresholds, not safety limits.
5. **Spatial Pattern:** largest connected steep-slope patch as a percentage of valid slope area; record threshold and 8-connectivity. Test 4-connectivity only as a sensitivity case if time permits.

Keep the current MVP matching profile as a baseline hypothesis: Slope 0.30, TRI 0.25, Local Relief 0.20, Spatial Pattern 0.20, Terrain Distribution 0.05. These weights are not NASA or rover-manufacturer standards. Keep the existing ±20% weight sensitivity analysis. Report feature-group completeness, valid-raster coverage, direct-observation support, uncertainty and ranking stability separately. Do not describe the score as probability or physical equivalence.

## 5. Scale and window decision — deliberately not hard-coded yet

Do **not** set `analysis_scale_m=30` or `relief_window_m=150` as approved values. Those values were previously suggested as candidates but are not supported by the team playbooks as approved parameters.

Required process:

1. Inspect local NASA Product 90 EFFRES around the Site01 screening window using a bounded COG read; do not download multi-gigabyte global rasters.
2. Inspect A306 `GLDBRES`, `GLDMASK`, `GLDSBCT`, `GLDSBCTALL`, `GLDDIFF`, and the multi-baseline SDEM slope/VRM products. Preserve their native grids and document differing grid sizes.
3. Choose at least two physically supported common scales for sensitivity. 30 m and 60 m may be tested first because GLO-30 is the current common Earth baseline, but the final choice must follow local effective-resolution evidence and the two-scale stability result.
4. Test at least two physical local-relief windows. Choose the final window only after reviewing the landform scale, valid-neighbour support, and scale/window sensitivity.
5. Leave missing values as null/NaN. Keep LOLA zero-count interpolated cells separate from NoData and positive direct-shot support.
6. Do not impose a minimum AOI sample count as a scientific rejection rule without validation. Report sample counts and neighborhood support, and flag results too small to be stable.

## 6. Differentiating evidence layers

Keep these independent from the terrain similarity score:

- **Illumination:** NASA Product 78 illumination evidence and, where available, A306 maximum-illumination orthomosaic/solar-bin maps. Show the time interval and observer height.
- **Effective resolution and image support:** NASA Product 90 EFFRES plus A306 best-input-resolution and image/solar coverage. Do not treat nominal 5 m posting as effective resolution.
- **Independent roughness cross-check:** NASA Product 90 LDRM products provide direct-LOLA roughness over multiple baselines (100–1600 m); use as external context/validation, not as a replacement for Hiba's Riley TRI.
- **Thermal context:** Diviner polar cumulative products provide bolometric brightness temperature by local-time/season bins at 240 m/pixel. This can support a contextual thermal panel, but its temporal and spatial support must be stated; it is not a 5–30 m terrain feature.
- **Shadowed regions/resources:** PSR maps and other resource evidence may be shown as proximity/context only. A PSR indicator is not proof of accessible or extractable ice.

No thermal, geology, volatile, biology or resource variable enters the terrain matching score unless its own source, units, time window, spatial scale and validation are established.

## 7. Evidence and interpretation rules

- Never compare absolute lunar and Earth elevations as if vertical datums were interchangeable.
- Do not infer effective resolution from pixel posting.
- Do not treat zero LDEC as NoData; report direct support separately.
- Do not infer the ROI shapefile's Moon-fixed frame from the matching projection parameters alone.
- Do not apply a generic ME/PA offset without authoritative frame provenance.
- Do not call a candidate a "safe", "best base", or "mission-certified" site from DEM metrics.
- Explain both the strength and the failure modes of each analogy: Earth gravity, atmosphere, radiation, vacuum and surface conditions remain different.
- Do not report synthetic demo rows as measured NASA results.

## 8. Team execution and handoffs

| Owner | Workstream | Immediate deliverable |
|---|---|---|
| Mohammed Jabr | Team lead, system integration and app | Freeze target/profile, approve data contracts, integrate only validated real CSVs, demo and release evidence. |
| Ghassan Al-Shoubi | Earth/Moon/Mars data acquisition and GIS | A306/Site01 + LOLA support/uncertainty package; Product 90 EFFRES bounded sample; final lunar AOI; 3–4 Earth polygons, footprints, manifests and preparation QA. |
| Hiba Sbouh | Terrain fingerprints and scientific validation | Real five-group fingerprints; synthetic and NoData tests; two-scale/window sensitivity; feature-correlation audit; uncertainty/clone sensitivity report. |
| Omar Salous | Matching and mission planning | Real candidate rankings, rejection reasons, distance contributions, Slope-only baseline, weight/tolerance sensitivity; keep route planner optional. |
| Team (unassigned) | Cross-dimension research/storytelling support | Source-backed analogue strengths/mismatches, experiment rationale, citations and demo narrative. Assign an owner before expanding beyond the terrain MVP. |

Every handoff must contain exact source/product/version, file paths, AOI ID and geometry, CRS/units/vertical reference, commands, output files, QA, checksums, caveats, and tests. A screenshot alone is not a handoff.

## 9. Release plan for the remaining hackathon window

1. Freeze the MVP to Site01 + Rover Navigation / Terrain Traversal + 3–4 Earth AOIs.
2. Finish the A306/Site01 and Product 90 effective-resolution/quality screen.
3. Draw and approve one lunar study AOI and 3–4 Earth landform AOIs; do not use whole source tiles.
4. Prepare compatible metric DEMs with explicit horizontal/vertical reference handling and source masks.
5. Run Hiba's real fingerprints on at least two supported scales; select the scale/window based on sensitivity, not habit.
6. Run Omar's matching with explicit tolerances and the current baseline weights; include data completeness and ranking stability.
7. Integrate the real target/fingerprint/ranking pair into the app; keep DEMO MODE as a clearly labelled fallback only.
8. Produce one Analog Passport with the measured match, source lineage, map, uncertainty, mismatches, and a test the Earth site can support.
9. Freeze features, run the end-to-end flow, rehearse the presentation, and submit before the official local deadline.

**Not in the MVP critical path:** A* routing, a global Earth-wide scan, deep learning, multiple mission profiles, or an unvalidated composite thermal/geology/resource score.

## 10. Official and project references

- NASA Space Apps 2026 challenge: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
- NASA PGDA Product 78, LOLA South Pole Sites: https://pgda.gsfc.nasa.gov/products/78
- NASA PGDA Product 104, Shape-from-Shading SDEMs: https://pgda.gsfc.nasa.gov/products/104
- NASA PGDA Product 90, Large-area LOLA/EFFRES/roughness/PSR products: https://pgda.gsfc.nasa.gov/products/90
- NASA LRO Diviner derived products: https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/DIVINER/Derived_Data.htm
- Impact Earth, Haughton crater: https://impact.uwo.ca/impact-craters/map/?crater_id=59
- US Antarctic Program, 2026–2027 field-camp planning (Lake Hoare/Taylor Valley): https://www.usap.gov/sciencesupport/scienceplanningsummaries/2026_2027/fieldcamps.cfm
- Smithsonian Global Volcanism Program, Askja: https://volcano.si.edu/volcano.cfm?vn=373060
- Published Yungay hyper-arid-core study: https://pmc.ncbi.nlm.nih.gov/articles/PMC8859261/
- Project method: `docs/TERRAIN_FINGERPRINT_METHOD.md`; current gates: `docs/FULL_CHALLENGE_ROADMAP.md` and `docs/LOCAL_JUDGING_READINESS.md`.
