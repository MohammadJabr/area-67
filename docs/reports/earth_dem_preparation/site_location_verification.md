# Site location verification

**Status:** coordinates remain provisional. The manifest records rounded reference points but does not include a source citation or uncertainty field for them. A named feature centroid, field station, and final study area are different things; this report verifies landmarks and flags unresolved site identity.

| Site | Manifest coordinate (lat, lon) and origin | Independent evidence | Coordinate confidence and decision |
|---|---|---|---|
| Haughton | 75.366667, -89.683333; carried in the Copernicus manifest/screening setup, source not recorded there | Western University's Impact Earth crater record gives 75°22′39″N, 89°39′13″W and a ~23 km apparent diameter. That reference is about 1.47 km from the manifest point. | Both are inside the local Copernicus tile and the ArcticDEM item. Ask the team whether the landmark center, Haughton-Mars Project location, or another crater sector is intended. |
| McMurdo | -77.500000, 162.000000; origin/selection rationale is not recorded in the manifest; it is a regional reference, not a named valley | Antarctic Treaty material places the Dry Valleys broadly near 77°S, 162°E. Australian Antarctic Gazetteer reference coordinates: Wright Valley 77°31′S, 161°50′E; Victoria Valley 77°23′S, 162°00′E; Taylor Valley 77°37′S, 163°00′E. Approximate geodesic distances from the manifest point are 4.4, 13.0, and 27.4 km, respectively. | The local Copernicus point is ~10 m from its west edge, but none of these three valley reference points is in that local tile. REMA item `18_35_1_1_2m_v2.0` covers the Wright reference; `17_35_2_1_2m_v2.0` covers the Victoria reference; neither specified item covers the Taylor reference. The team must name the valley/sector. |
| Askja | 65.033, -16.783; copied to the manifest as the Askja landmark | Smithsonian Global Volcanism Program publishes Askja at 65.033°N, 16.783°W and describes the central volcano/caldera complex. The manifest coordinate matches at its stated precision. | Suitable as a volcano reference, not as an AOI center with a known boundary. Askja caldera, Víti/Öskjuvatn, and another volcanic feature remain candidate concepts. |
| Mauna Kea | 19.820, -155.470; rounded volcano/summit reference in the manifest | USGS Hawaiian Volcano Observatory lists Mauna Kea at 19.82°N, 155.47°W. | Landmark identity is consistent. The 1 m 3DEP tiles cover the coordinate and overlap, but the exact summit/upper-flank terrain unit and required extent remain a team decision. |
| Yungay | -24.090, -69.930; provisional Yungay/Atacama reference copied into the manifest | A published Atacama study reports a Yungay research location at 24°05′24″S, 69°55′48″W, which converts to the manifest values. Other published Yungay sampling areas differ by several kilometres. The investigated ALOS Atacama raster footprint does not reach this latitude. | The point is credible for the broad Yungay research locality, but no AREA 67 record ties the coordinate to one field plot or station. Confirm the intended location before treating point coverage or ALOS noncoverage as final. |

## Coverage margins and raster availability

Margins below are distances from the provisional manifest point to the nearest edge of each local tile. They are geometry checks, not recommendations for AOI size.

| Site/local raster | Point/nearest-edge evidence | Result |
|---|---|---|
| Haughton Copernicus GLO-30 | Point inside; nearest edge ~8.95 km west | Local DSM available. Official crater center differs from manifest point by ~1.47 km; both references remain covered. |
| McMurdo Copernicus GLO-30 | Point inside; ~10.1 m from west edge | The point is not a valley selection. Wright, Victoria, and Taylor reference points are outside this local tile. |
| Askja Copernicus GLO-30 | Point inside; nearest edge ~3.66 km south | Local DSM available; exact caldera coverage depends on the team-defined feature boundary. ÍslandsDEM 10 m national mosaic was window-read remotely, not downloaded. |
| Mauna Kea Copernicus GLO-30 | Point inside; nearest edge ~19.94 km north | Local DSM available. |
| Mauna Kea USGS 3DEP x86y220 | Point inside; ~149.7 m from east edge | Locally downloaded and QA-inspected; EPSG:26904. |
| Mauna Kea USGS 3DEP x24y220 | Point inside; ~1.28 km from west edge | Neighbor locally downloaded and QA-inspected; EPSG:26905. The transformed tile footprints overlap by about 13.35 km² using their densified bounding footprints. This supports geographic coverage continuity around the point, not grid alignment or a ready mosaic. |
| Yungay Copernicus GLO-30 | Point inside; nearest edge ~7.13 km north | Local DSM covers the provisional point. SRTMGL1 catalog granule also covers it; not downloaded. Regional Atacama ALOS extent ends about 0.895° south of the point. |

No ArcticDEM, REMA, or ÍslandsDEM source raster was saved locally. Their remote COG window reads are display/screening evidence in [targeted access QA](../../../data/metadata/earth_dem_qa/remote/targeted_cog_access_2026-11-15.json). No new fingerprints, similarity results, final AOI boundaries, or scale assumptions were made.

## Candidate features (not approved)

- Haughton: crater rim/floor sectors or a selected crater-fill feature.
- McMurdo: a chosen sector of Wright, Victoria, Taylor, or another named Dry Valley. The map in `figures/mcmurdo_named_valleys_rema_coverage.png` shows these as unresolved alternatives.
- Askja: caldera, inner lake/caldera margins, or another named volcanic landform.
- Mauna Kea: summit complex or an upper-flank sector. Adjacent tiles provide provisional-point continuity.
- Yungay: the confirmed AREA 67 field station/plot, once supplied; published Yungay field sites are not interchangeable.

## Sources

- [Impact Earth Haughton record](https://impact.uwo.ca/impact-craters/map/?crater_id=59)
- [Antarctic Treaty visitor/site guidance for Taylor Valley](https://www.ats.aq/devAS/e/Ats/Guideline/d17178ba-8e2b-4fa5-9528-6b8807dc0eb4), [SCAR/Australian Antarctic Gazetteer: Wright Valley](https://data.aad.gov.au/aadc/gaz/display_name.cfm?gaz_id=133876), [Victoria Valley](https://data.aad.gov.au/aadc/gaz/display_name.cfm?gaz_id=114653), [Taylor Valley](https://data.aad.gov.au/aadc/gaz/display_name.cfm?gaz_id=132512)
- [Smithsonian Global Volcanism Program: Askja](https://volcano.si.edu/volcano.cfm?vn=373060)
- [USGS Hawaiian Volcano Observatory: Mauna Kea](https://www.usgs.gov/volcanoes/mauna-kea)
- [Yungay study location and coordinates](https://www.sciencedirect.com/science/article/pii/S2213343726014053); compare with [distinct Yungay Valley study plots](https://bg.copernicus.org/articles/21/5305/2024/bg-21-5305-2024.html)
