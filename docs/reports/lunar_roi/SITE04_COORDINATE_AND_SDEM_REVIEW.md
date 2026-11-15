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

This coarse regional bounding box includes the inverse-transformed local provider ROI centroids and the peer-reviewed SP-4 coordinate. It does not, by itself, prove exact raster-mask coverage for every point or every layer.

### Screened small derivative: not the Site04/SP-4 tile

A third-party Hugging Face dataset, “Connecting Ridge 5 m: Lunar South Pole Terrain & Ice-Prospectivity” (Terranova Robotics, 2026), describes a 3 km × 3 km, 5 m/pixel tile centered at 89.439°S, 222.856°E (the Site001 / Connecting Ridge vicinity). Its published South Polar Stereographic georeferencing places that tile center approximately 10.90 km from the SP-4 point; the 3 km square therefore does not overlap SP-4.

This third-party tile should not be treated as the Site04/SP-4 SDEM subset. It is centered on the Connecting Ridge/Site001 vicinity, about 10.90 km from the SP-4 point in the local projection; its 3 km square does not overlap SP-4. It may be useful as an example of a small derived terrain bundle or pipeline reference, but not as elevation coverage for this Site04 target. Its derived layers and model outputs have the limitations stated in its dataset card and are not substitutes for the NASA source rasters.

This is a screening result from the dataset card's published center and grid description, not inspection of the files themselves. Source: https://huggingface.co/datasets/terranova-robotics/connecting-ridge-5m.

### Suitability and limitations

This is a promising alternate/companion lunar terrain source for the Site04 ROI cluster because the local ROI coordinates lie within the Connecting Ridge region bounds. It is not yet approved as a replacement for Site04 LDEM.

Before use, verify locally:
1. The exact raster footprints and valid masks of SDEM, uncertainty/resolution, slope and image/solar coverage layers.
2. The SDEM CRS, Moon body/reference frame, pixel spacing, affine transform, NoData semantics and vertical relationship to the existing Site04 LOLA products.
3. Whether the provider ROI cluster and the selected Artemis SP-4 research point are actually covered by valid SDEM/ancillary pixels.
4. Which areas have adequate multi-illumination/image support and which remain constrained by shadows or sparse image input.
5. Product citation and license/usage terms before redistribution.

The archive should not be downloaded in full until the team agrees that a targeted SDEM validation is worth the approximately 2.2 GB compressed regional download. The file-level preview is available, but this review did not download or inspect the GeoTIFF raster data.

## 5. Recommended next steps

1. Retain the existing four provider ROI polygons and their feature attributes as source evidence. Do not alter them or write repaired alternatives over the source.
2. Record both published coordinate definitions with their labels and citations. Ask the GIS owner to reconcile whether the team is targeting the PGDA R04 region center, Artemis site 004 / SP-4, or a broader Shackleton-Rim/Connecting-Ridge terrain unit.
3. Use the four local ROI polygons as a cluster reference, not as the only possible study-area boundary.
4. Validate the Connecting Ridge SDEM file-level footprint and ancillary masks before any large download or switch of the lunar DEM source.
5. Keep the 1.2 km, 1.5 km and 2.0 km Site04 windows labelled as ROI-cluster sensitivity windows, not approved study AOIs.
6. Do not launch real terrain fingerprint extraction until the lunar target AOI, Earth candidate AOIs, common physical analysis scale, relief window, local-relief neighborhood support and vertical-reference policy are reviewed.

## 6. Sources

- NASA GSFC PGDA Product 78, High-Resolution LOLA Topography for Lunar South Pole Sites: https://pgda.gsfc.nasa.gov/products/78
- NASA GSFC, Lunar Surface Data Book, ACD-50044 Rev A (2023), Appendix A, Table A2-2: https://ntrs.nasa.gov/api/citations/20230007818/downloads/ACD-50044%20Lunar%20Surface%20Data%20Book%20Rev%20A.pdf
- Patterson et al. (2024), “Lithologies and Chronologic Opportunities of Materials to Be Returned From the Artemis Exploration Zone,” section 1.2.2: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023JE008275
- NASA GSFC PGDA Product 104, Enhanced Topography Models for Selected Lunar South Pole Regions with Shape-from-Shading: https://pgda.gsfc.nasa.gov/products/104
- Bertone et al. (2025), archived SDEM geospatial products, Zenodo record 17954508: https://zenodo.org/records/17954508

**No new raster or vector data was downloaded, modified, repaired, reprojected or resampled for this note.**
