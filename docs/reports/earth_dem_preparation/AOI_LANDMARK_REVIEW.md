# AREA 67 — Provisional Earth Candidate Landmark Review

**Review date:** 2026-11-15  
**Purpose:** Interpret the generated whole-tile previews and verify that provisional site markers correspond to defensible geographic reference points.  
**Status:** Evidence review only. No AOI polygon, candidate ranking, physical analysis scale, or site approval is created by this document.

## 1. What the preview figures do — and do not — show

The six screening figures are useful for source-file inspection and geographic context:

- Each elevation preview shows the complete downloaded 1° source tile, not a defined study ROI.
- The displayed color stretch is calculated independently for each tile (2nd–98th percentile). The same color in two different figures does not mean the same elevation.
- The histograms and quantiles describe each full source tile. Tile dimensions, land/ice/ocean composition, native angular spacing and elevation distributions differ.
- The previews are downsampled with nearest-neighbour sampling for display. They are not analysis rasters.
- The star is a provisional landmark coordinate from the source manifest. It is not a candidate boundary or an AOI center approved by the team.

Visual inspection can detect coverage and landmark issues, but cannot establish Earth–Moon/Mars similarity or choose final AOI dimensions.

## 2. Provisional landmark checks

Distances below are approximate WGS84 geodesic distances calculated between the current manifest coordinate and the cited reference coordinate. They are location cross-checks, not AOI radii.

| Candidate | Current manifest marker | Independent reference | Review finding |
|---|---|---|---|
| Haughton | 75.366667°N, 89.683333°W | Impact Earth: 75°22′39″N, 89°39′13″W | About 1.47 km apart. Both refer to the Haughton impact-crater locality. The database describes a 23 km apparent crater diameter and exposed polar-desert setting. Use a mapped crater/landform boundary for any subarea; do not use the full source tile. |
| McMurdo | 77.500000°S, 162.000000°E | USAP 2026–2027 planning summary: Lake Hoare/Taylor Valley camps at 77°38.000′S, 162°52.000′E | About 25.6 km apart. The current marker sits effectively on the western edge of the downloaded 162°–163°E tile and does not identify a specific valley segment. Lake Hoare's published reference point is inside the existing tile and is a better named Taylor Valley anchor if the team chooses Taylor Valley. It is not automatically the correct AOI. |
| Askja | 65.033°N, 16.783°W | Smithsonian Global Volcanism Program: 65.033°N, 16.783°W | Exact match at the precision reported. The marker is close to the southern edge of the 1° tile, but it is a recognized volcano reference point. Askja contains overlapping calderas; a final AOI should identify the specific caldera, crater, lava field or other landform rather than treating the complete volcano or tile as one region. |
| Mauna Kea | 19.82°N, 155.47°W | USGS: 19.82°N, 155.47°W | Exact match at the precision reported. The preview shows the large summit/flank elevation structure. The final AOI still needs a chosen geomorphic unit (for example, summit cone field or a specified flank sector) and suitable land-only boundary. |
| Yungay | 24.09°S, 69.93°W | Published hyper-arid-core study site: 24°03′49.6″S, 69°52′49.8″W | About 5.81 km apart. Both points lie in the downloaded tile, but the manifest marker is not the exact published field-site coordinate. Confirm whether the intended analogue is that specific Yungay field site, another part of the Aguas Blancas basin, or a broader hyper-arid terrain unit. |

## 3. Recommended site-specific follow-up

### Haughton — impact crater / polar desert
- Retain as a strong candidate for further investigation, not yet an approved AOI.
- Obtain or digitize a defensible crater boundary from an authoritative geologic/impact map.
- Distinguish rim, ejecta, crater floor and surrounding polar terrain: these are different analogue environments and should not be combined without a reason.
- Assess ArcticDEM v4.1 plus its count/MAD/date/mask companions against the local Copernicus DSM. ArcticDEM is catalog-confirmed for the area, but its high-resolution raster and quality companions were not downloaded in the current handover.

### McMurdo — cold, hyper-arid polar valleys
- Do not use the current generic marker at 162.000°E as the AOI center without further review.
- Ask the team whether the intended landform is Taylor Valley, Wright Valley, Victoria Valley, or another named valley.
- If Taylor Valley is chosen, use the USAP Lake Hoare reference only as a search anchor; delineate a scientific ROI from a suitable map/landform and check whether the REMA mosaic tile(s) plus quality companions cover it.
- The 2 m REMA catalog items are documented as available, but the corresponding raster and quality assets are not downloaded.

### Askja — volcanic / caldera terrain
- The manifest coordinate agrees with the Smithsonian volcano reference.
- Define which of the overlapping caldera structures or adjacent lava terrains is the subject. The caldera is not interchangeable with the surrounding Dyngjufjöll massif.
- Review local topographic and geological mapping before drafting a polygon. The current Copernicus tile is a DSM and does not itself supply lithology/mineralogy.

### Mauna Kea — volcanic summit and flank terrains
- The manifest coordinate agrees with USGS' summit coordinate.
- Decide whether the research question concerns cinder cones, lava-flow surfaces, glacially modified terrain, or a selected flank environment.
- The downloaded Copernicus GLO-30 DSM and the separate USGS 3DEP 1 m bare-earth alternative have different surface types and vertical references (EGM2008 versus NAVD88). Do not combine or compare raw elevations until a documented transformation and product-purpose decision is made.

### Yungay — hyper-arid core / desert processes
- Confirm whether the intended field site is the published Yungay hyper-arid-core locality at 24°03′49.6″S, 69°52′49.8″W.
- If yes, update the candidate reference point only after team/GIS confirmation, then delineate a local terrain unit using field-site and geomorphic evidence.
- The published work describes the site in the Aguas Blancas basin, within the hyper-arid core of the Atacama. This makes Yungay potentially valuable for aridity, soil, dust and biological-extreme-environment context; DEM morphology alone cannot characterize those dimensions.
- The current Copernicus tile shows a broad elevation gradient toward the Andes. A tile-wide histogram is not a measurement of the field-site terrain.

## 4. Cross-site cautions

1. The five products are Copernicus GLO-30 digital surface model tiles. They are a consistent first source family, but they are not necessarily bare-earth terrain and do not include the Copernicus quality companions in the current downloads.
2. The native angular grid differs by tile and latitude. Similar nominal product labels do not establish identical ground sampling or effective resolution.
3. Whole-tile elevation distributions are dominated by broad geography and tile composition. Do not rank sites by these histograms or compare their color scales.
4. A point coordinate is only a landmark/search seed. A study ROI needs a justified polygon and a scientific question.
5. Candidate sites may be analogues along different dimensions. Haughton may be useful for impact/polar-desert processes; Taylor Valley for cold dry-valley operations; Askja and Mauna Kea for volcanic landforms; Yungay for hyper-arid desert conditions. Those are research hypotheses, not scores or validated analog claims.
6. None of these Earth sites reproduces lunar vacuum/gravity/radiation or the Martian atmospheric environment. A useful analogy must state both matches and mismatches.

## 5. Decisions required before any clipping or fingerprint run

| Decision | Required team/GIS record |
|---|---|
| Which Earth candidates to carry forward | Explicit keep/defer decision for each site, with the mission/science question |
| Named target landform per candidate | Crater rim/floor, valley segment, caldera unit, volcano flank, hyper-arid field unit, etc. |
| AOI boundary | Polygon GeoJSON with stable site_id, source/map citation, author/reviewer and rationale |
| Target AOI | Confirm the exact LOLA Site04 sub-area and retain counts/uncertainty layers alongside it |
| Common scale and preparation | Approved physical analysis scale, projection, resampling/reprojection method, window sizes and source-combination policy |
| Source quality | Decide which quality companions and uncertainty/support measures are required and how they affect interpretation |
| Surface-type comparability | Explicitly assess DSM versus DTM/bare-earth differences and vertical-reference treatment |

Until these decisions are recorded, do not run terrain fingerprint extraction on the complete 1° Earth tiles or on the complete 16 km × 16 km LOLA raster as if either were a selected candidate ROI.

## 6. References

- Impact Earth, Haughton impact crater record: https://impact.uwo.ca/impact-craters/map/?crater_id=59
- US Antarctic Program, 2026–2027 Science Planning Summary, Taylor Valley Camps / Lake Hoare: https://www.usap.gov/sciencesupport/scienceplanningsummaries/2026_2027/fieldcamps.cfm
- Antarctic Treaty Secretariat, Taylor Valley visitor site guidelines: https://www.ats.aq/devAS/e/Ats/Guideline/d17178ba-8e2b-4fa5-9528-6b8807dc0eb4
- Smithsonian Global Volcanism Program, Askja: https://volcano.si.edu/volcano.cfm?vn=373060
- USGS, Mauna Kea: https://www.usgs.gov/volcanoes/mauna-kea/
- Published Yungay/Aguas Blancas hyper-arid-core study: https://pmc.ncbi.nlm.nih.gov/articles/PMC8859261/

**Status after this review:** Five source tiles remain available and integrity-checked. Candidate landmark references are clearer, but no final AOIs, analysis grid, real fingerprints, rankings, or planetary-analogue conclusions have been produced.
