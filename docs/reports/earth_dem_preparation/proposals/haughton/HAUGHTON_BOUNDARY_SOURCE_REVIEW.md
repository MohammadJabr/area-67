# Haughton Central Basin — Geological Boundary Source Review

**Review date:** 2026-11-15  
**Status:** Source located; GIS boundary is not yet digitized or approved. No AOI coordinates or raster products are created by this review.

## Decision

Use the published geological map reproduced as Figure 2 in Patterson & Ernst (2020) as the lead digitization source for the Haughton central-basin / crater-fill investigation. The paper explicitly describes Figure 2 as a digitized product modified after Osinski's 2005 geological map. Its legend distinguishes allochthonous crater-fill impactites, parautochthonous crater-fill impactites, Haughton Formation, fluvial/glacial deposits, bedrock formations, and fault classes.

This is a defensible map source for tracing a provisional geological study polygon. It is **not** evidence that a downloadable georeferenced GIS vector or the authors' original shapefile is publicly available. No raw vector download was verified in this review.

## Source evidence

1. Patterson, C. W. & Ernst, R. E. (2020), *A novel geomatics method for assessing the Haughton impact structure*, Meteoritics & Planetary Science, DOI: https://doi.org/10.1111/maps.13573
   - Full-text article: https://onlinelibrary.wiley.com/doi/full/10.1111/maps.13573
   - Author-hosted PDF: https://carleton.ca/timpatterson/wp-content/uploads/Patterson.2020.Met_.Plan_.Sci_.13573.pdf
   - Figure 2 is on PDF page 4. The caption states that the digitized product is modified after Osinski (2005), and gives the crater-centre reference as 75°22′38″N, 89°40′48″W.
   - The map includes a north arrow and a 0–8 km scale bar, and differentiates definite, approximate and inferred faults.
   - The paper's geomatics analysis identifies the central basin as a broad shallow depression, with a radius of approximately 5.0–6.5 km in its cross-sections. This is a structural interpretation and a scale/context check, not a ready-made AOI polygon.

2. Osinski et al. (2005a), detailed field mapping and geological interpretation. Patterson & Ernst identify Osinski's mapping as the basis for their Figure 2. The reproduced map is the most directly useful accessible map artifact found in this review.

3. Western University Impact Earth, Haughton crater record:
   https://impact.uwo.ca/impact-craters/map/?crater_id=59
   - Independent locality reference: 75°22′39″N, 89°39′13″W.
   - This is a crater reference point, not an AOI boundary.

4. Lunar and Planetary Institute, Haughton geologic map on air-photo mosaic:
   https://www.lpi.usra.edu/publications/slidesets/craters/slide_20.shtml
   - Independent visual geological context. It is not a downloadable georeferenced vector in the material inspected here.

## Geological interpretation to preserve

Do not collapse these into one arbitrary polygon:

- **Central basin structural envelope:** a broad central depression described in Patterson & Ernst as having an approximate 5.0–6.5 km radius in reconstructed cross-sections.
- **Allochthonous crater-fill impactites:** a mapped geological unit shown in Figure 2 (light blue). This is the most defensible initial geological class to trace for a crater-fill-focused study.
- **Parautochthonous crater-fill impactites and Haughton Formation sediments:** separate mapped classes; do not silently merge them with the allochthonous unit.
- **Uplifted target-rock exposures and water/glacial/fluvial deposits:** separate units and potential exclusions/strata, depending on the precise study question.

Recommended provisional GIS layer design:
- `central_basin_structural_context` — reference/context only; do not treat as a final boundary unless separately digitized from defensible structural evidence.
- `allochthonous_crater_fill` — digitized source geology polygon(s), preserving separate multipart components if the map shows them.
- `parautochthonous_crater_fill` — separate polygon class.
- `haughton_formation` — separate polygon class.
- `faults_definite`, `faults_approximate`, `faults_inferred` — separate line classes, retaining source certainty.

The first candidate AOI should be a landform-specific polygon derived from the mapped geological class and checked against the DEM and current surface expression. It must not be a circular buffer around the crater centre.

## Reproducible GIS workflow

1. Obtain the author-hosted PDF above and extract Figure 2 at the highest available raster resolution. Preserve the unmodified PDF and extracted figure, record source URL, retrieval date, page number, and SHA-256.
2. In QGIS Georeferencer, georeference the map image against the local Haughton DEM and/or an independently sourced basemap. Use multiple spatially distributed, unambiguous control points visible in both map and reference data (for example, persistent coastline/shoreline intersections, distinctive drainage junctions, and unmistakable landform features). The crater-centre coordinate and scale bar are useful checks, but a single centre point plus a scale bar is not enough to establish a reliable georeferencing solution.
3. Compare suitable projected target CRSs for the site (including EPSG:3413 and local UTM zone 16N / EPSG:32616); document the selected CRS and its distortion/coverage rationale. Do not assign a CRS by relabelling coordinates.
4. Record every GCP, source of its reference coordinate, transformation type, residual, total RMS, and visual overlay check. Reject a solution with systematic drift or control points concentrated in one part of the map. Do not hide map-source generalization or line-width uncertainty behind a small RMS.
5. Digitize the mapped unit boundaries into a GeoPackage. Preserve map classes and certainty attributes; do not trace the map's central blue region as a generic central-basin polygon without retaining its actual legend class.
6. Validate geometry (validity, multipart components, self-intersections), topology, area, bounds, and overlap with the local DEM. Do not automatically repair the source trace without recording a separate repair candidate and before/after geometry.
7. Export a review GeoJSON with stable IDs, source citation, map page/figure, georeferencing metadata, digitizer, review status, and explicit provisional status. Have the GIS lead visually review the overlay before approval.
8. Only after AOI approval, clip the unchanged source DEM to the approved polygon plus a documented processing margin, project to the selected metric grid, and record all resampling/NoData/mask choices. Keep the original source tile immutable.

## Existing Haughton DEM constraints

The repository's local Copernicus GLO-30 DSM QA records:
- File: `data/raw/earth/copdem_glo30/haughton/Copernicus_DSM_COG_10_N75_00_W090_00_DEM.tif`
- SHA-256: `6731d23cff09f4cb7d2c72ec1d41c7ae9b6389565434e820692e08c2a4bcefa7`
- Grid: 1200 × 3600, one Float32 band, EPSG:4326.
- Native pixel spacing: 0.0008333333° × 0.0002777778°; approximate ground spacing at the provisional site is about 24 × 31 m.
- Product metadata documents EGM2008 heights in metres, but the local raster does not declare a band unit tag or NoData value. The local QA has no companion quality rasters.
- The tile extends from approximately 75° to 76°N and -90° to -89° longitude. The mapped crater area should be checked against this coverage before any clipping.

This tile is a provisional, globally consistent DSM baseline. It is not yet an analysis-ready DEM: no AOI clip, projected metric grid, common scale, effective-resolution assessment, or approved processing policy exists. ArcticDEM v4.1 is a documented higher-resolution regional alternative with quality companions, but its full raster was not downloaded in the reviewed handoff. Do not silently switch source families; compare its coverage, surface type, vertical reference, acquisition dates, quality layers and license first.

## Immediate execution gate

The published map source is now identified and can support a controlled digitization attempt. The next missing inputs are the high-resolution Figure 2 image and the local DEM/hillshade in the same GIS session so that distributed GCPs can be selected and checked. Until the georeferencing and overlay are reviewed, the AOI remains **PROVISIONAL / NOT APPROVED**.

No final AOI polygon, coordinates, clipped raster, reprojected raster, analysis scale, or scientific fingerprint is claimed by this document.
