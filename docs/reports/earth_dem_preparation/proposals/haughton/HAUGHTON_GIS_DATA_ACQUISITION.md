# Haughton GIS Data Acquisition — Author Data Request and Fallback

**Status:** The published workflow confirms that georeferenced geological polygons already existed for the Patterson & Ernst (2020) analysis. The project should attempt to obtain those source vectors before manually rebuilding them from a printed figure.

## New finding

The full-text methodology states that the published Osinski (2005) geological maps were georeferenced, digitized as polygons, and classified by stratigraphic formation. The authors then joined those polygon classes to a 20 m Canadian Digital Elevation Model (CDEM). This establishes that a georeferenced polygon dataset was used in the published analysis, even though this review did not find a public download link for the underlying vectors.

Source: Patterson & Ernst (2020), Methods, steps 1–5: https://onlinelibrary.wiley.com/doi/full/10.1111/maps.13573

Important distinction: the paper's CDEM is a different raster source from AREA 67's local Copernicus GLO-30 tile. Its 20 m posting and its georeferenced vector work are not automatically transferable to our local DEM without checking the original coordinate reference, control, and coverage.

## Preferred next action — request the existing GIS data

Contact the corresponding author, Calder W. Patterson (email listed on the paper: calderpatterson@mail.carleton.ca), and request:

1. The georeferenced Osinski (2005) Haughton geological map used in the 2020 paper.
2. The digitized polygon/line GIS layers and attribute table (GeoPackage, Shapefile, File Geodatabase, or equivalent).
3. The source map scan/image and its map projection / coordinate reference details.
4. Any GCP list, transformation method, residual/RMS report, and digitizing notes.
5. The 20 m CDEM extraction footprint and any derived study-area geometry, if shareable.
6. Reuse/redistribution terms and recommended citation.

Do not assume that the vectors can be redistributed in AREA 67 until the author confirms the terms. If they are supplied, preserve the original files and metadata, inspect their CRS and topology, and cite the source. Compare them with Figure 2 only as a visual consistency check.

## Fallback if the vectors cannot be obtained in time

1. Extract Figure 2 from the author-hosted PDF at its highest available resolution; retain the original PDF and extracted image with SHA-256 provenance.
2. Georeference the map in QGIS against the local Haughton DEM/hillshade using spatially distributed, independently identifiable control points. Use the published crater-centre coordinate (75°22′38″N, 89°40′48″W) as one check, not the sole control point.
3. Preserve the map's classes and certainty: allochthonous crater-fill impactites, parautochthonous crater-fill impactites, Haughton Formation, target formations, water, glacial/fluvial deposits, and definite/approximate/inferred faults.
4. Digitize the allochthonous crater-fill polygons separately from the central-basin structural envelope. The paper says the central basin includes all remaining allochthonous crater-fill impactites plus Haughton Formation lake sediments draped over basin margins; these are not synonymous boundaries.
5. Record GCP coordinates, reference source, transform, per-point residuals, total RMS, digitizer uncertainty, topology validation, and a visual overlay. A low RMS does not remove the source map's line-width/generalization uncertainty.
6. Keep the resulting geometry provisional until reviewed by the GIS lead. Do not fabricate a polygon from a 5–6.5 km radius or use a circular buffer as a substitute for mapped geology.

## Scientific use of the paper's method

The paper's central-basin description provides context for checking the digitized geometry: a broad shallow basin, approximately 5.0–6.5 km radius in the cross-sections, containing both crater-fill impactites and Haughton Formation sediments. It also reports that the 2 km diameter central core is occupied by allochthonous crater-fill impactites and some fluvial/glacial deposits. These statements support class-aware polygon interpretation; they do not supply a complete coordinate boundary.

The paper's 20 m CDEM was used for radial distance and lithology joins. AREA 67 should not copy its 20 m grid as an approved analysis scale. Our common physical scale still requires comparison of source effective resolution, target data, and sensitivity.

## Go / no-go

- **GO:** inspect and reuse author-supplied georeferenced polygons if received with adequate provenance and permission.
- **GO with provisional status:** georeference and digitize the published figure if author data are unavailable and local reference layers support an auditable fit.
- **NO-GO:** invent coordinates, approximate the central basin with a circle, or call the whole Haughton tile an AOI.
- **NO-GO:** generate a real fingerprint or ranking from the full 1° Copernicus tile.

Next handoff required: georeferenced geological vector(s), or the extracted map image plus local DEM/hillshade and GCP report; then a GIS-reviewed provisional AOI and a documented preparation configuration.
