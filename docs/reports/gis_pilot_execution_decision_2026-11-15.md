# AREA 67 GIS pilot — execution decision record

**Prepared:** 2026-11-15  
**Scope:** GIS data readiness, target shortlist, and the gates required before a defensible Earth–Moon terrain comparison.  
**Status:** Working decision record; it does not approve any provider polygon as an AREA 67 AOI.

## Executive decision

Do not run the terrain fingerprint extractor on whole source tiles, provisional landmark buffers, or tiny provider polygons simply to produce a ranking. That would create numbers without a defensible common study area.

Run the GIS pilot in this order:

1. **Lunar comparison set:** NASA PGDA Site01 (Connecting Ridge) and Site04 (Shackleton rim) as a two-target comparison, not as interchangeable labels.
2. **Earth pilot shortlist:** Haughton Crater, Askja, and Mauna Kea.
3. **Hold pending location clarification:** McMurdo and Yungay.
4. **First analytical product:** a source/coverage/quality dossier and AOI candidate package. Fingerprints follow only after AOIs and common-grid parameters pass the gates below.

This is the fastest route that preserves scientific defensibility. It uses the best documented candidates while avoiding unsupported geometry, datum, and resolution assumptions.

## Evidence-based rationale

### Lunar target shortlist

The repository's Site01 review records five aligned 3,200 × 3,200 LOLA layers, 100% finite raster-mask coverage, and 9.4942% positive LDEC support across the full raster. Site04's corresponding full-raster positive LDEC support is approximately 9.1541%. These percentages are site-wide, not ROI-specific, and must not be treated as direct-observation coverage for an AOI.

The local multi-site screening report compares seven valid provider ROI features across Site01, Site04, Site07 and Site11. The lunar pilot pair uses these five candidates:
- Site01 feature 4: 362 pixel centres, 11.05% positive LDEC support, median Z RMS 0.304 m, median slope RMS 1.780°. It is provider feature index 4 (the fifth feature / RoI 5), within the Site01 RoIs 4–6 highlighted for favorable illumination by PGDA Product 78.
- Site01 feature 2: 135 pixel centres, 17.78% positive LDEC support, median Z RMS 0.266 m; highest direct support among the seven screened candidates, but smaller sample.
- Site01 feature 3: 484 pixel centres, 9.09% positive LDEC support, median Z RMS 0.349 m; larger comparison sample.
- Site04 feature 2: 102 pixel centres, 14.71% positive LDEC support, median Z RMS 0.266 m.
- Site04 feature 3: 101 pixel centres, 13.86% positive LDEC support, median Z RMS 0.268 m.

The wider screen also found Site07 feature 1 has the largest sample (612 centres) and Site11 feature 2 has the lowest median Z RMS (0.245 m) and slope RMS (1.533°). These remain context candidates, not part of the current Site01/Site04 pilot pair. See [multi-site ROI candidate screening](MULTI_SITE_ROI_CANDIDATE_SCREENING_2026-11-15.md).

These are useful comparison candidates, not approved AOIs. The polygons are small (roughly 3,000–12,000 m² in the reported examples), and the current terrain fingerprint workflow uses neighbourhood metrics. Their usable interior support must be tested against the eventual analysis scale and relief window before any is selected. Do not silently enlarge, union, repair, or replace provider polygons.

PGDA's product description also highlights Site01's illumination context for the 2024–2026 interval. That makes Site01 important to retain in the comparison, but illumination alone does not establish the best landing/base site.

**Decision:** retain Site01 and Site04 as the lunar pilot pair, with Site01 as the working illumination/SDEM evidence anchor and Site04 as the LOLA comparison target. Test Site01 features 2, 3 and 4 plus Site04 features 2 and 3 for scale/support feasibility. No single polygon is selected yet.

### Earth candidate shortlist

| Priority | Candidate | Reason to retain | Blocking issue before AOI creation |
|---|---|---|---|
| 1 | Haughton Crater, Devon Island | Impact-crater and polar-desert context; ArcticDEM v4.1 catalog coverage and quality/time companions are documented | Choose a specific rim/floor/ejecta sector; obtain authoritative landform boundary and complete coverage |
| 2 | Askja, Iceland | Volcanic/caldera context; Copernicus tile covers the provisional reference point | Select a specific caldera/lava landform; verify exact ÍslandsDEM tile metadata if using it |
| 3 | Mauna Kea, Hawaii | Strong volcanic summit/flank relief; Copernicus and a USGS 3DEP 1 m alternative are documented | Select a geomorphic unit; resolve product choice and vertical-reference/grid policy; USGS point is close to tile edge |
| Hold | McMurdo / Dry Valleys | Strong cold, polar-desert analogue context; REMA catalog coverage is documented | The provisional marker does not identify a valley; select Taylor, Wright, Victoria, or another named valley first |
| Hold | Yungay, Atacama | Hyper-arid analogue context; Copernicus and SRTM coverage leads exist | Confirm the intended field-site coordinate; current marker differs from the published Yungay hyper-arid-core coordinate |

The shortlist is a project-planning recommendation, not a claim that these locations are the closest terrain matches to the Moon. The present source set is not sufficient to rank Earth sites scientifically.

## Common-grid policy: what is and is not decided

The following are hard requirements from the current GIS preprocessing specification and Hiba's extractor:

- Raw inputs remain immutable.
- Each AOI must be an approved, valid polygon with provenance and a stable ID.
- The analysis DEM must be projected, metric, north-up, and non-rotated.
- Horizontal reprojection and vertical-datum transformation are separate operations.
- Elevation units and vertical reference must be supported by authoritative source evidence.
- NoData is not filled or interpolated by default.
- Quality/count/uncertainty companions remain separate and are checked for coverage and grid alignment.
- The same physical analysis scale and relief-window policy must be applied across compared sites.
- A raster's posting is not evidence of effective terrain resolution.

**Not yet decided:** final AOI boundaries, target CRS, common pixel scale, grid origin, resampling operators, relief window, minimum valid-support fraction, coverage threshold, and vertical transformation pipeline. These are not safe to guess from the current documents. In particular, do not mix Copernicus DSM (EGM2008), ArcticDEM/REMA DSM (WGS84 ellipsoid), USGS 3DEP DTM (NAVD88), and SRTM (EGM96) as though their elevations share one vertical reference.

A 30 m exploratory grid may be evaluated because the Earth shortlist includes Copernicus GLO-30, but it is not approved as the final scientific scale. Run a scale-sensitivity test before locking it, and do not infer 30 m effective LOLA resolution from its 5 m posting.

## Execution gates

### Gate A — inputs physically present and verified

- Verify the existing local Site01 and Site04 five-layer LOLA sets and provider ROI archives by checksum, exact grid, masks and provenance. Re-acquire only missing or corrupt assets; GitHub does not carry the raw rasters.
- Verify checksums, exact grids, finite masks, LDEC counts, and both RMS uncertainty layers.
- Inventory current local Earth source tiles and quality companions for Haughton, Askja and Mauna Kea; acquire only missing assets. Keep McMurdo and Yungay on hold until their named-landform/reference-coordinate gates pass.
- Raw rasters are gitignored and cannot be inferred from the GitHub tree. Existing local handoff outputs include Site01 ROI screening and prior Earth-source work, but verify the active workstation's paths, sizes and checksums before rerunning. Do not use another teammate's empty workspace as evidence that the user's local assets are absent.

### Gate B — AOI and geometry

- Select named Earth landforms and obtain/digitize polygons from traceable authoritative sources.
- Inspect provider lunar ROI feature attributes and validity.
- Preserve invalid provider geometries unchanged; any repair preview remains a separate derivative and requires explicit provenance/review.
- Check complete polygon coverage and neighbourhood margins against each raster and quality layer.
- Test candidate polygon interior cell counts after accounting for slope/TRI/relief neighbourhood edge loss.

### Gate C — harmonized DEMs

- Record source IDs, hashes, epochs, surface type, CRS, vertical reference, units, masks, and quality layers.
- Approve target CRS, grid, pixel scale, resampling, mask policy, and vertical transformations.
- Stop any cross-site absolute-elevation comparison if a defensible vertical transformation cannot be established.
- Produce separate immutable run folders with manifests and QA.

### Gate D — Hiba handoff and matching

- Run synthetic regression tests first.
- Generate real fingerprints only from approved analysis-ready DEM/AOI pairs.
- Validate each row against the integration contract.
- Include per-site support and quality warnings; do not collapse LDEC support and RMS uncertainty into a single opaque score.
- Omar's similarity weights and ranking must remain explicit and mission-dependent. A terrain ranking is not a safety certification.

## Ownership and interfaces

- **GIS workstream:** source acquisition, AOI provenance/coverage, DEM preparation, QA, and GIS handoff.
- **Hiba:** terrain metric definitions, feature extraction, validation, and scientific interpretation.
- **Omar:** similarity model, weights, ranking, and route logic.
- **Mohammed:** Streamlit integration and application presentation.

GIS will deliver stable site/source IDs, approved AOIs, analysis-ready rasters, processing manifests, QA, and provenance. It will not silently change Hiba's metric definitions or Omar's ranking logic.

## Immediate next actions

1. Inventory the active local data packages and compare checksums/manifests with the existing Site01, Site04 and Earth-source audits; re-download only missing or corrupt assets.
2. Run the Site01 A306/LOLA quality screen and bounded Product 90 EFFRES/LDEC/error COG inspection after input verification; keep every layer on its native grid and do not download complete multi-gigabyte COGs.
3. Extend the candidate-polygon feasibility table with Site01 F4/F2/F3 and Site04 F2/F3: area, pixel-centre count, per-layer valid support, direct LDEC support, RMS summaries, and interior support after each proposed neighbourhood. Use the seven-ROI report as diagnostic context, not as a ranking.
4. In parallel, prepare authoritative AOI source references for Haughton, Askja and Mauna Kea; do not substitute point buffers. Keep McMurdo and Yungay held until the named valley/core and reference coordinate are resolved.
5. Only after those results, freeze the two-target lunar / three-site Earth pilot AOI and common-grid config, then run the real fingerprint pipeline.

## Claims this project must not make yet

- No Earth site is currently proven to be the closest analogue to Site01 or Site04.
- No provider ROI is yet an AREA 67-approved AOI.
- No common vertical datum or final common grid has been established.
- No real five-group Earth–Moon fingerprint comparison or validated ranking is established by this decision record.
- A complete raster mask does not mean direct altimetry coverage, and 5 m posting does not mean 5 m effective terrain resolution.
