# NASA LOLA Site01 — ROI, support, uncertainty and registration review

**Review date:** 2026-11-15  
**Site:** NASA PGDA LOLA Site01 — Connecting Ridge  
**Status:** Local evidence review completed; provider ROIs remain provisional and are not AREA 67-approved study AOIs.

## 1. Scope and provenance

This report consolidates the local Site01 command outputs supplied during the AREA 67 GIS review. The five NASA PGDA raster assets and provider ROI shapefile were inspected on the project workstation. Large raw rasters and the generated JSON reports remain local; this document records the measured results and the commands used, not a replacement for the original files.

Inputs:

- ROI source: `data/raw/moon/roi_shapes/Site01/Site01_ROIs.shp`
- Elevation: `data/raw/moon/site01/Site01_final_adj_5mpp_surf.tif`
- LDEC counts: `data/raw/moon/site01/Site01_final_adj_5mpp_ldec.tif`
- Slope: `data/raw/moon/site01/Site01_final_adj_5mpp_slp.tif`
- Elevation RMS uncertainty: `data/raw/moon/site01/Site01_final_adj_5mpp_toterr.tif`
- Slope RMS uncertainty: `data/raw/moon/site01/Site01_final_adj_5mpp_slperr.tif`

Provider catalog: https://pgda.gsfc.nasa.gov/products/78

## 2. Raster inventory and structural QA

All five assets were locally downloaded or found already present, then inspected:

| Property | Result |
|---|---|
| Dimensions | 3,200 × 3,200 pixels per layer |
| Band count / data type | One band, Float32 |
| Nominal pixel posting | 5 m × 5 m |
| Affine transform | [5, 0, -19000, 0, -5, -4000] |
| Raster bounds | X [-19000, -3000] m; Y [-20000, -4000] m |
| Valid finite pixels | 10,240,000 / 10,240,000 per layer |
| Raster-mask valid coverage | 100% per layer |
| NoData / non-finite samples | 0 masked and 0 non-finite samples per layer |
| LDEC value range | 0 to 5 |

The Site01 QA command reported:

- `exact_grid_alignment=True` for the five layers.
- `positive_LDEC_pct=9.4942` across the full valid raster.
- The remaining valid zero-count LDEC cells represent interpolated LDEM support, not NoData.

A 100% valid raster mask is not 100% direct LOLA observation. The 9.4942% figure is site-wide and must not be substituted for a polygon-specific support percentage. Five-metre posting is not proof of five-metre effective terrain resolution or accuracy.

Both the local raster and provider ROI WKT use placeholder unknown datum labels, but their roles differ: NASA PGDA Product 78 documents the GeoTIFF raster layers as MOON_ME/DE421 and explicitly excludes ROI shapefiles. Thus the raster frame is source-documented at product level; the provider ROI shapefile frame remains unverified. Do not assign the raster frame to ROI shapes, rewrite raw WKT, invent an ME/PA shift, or infer a vertical datum from the horizontal CRS.

## 3. Native-geometry ROI audit

The normal ROI-quality audit uses pixel centres inside the original polygon (`all_touched=false`). Features 0–4 are valid source polygons and have 100% elevation and LDEC raster coverage at their included pixel centres.

Feature indexing below is zero-based as reported by the script. The ROI number is the corresponding one-based sequence position in the seven-feature shapefile.

| Feature | ROI | Polygon area (m²) | Perimeter (m) | Compactness¹ | Pixel centres | Positive LDEC support | Zero-count / interpolated | Median Z RMS (m) | Median slope RMS (°) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 7,687.5 | 437.49 | 0.505 | 317 | 4.73% | 95.27% | 0.4397 | 2.1188 |
| 1 | 2 | 6,575.0 | 474.56 | 0.367 | 270 | 11.48% | 88.52% | 0.3103 | 1.8234 |
| 2 | 3 | 3,137.5 | 312.63 | 0.403 | 135 | 17.78% | 82.22% | 0.2658 | 1.6642 |
| 3 | 4 | 11,900.0 | 661.84 | 0.341 | 484 | 9.09% | 90.91% | 0.3492 | 1.9321 |
| 4 | 5 | 8,587.5 | 665.77 | 0.243 | 362 | 11.05% | 88.95% | 0.3036 | 1.7799 |

¹ Compactness is the dimensionless circularity measure (4\pi A/P^2), calculated only for valid original polygons. It is a shape descriptor, not a mobility or safety metric.

The following are the exact per-feature source attributes and native vector metrics from the local geometry inventory:

| Feature | Source X (m) | Source Y (m) | Bounds X (m) | Bounds Y (m) |
|---:|---:|---:|---|---|
| 0 | -11582.5 | -12462.5 | [-11657.5, -11522.5] | [-12517.5, -12407.5] |
| 1 | -11487.5 | -12557.5 | [-11537.5, -11447.5] | [-12637.5, -12477.5] |
| 2 | -11352.5 | -12502.5 | [-11392.5, -11297.5] | [-12542.5, -12467.5] |
| 3 | -11287.5 | -12167.5 | [-11372.5, -11212.5] | [-12267.5, -12052.5] |
| 4 | -11102.5 | -11942.5 | [-11177.5, -11002.5] | [-12052.5, -11857.5] |

Positive LDEC support is the percentage of valid finite LDEC pixels inside each ROI with a positive spot count. Zero-count cells are reported separately as interpolated LDEM support. RMS uncertainty medians are descriptive summaries, not guaranteed per-cell error bounds.

## 4. Invalid source polygons and read-only repair sensitivity

The original features 5 and 6 are invalid due to ring self-intersections. Their native-geometry ROI statistics are therefore not calculated by the normal QA tool.

| Feature | Source validity reason | In-memory `make_valid` output | Polygonal result |
|---:|---|---|---|
| 5 | Ring self-intersection at (-10732.5, -11722.5) | MultiPolygon: 2 Polygon components | 8,900 m² combined; one component is only 12.5 m² |
| 6 | Ring self-intersection at (-10167.5, -11602.5) | GeometryCollection: 1 Polygon + 2 LineStrings | 6,037.5 m² Polygon; both LineStrings excluded from raster statistics |

Repair-preview measurements (not official native-geometry ROI results):

| Feature | Preview pixel centres | Positive LDEC support | Zero-count / interpolated | Median Z RMS (m) | Median slope RMS (°) |
|---:|---:|---:|---:|---:|---:|
| 5, union of polygon components | 373 | 12.06% | 87.94% | 0.3030 | 1.7961 |
| 5, component 0 (8,887.5 m²) | 372 | 12.10% | 87.90% | 0.3032 | 1.7997 |
| 5, component 1 (12.5 m²) | 1 | 0.00% | 100.00% | 0.1392 | 1.2575 |
| 6, polygon only | 256 | 10.94% | 89.06% | 0.3147 | 1.8046 |

Feature 5's 12.5 m² fragment has only one pixel centre and no direct LDEC shot support. Feature 6's two line remnants are lower-dimensional topology outputs and were not converted into area. These results describe temporary in-memory candidates; they do not establish the provider's intended boundary or authorize replacing either source feature. Keep features 5 and 6 marked `review_required`.

## 5. Pixel-registration audit

The versioned ROI-quality workflow now exports each original provider polygon as native_geometry in its compact JSON artifact, alongside the original shapefile WKT, one-based provider ROI number, validity reason, native bounds/area/centroid, and any valid-pixel support statistics. Coordinates are retained in the source projected coordinate plane; this is not WGS84 GeoJSON and does not assign a physical frame to the ROI shapefile.

The read-only registration audit examined all seven source geometries, including the two invalid polygons:

- 7 features and 607 vertices.
- 607 / 607 vertices (100%) align with the raster pixel-centre lattice.
- Maximum pixel-centre residual: 0 m.
- 0 vertices align with the pixel-corner lattice.

This demonstrates exact geometric agreement between the submitted shapefile vertices and this raster's affine pixel-centre lattice. It does not repair self-intersections, validate the physical lunar frame, or establish the scientific rule used to create the ROIs.

## 6. Cross-check against the provisional Site04 review

The currently available native-geometry summaries support a limited comparison:

| Site / feature | Valid source geometry | Pixel centres | Positive LDEC support | Median Z RMS (m) | Median slope RMS (°) |
|---|---:|---:|---:|---:|---:|
| Site01 / feature 2 | Yes | 135 | 17.78% | 0.2658 | 1.6642 |
| Site04 / feature 2 | Yes | 102 | 14.71% | 0.2656 | 1.6038 |
| Site04 / feature 3 | Yes | 101 | 13.86% | 0.2678 | 1.4734 |

Site01 feature 2 has the highest direct-shot support among these three records. Site04 feature 3 has the lowest median slope RMS. Their median elevation RMS values are close. These are separate evidence dimensions; they do not establish an overall winner, a safer rover route, or a preferred lunar base AOI.

Site01's site-wide direct-support percentage (9.4942%) and Site04's previously reported site-wide percentage (9.1541%) are not substitutes for ROI-specific values. The target polygons also have not been approved by the AREA 67 team.

## 7. Pixel-count and polygon-area accounting

A separate diagnostic counted cells touched by each valid polygon:

| Feature | Polygon area (m²) | Pixel-centre count | All-touched count |
|---:|---:|---:|---:|
| 0 | 7,687.5 | 317 | 360 |
| 1 | 6,575.0 | 270 | 313 |
| 2 | 3,137.5 | 135 | 161 |
| 3 | 11,900.0 | 484 | 554 |
| 4 | 8,587.5 | 362 | 417 |

A 5 m cell has a nominal 25 m² area, but multiplying a pixel count by 25 m² is a rasterized-area estimate under that pixel-inclusion rule, not the vector polygon's exact area. `all_touched` deliberately includes cells intersected only at their edges and therefore produces larger counts. Do not call either count-derived value the provider's official polygon area. Any difference from an area stated in a paper needs a separate boundary/method/provenance reconciliation; this audit does not establish its cause.

## 8. Conclusions and blockers

Completed locally for Site01:

- Acquisition/presence check of all five raster assets.
- Five-layer metadata inspection and exact-grid QA.
- Seven-feature native ROI support and uncertainty audit.
- Read-only topology repair preview for the two invalid features.
- Pixel-registration audit of all 607 vertices.
- Geometry area, perimeter, compactness, centroid and bounds inventory.

Still unresolved:

1. The Site01 provider ROI polygons are not AREA 67-approved study AOIs.
2. The physical lunar body-fixed frame/datum is not resolved by the local WKT; no guessed shift is authorized.
3. The intended treatment of original invalid features 5 and 6 requires provider/topology provenance review.
4. Site04 and Site01 have not been selected as the final lunar target/sub-AOI.
5. Three to five Earth landform AOIs have not been delineated or approved.
6. A common physical analysis grid, projection, scale, source/resampling policy, relief window, support policy and completeness threshold are not approved.
7. No real five-group terrain fingerprints or Earth–Moon rankings have been generated.

The next scientifically valid handoff is a team decision on the target lunar ROI(s), named Earth landforms and polygon boundaries, followed by a documented common-grid/scale policy. Do not generate real fingerprints from whole source tiles or unapproved provider ROIs.

## 9. Reproduction commands

Run from the repository root after the five local rasters and Site01 ROI archive are available:

```powershell
python src/data/lola_south_pole.py inspect --sites Site01 --assets elevation counts slope z_uncertainty slope_uncertainty
python src/data/lola_south_pole.py qa --sites Site01
python src/data/lola_roi_quality.py --sites Site01 --roi-root data/raw/moon/roi_shapes --output-root data/metadata/lola_roi_quality_site01_20261115
python src/data/preview_invalid_roi_repairs.py --site Site01 --roi-directory data/raw/moon/roi_shapes/Site01 --output data/metadata/site01_invalid_roi_repair_preview_20261115.json
python src/data/audit_roi_pixel_registration.py --shapefile data/raw/moon/roi_shapes/Site01/Site01_ROIs.shp --raster data/raw/moon/site01/Site01_final_adj_5mpp_surf.tif --output data/metadata/site01_roi_registration_20261115.json
```

All audit and repair-preview commands are read-only with respect to the source ROI geometries and raster values. They write derived reports only. Keep the large source rasters outside Git.
