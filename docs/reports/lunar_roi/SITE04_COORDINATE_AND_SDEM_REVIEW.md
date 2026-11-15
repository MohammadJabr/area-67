# Site04 Coordinate Reference and Connecting Ridge SDEM Review

**Review date:** 2026-11-15  
**Status:** Coordinate-definition conflict documented; no coordinate or AOI has been approved by this note.

## Executive finding

Do not use the NASA Lunar Surface Data Book R04/Site04 coordinate as an unquestioned center for the four locally inspected Site04 provider ROIs.

Two published coordinate definitions appear in the available sources:

1. NASA's 2023 Lunar Surface Data Book lists **R04 or Site04 — Shackleton Rim** at 89.7668°S, 171.87°W.
2. A 2024 peer-reviewed Artemis exploration paper lists potential Artemis landing site **004 / SP-4** at 89.78°S, 204.27°E (155.73°W) and describes it as being along the margin of the Connecting Ridge Artemis candidate region on a portion of Shackleton crater rim.

When transformed using the local shapefile's spherical polar stereographic CRS, these coordinates are separated by about 1.64 km in the relevant direction from the current provider-ROI cluster. The 2024 SP-4 point is much closer to the locally inventoried ROI cluster. The source labels are similar but not proven to describe exactly the same spatial reference object; retain the discrepancy and do not silently choose one coordinate.

## 1. Local provider ROI geometry

The four source ROI features in `Site04_ROIs.shp` have the following original geometry centroids and bounds (projected X/Y metres, from the user's local inspection):

| Feature | Source X | Source Y | Centroid X | Centroid Y | Source validity |
|---|---:|---:|---:|---:|---|
| 0 | -2812.5 | -6647.5 | -2810.60 | -6645.52 | Invalid: ring self-intersection |
| 1 | -2757.5 | -6342.5 | -2755.22 | -6340.23 | Invalid: ring self-intersection |
| 2 | -2677.5 | -6107.5 | -2678.78 | -6108.27 | Valid |
| 3 | -2657.5 | -5957.5 | -2656.29 | -5955.49 | Valid |

Combined source bounds:

- X: [-2842.5, -2627.5] m
- Y: [-6802.5, -5902.5] m

The combined provider-ROI bounding-box center is (-2735.0, -6352.5) m.

Inverse-transforming the four rounded local geometry centroids through the shapefile's custom spherical polar stereographic CRS gives approximate longitudes/latitudes:

| Feature centroid | Longitude (°) | Latitude (°) |
|---|---:|---:|
| 0 | -157.0750 | -89.7621 |
| 1 | -156.5121 | -89.7720 |
| 2 | -156.3202 | -89.7800 |
| 3 | -155.9620 | -89.7850 |

These inverse-transformed values are a local consistency check. They do not replace a source-authoritative coordinate definition, and they inherit the CRS/axis assumptions recorded in the original shapefile WKT.

## 2. Published coordinate definitions requiring reconciliation

### NASA Lunar Surface Data Book (2023)

Appendix A, Table A2-2 lists:

- Shorthand: R04 or Site04
- Name: Shackleton Rim
- Latitude: -89.7668°
- Longitude: -171.87°

The same paragraph says that the coordinates in the table were generated from DEM files on the PGDA website and that center points of the original polygons are accurate to 5–10 m.

Applying the local shapefile CRS to (-171.87°, -89.7668°) gives approximately:

- X = -1000.04 m
- Y = -7000.35 m

This point lies outside the bounding box of the four local provider ROI features. Its distance to the nearest edge of that combined bounding box is approximately 1,639.45 m.

### Peer-reviewed Artemis exploration paper (2024)

Patterson et al. (2024), section 1.2.2, describes potential Artemis landing site 004 as:
- Site SP-4 in Mazarico et al. (2011): (-89.78°, 204.27°)
- Point A in Bussey et al. (2010): (89.68°S, 166.0°W)

The paper states that potential site 004 is along the margin of the Artemis III candidate landing region named Connecting Ridge, on a portion of Shackleton crater rim.

Converting 204.27°E to -155.73° longitude and projecting with the local shapefile CRS gives approximately:

- X = -2742.09 m
- Y = -6081.54 m

This point is within the combined provider-ROI bounding rectangle and close to the feature-centroid cluster. It is not inside every provider polygon, and this proximity does not establish that it is the exact center or identifier of the shapefile's four features.

A follow-up point-to-feature check against the four original shapefile geometries reported the following distances for SP-4:

| Feature | Original geometry validity | SP-4 inside feature? | Reported distance |
|---|---|---:|---:|
| 0 | Invalid: ring self-intersection | No | 445.08 m |
| 1 | Invalid: ring self-intersection | No | 181.55 m |
| 2 | Valid | No | **49.27 m** |
| 3 | Valid | No | **99.10 m** |

For the Data Book R04 point, the same check returned 1,814.41 m to Feature 0, 1,842.38 m to Feature 1, 1,875.06 m to valid Feature 2 and 1,921.88 m to valid Feature 3; it was not contained by any feature.

The distances to valid Features 2 and 3 provide the more reliable geometric comparison. Distances reported for self-intersecting Features 0 and 1 are diagnostic only: invalid polygon topology can make geometric operations less dependable. Neither published point is covered by any of the four original provider ROI polygons. In particular, SP-4 is a nearby reference point, not a point proven to lie within the provider's ROI footprint.

### Numbering lineage and disposition

NASA PGDA Product 78 explicitly states that the Site01/Site04/Site07/Site11 numbering follows Mazarico et al. (2011). The same product identifies Site04 as Shackleton Rim and provides the exact Site04 ROI archive used in this project.

Patterson et al. (2024), section 1.2.2, explicitly identifies potential Artemis landing site 004 as Mazarico et al. (2011) site SP-4 at (-89.78°, 204.27°E). The local provider ROI cluster projects close to that SP-4 point: the point is 49.27 m from valid Feature 2 and 99.10 m from valid Feature 3, although it is not contained by any of the four original features.

This published numbering lineage supports treating the local Site04 ROI cluster as the **Mazarico Site 4 / Artemis Site 004 (SP-4) area**. It is stronger evidence than proximity alone.

The NASA Lunar Surface Data Book nevertheless labels (-89.7668°, -171.87°) as “R04 or Site04 — Shackleton Rim.” That point is about 1.97 km from the SP-4 point in the local projected CRS and is 1,875.06 m and 1,921.88 m from valid provider Features 2 and 3 respectively. The available sources do not explain why this separately published coordinate differs from the Mazarico/SP-4 reference. It could represent a different center/reference point within the broader Shackleton-Rim site or a source-definition inconsistency; do not silently substitute it for the SP-4 coordinate or erase it from provenance.

Keep both records in the manifest with their exact source labels and longitude conventions. For work specifically using the locally inspected Site04 ROI cluster, identify the target provisionally as the Mazarico Site 4 / Artemis Site 004 (SP-4) vicinity, pending team/GIS-owner approval of the study AOI.

### Original provider ROI archive and `.prj` evidence

The team-local acquisition record for the official `Site04_ROIs.tgz` archive records:

- Source: `https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site04/Site04_ROIs.tgz`
- Downloaded size: **1,712 bytes**
- SHA-256: `8e8b788f9fdf6400f23fd36dad02138102bd1a905b4b71a5739a9a4fd8a0e07a`
- Archive member count: **5**

The preserved acquisition record contains the member count but not the member-name listing. The extracted `Site04_ROIs.prj` WKT recorded in the local CRS inspection declares a spherical ellipsoid with radius **1,737,400 m**, a datum named **`unknown`**, a prime meridian named **`Reference meridian`** at 0°, and a south-polar stereographic projection with latitude of origin -90°, central meridian 0°, false offsets 0 m, and metre units.

The Site04 GeoTIFF WKT has the same nominal sphere and polar-stereographic parameters and also labels its datum `unknown`; it labels the zero-degree prime meridian `Greenwich`. This supports a comparison in the same *nominal projection plane* for the local shapefile and local raster. It does **not** identify the body-fixed frame as ME or PA.

This distinction is explicit in NASA PGDA Product 78: its MOON_ME / DE421 CRS statement applies to the GeoTIFF products, **excluding the ROI shapefiles**. Therefore, the catalog's GeoTIFF frame description cannot be inherited by the shapefile. The archive checksum and member count establish which archive was acquired, but they do not supply a frame definition. No source-authoritative ME/PA assignment for the legacy ROI shapefile has been found in the evidence reviewed here.

**Disposition:** keep the Site04 shapefile frame as unknown. Do not relabel it MOON_ME, MOON_PA, or Moon (2015), and do not apply a frame shift to force alignment. The local shapefile-to-local-Site04-raster ROI statistics remain useful as a nominal same-product coordinate comparison; comparisons against external lunar products remain conditional until the shapefile's frame provenance is confirmed.

## 3. Exploratory window result remains scoped to the ROI cluster

The previously tested 1.2 km, 1.5 km and 2.0 km windows were centered on the combined provider-ROI bounds at (-2735.0, -6352.5) m.

All three contain the four provider ROI bounds and have 100% valid coverage in all five local Site04 raster layers. The 1.2 km square is the smallest of those three tested windows that encloses all four provider ROIs.

The 1.2 km square bounds are X=[-3335, -2135] m and Y=[-6950, -5750] m. The Mazarico Site 4 / Artemis Site 004 (SP-4) point at (-2742.09, -6081.54) m also falls inside this 1.2 km square, with a minimum clearance of 331.54 m to the window edge. The 1.5 km and 2.0 km windows contain it as well. Thus, for the provisional SP-4 vicinity interpretation, the 1.2 km window covers both the local ROI cluster and the published SP-4 point; this is a useful exploratory footprint result, not AOI approval.

These windows were **not** designed to contain the Data Book R04 point at (-1000.04, -7000.35) m. Therefore:
- the 1.2 km result remains a valid compact-window comparison for the four-feature provider-ROI cluster;
- it must not be described as covering the Data Book R04 coordinate;
- the coordinate difference must be resolved before calling any window the complete Site04 study area.

## 4. Candidate higher-detail source: NASA Shape-from-Shading Connecting Ridge SDEM

NASA PGDA Product 104, “Enhanced Topography Models for selected Lunar South Pole regions with Shape-from-Shading,” publishes 5 m/pixel SDEMs for 13 original Artemis III Candidate Landing Regions. The products use LROC NAC imagery to add terrain detail to LOLA-based 5 m/pixel DEMs in illuminated areas while retaining consistency with LOLA geodetic reference.

The associated Zenodo archive is version 1.0.0, published 2025-12-16. It lists a regional file:

- `A3CLR22_6_Connecting_Ridge.zip`
- Compressed archive size listed by Zenodo: approximately 2.2 GB
- MD5 listed by Zenodo: `0ad982cf42319a300f2a2cff69d39322`

The archive preview lists among its products:
- `A306_GLDELEV_005.tif` (SDEM elevation);
- `A306_GLDHILL_005_315_45.tif` (hillshade);
- `A306_GLDMASK_005.tif` (mask/coverage);
- `A306_GLDOMOS_005.tif` (maximum-illumination orthomosaic);
- `A306_GLDSBCT_005.tif` and `A306_GLDSBCTALL_005.tif` (solar-bin/image count products);
- `A306_GLDSIGM_005.tif` (uncertainty-related ancillary layer);
- `A306_GLDBRES_005.tif` (best-input-resolution product);
- `A306_GLDDIFF_005.tif` (SDEM-LDEM difference product).

The Zenodo README gives the Connecting Ridge regional bounding box in longitude/latitude as:

- Min longitude: -171.469234°
- Min latitude: -89.835111°
- Max longitude: -101.888658°
- Max latitude: -89.090284°

The archive's own README also defines the A306 region footprint in projected coordinates as a rectangle with X from -19,000 m to -3,000 m and Y from -20,000 m to -4,000 m. The extracted 5 m elevation GeoTIFF confirms those bounds exactly. This projected footprint is the decisive screening geometry; the broader longitude/latitude bounding box is not an adequate substitute for testing the actual projected footprint.

### Screened small derivative: not the Site04/SP-4 tile

A third-party Hugging Face dataset, “Connecting Ridge 5 m: Lunar South Pole Terrain & Ice-Prospectivity” (Terranova Robotics, 2026), describes a 3 km × 3 km, 5 m/pixel tile centered at 89.439°S, 222.856°E (the Site001 / Connecting Ridge vicinity). Its published South Polar Stereographic georeferencing places that tile center approximately 10.90 km from the SP-4 point; the 3 km square therefore does not overlap SP-4. It should not be used as the Site04/SP-4 elevation source.

This is a screening result from the dataset card's published center and grid description, not inspection of the files themselves. Source: https://huggingface.co/datasets/terranova-robotics/connecting-ridge-5m.

### Suitability and limitations

### Result of the local A306 / Connecting Ridge header audit

The selectively extracted files were CRC32-verified, and the read-only GeoTIFF metadata audit reported:

| Layer | Dimensions | Pixel size | Bounds (Xmin, Ymin, Xmax, Ymax) | NoData |
|---|---:|---:|---|---:|
| GLDELEV | 3200 × 3200 | 5 m | [-19000, -20000, -3000, -4000] | -3.4028235e38 |
| GLDMASK | 1066 × 1066 | 15 m | [-19000, -19990, -3010, -4000] | None |
| GLDBRES | 1066 × 1066 | 15 m | [-19000, -19990, -3010, -4000] | None |
| GLDSBCT | 1066 × 1066 | 15 m | [-19000, -19990, -3010, -4000] | None |
| GLDSBCTALL | 1066 × 1066 | about 15.0094 m | [-19000, -20000, -3000, -4000] | 0 |

All five GeoTIFFs declare the same Moon (2015) spherical South Polar Stereographic CRS (radius 1,737,400 m; longitude of origin 0°; latitude of origin -90°). The elevation product is 5 m/pixel, while the mask and most coverage companions are 15 m/pixel. Therefore the earlier `GRID DIFFERS` output is expected: it means the companions are not cell-for-cell on the elevation grid, not that their CRS necessarily differs. The mask README meaning is a count of illuminated LROC image pixels contributing to the SfS solution; the mask has no declared NoData value. GLDSBCT is described as solar bins per pixel.

### Critical projected-footprint screening result

The local Site04 ROI shapefile and SP-4 coordinates were previously calculated in the custom lunar polar stereographic plane with the same nominal sphere radius and polar-stereographic parameters. Under direct comparison in that projected plane:

- A306 SDEM elevation maximum X is **-3,000 m**.
- Local Site04 provider ROI X bounds are **-2,842.5 to -2,627.5 m**. All four features lie east of the A306 footprint boundary, with the nearest part of their combined bounding box 157.5 m beyond it.
- The published Mazarico Site 4 / Artemis Site 004 (SP-4) point is at X=-2,742.09 m, **257.91 m east** of the A306 elevation footprint boundary.
- The previous 1.2 km ROI-cluster window spans X=[-3,335,-2,135] m. It overlaps the A306 rectangular extent only in the 335 m strip from X=-3,335 to -3,000 m; it does not contain SP-4 or any part of the provider ROI bounding box.

**Operational conclusion:** A306 / Connecting Ridge is not currently demonstrated to cover the Site04/SP-4 ROI cluster. In the shared projected coordinate plane, its raster bounds exclude the provider ROIs and SP-4. Do not sample its pixels at those locations, resample it into Site04, or call it a Site04 SDEM source.

There is one remaining coordinate-reference caveat: the SDEM GeoTIFFs explicitly identify the Moon (2015) datum/IAU CRS, while the legacy Site04 shapefile WKT names its datum/spheroid as `unknown` (although its nominal sphere radius and projection parameters match). The direct projected-coordinate comparison is therefore the correct screening result under the apparent common map plane, but a definitive physical co-registration claim requires the shapefile's original source/reference-frame provenance to be confirmed. The fact that Product 104 SDEMs are geodetically consistent with their LOLA reference is relevant, but it does not by itself prove the legacy shapefile WKT's datum identity.

### Reference-frame interpretation: do not apply a generic ME/PA offset

The coordinate-frame distinction must be handled with source-specific provenance:

- NASA PGDA Product 78 states that its Site04 LDEM and other 5 m GeoTIFF layers use the **MOON_ME reference frame of JPL ephemeris DE421**. It explicitly excludes the ROI shapefiles from that GeoTIFF CRS statement, so the local shapefile's missing datum label remains a genuine provenance gap.
- The SDEM paper states that the LOLA-based LDEM is its geodetic reference, that the SDEM is registered to that LDEM, and that the released GeoTIFF products use the **Moon (2015) South Polar Stereographic** projection. This is evidence of a LOLA geodetic tie for the SDEM, but the raster WKT alone does not document every upstream frame/registration operation.
- NASA's 2024 Lunar Reference Frames white paper explains that Mean Earth (ME) and Principal Axis (PA) are distinct body-fixed frames and equivalent surface positions may differ by up to about 875 m. It also states that ME is commonly used for lunar surface mapping and that Artemis uses ME for site selection and surface analyses.

**Do not add or apply the generic 875 m ME/PA displacement simply because the A306 WKT says “Moon (2015).”** First establish whether a particular input is actually PA or ME. The SDEM paper's LOLA geodetic tie argues against treating A306 as an arbitrary PA-only dataset. The remaining uncertainty in this review is specifically the frame provenance of the legacy Site04 ROI shapefile and whether its coordinate values are directly co-registered with the Site04 LDEM.

Until the original ROI archive/source metadata resolves that point, retain the A306 projected-bounds comparison as a strong screening result under the apparent common map plane, not as a final survey-grade registration proof. Do not apply a frame rotation to make the geometries overlap; that would be an unsupported correction.


### Additional official region README screening: A305 and A308

The team selectively extracted only the README from each additional Zenodo archive using HTTP Range requests; both files passed CRC32 verification. No raster companions were downloaded from these two archives.

| Product | Artemis region | Published projected bounds (Xmin, Ymin, Xmax, Ymax), m | SP-4 comparison in nominal polar plane |
|---|---|---|---|
| A305 | Connecting Ridge Extension | [-38,700, -16,100, -18,700, 3,900] | SP-4 is about 15.96 km east of the nearest rectangle edge |
| A306 | Connecting Ridge | [-19,000, -20,000, -3,000, -4,000] | SP-4 is 257.91 m east of the elevation rectangle edge |
| A308 | Peak Near Shackleton | [22,000, -28,000, 38,000, -12,000] | SP-4 is about 25.44 km from the nearest rectangle corner |

A305 and A308 therefore do not provide plausible raster coverage for the local Site04/SP-4 point under the nominal shared polar-stereographic plane. A306 remains the only one of these three inspected products that is spatially close to the provider ROI cluster, but its published elevation footprint stops 257.91 m short of the SP-4 point and 157.5 m short of the eastern edge of the provider ROI bounding box.

The README-defined ROI rectangles are strong screening evidence, but all cross-product comparisons remain conditional on confirmation that the legacy shapefile is expressed in the same lunar body-fixed reference frame as the SDEM products. Do not apply an assumed ME/PA frame shift or download more raster companions from A305/A308 for this Site04 task.

The Zenodo record also lists A307 Nobile Rim 1, which has not yet been screened locally. Its README can be inspected selectively if a complete 13-region catalog screening is desired; the current A305/A306/A308 evidence already shows that the closest candidate among the three inspected is A306.

The archive README in the local A306 package contains placeholder `doi:XYZ` citation fields. Use the completed official publication citation listed below rather than copying those placeholders. NASA PGDA Product 104 identifies the paper as Bertone et al. (2026), DOI 10.3847/PSJ/ae5b70.

This review used header metadata only. No SDEM pixel arrays were read, and no raster was reprojected, resampled, modified or combined.

## 5. Recommended next steps

1. Retain the existing four provider ROI polygons and their feature attributes as source evidence. Do not alter them or write repaired alternatives over the source.
2. Preserve the published coordinate definitions with their labels and citations. For the local ROI cluster, the Mazarico Site 4 / Artemis Site 004 (SP-4) vicinity is the stronger provisional identity.
3. Keep the 1.2 km, 1.5 km and 2.0 km windows labelled as exploratory ROI-cluster/SP-4 vicinity sensitivity windows, not approved study AOIs.
4. The A305 Connecting Ridge Extension and A308 Peak Near Shackleton README-only screenings are complete. Neither footprint is a plausible Site04/SP-4 raster source in the nominal shared projection plane; do not download their raster companions for this task. A307 is optional only if the team later requests a complete Artemis-region catalogue screen.
5. Keep the Site04 ROI shapefile frame explicitly unknown. Request an authoritative frame/provenance statement from the PGDA product author or obtain the original shapefile-generation metadata before making a definitive cross-product co-registration claim. If additional archive inspection is performed, preserve the full member-name listing alongside the archive checksum.
6. Do not launch real terrain fingerprint extraction until the lunar target AOI, Earth candidate AOIs, common physical analysis scale, relief window, local-relief neighborhood support and vertical-reference policy are reviewed.

## 6. Sources

- NASA GSFC PGDA Product 78, High-Resolution LOLA Topography for Lunar South Pole Sites: https://pgda.gsfc.nasa.gov/products/78
- NASA GSFC, Lunar Surface Data Book, ACD-50044 Rev A (2023), Appendix A, Table A2-2: https://ntrs.nasa.gov/api/citations/20230007818/downloads/ACD-50044%20Lunar%20Surface%20Data%20Book%20Rev%20A.pdf
- Patterson et al. (2024), “Lithologies and Chronologic Opportunities of Materials to Be Returned From the Artemis Exploration Zone,” section 1.2.2: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023JE008275
- NASA GSFC, “Lunar Reference Frames,” 2024 Moon to Mars Architecture Concept Review: https://www.nasa.gov/wp-content/uploads/2024/12/acr24-lunar-reference-frames.pdf
- U.S. Geological Survey, McClernan et al. (2025), “Lunar Grid Systems, Coordinate Systems, and Map Projections for the Artemis Missions and Lunar Surface Navigation,” https://doi.org/10.3133/tm11E1
- NASA GSFC PGDA Product 104, Enhanced Topography Models for Selected Lunar South Pole Regions with Shape-from-Shading: https://pgda.gsfc.nasa.gov/products/104
- Bertone et al. (2026), “Enhanced Topography Models for selected Lunar South Pole regions with Shape-from-Shading,” The Planetary Science Journal, 7, 118, DOI: https://doi.org/10.3847/PSJ/ae5b70
- Bertone et al. (2025), archived SDEM geospatial products, Zenodo record 17954508: https://zenodo.org/records/17954508

The SDEM elevation, mask, best-resolution and solar-bin companion files were selectively extracted from Zenodo using HTTP byte-range requests and CRC32-verified. The audit read their GeoTIFF headers only; no raster pixel arrays were read, and no original source raster/vector was modified, repaired, reprojected, resampled or combined.
