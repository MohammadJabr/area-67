# AREA 67 AOI and MVP implementation status

**Status: AOI geometry release blocked; fail-closed AOI input validation implemented.**

This branch starts from `origin/main` at `f592b5a817baa8359f4a544b28c007f71b0440a4`. PR #98 is closed and unmerged. PR #108 was found open, then closed as requested; it remains unmerged. The older local GIS worktree and its data have not been changed.

## AOI files and evidence

No AOI polygon files were created. The available evidence does not define defensible machine-readable boundaries for these four targets. Creating a polygon from a landmark, arbitrary buffer, source-tile edge, or pilot window would imply a geomorphic boundary the evidence does not support.

| Target | Available source and coverage evidence | AOI geometry status | Raster coverage / valid-pixel percentage | Effective resolution and feature readiness | Final status |
|---|---|---|---|---|---|
| Site01 / Connecting Ridge | The local checkout used for this audit has no `data/raw/moon/site01/` elevation layers or provider ROI vector. `docs/reports/lunar_roi/SITE01_COORDINATE_AND_SDEM_REVIEW.md` records prior workstation observations, including a provider ROI frame caveat, but those source geometries are not available here to reproduce. | **BLOCKED.** Provider geometries are absent from the inspected checkout; recorded frame provenance is unresolved. | Not computable for an AOI. No local Site01 DEM was available. | Prior notes report a 5 m posting and Product 90 EFFRES P50/P90 15.78/24.08 m for a bounded window; posting is not effective resolution. Five-group code exists, but no current geometry/data pair can be run. | BLOCKED |
| Haughton | Local Copernicus GLO-30 DSM source tile and QA/manifest evidence exist. The tile-level QA reports 100% valid coverage; this does not describe an AOI. `docs/reports/earth_aoi/HAUGHTON_AOI_BOUNDARY_REVIEW_2026-11-15.md` identifies the published map pathway and distinct central-basin, final-rim and apparent-rim interpretations. No georeferenced GIS boundary was found in the checkout. | **BLOCKED.** A landform choice and a digitized/georeferenced authoritative map with recorded control points and residuals are missing. | Not computable for an AOI. Tile-level valid coverage must not be substituted. | GLO-30 DSM, geographic source grid, EGM2008 metres per product documentation; effective terrain resolution and per-pixel quality companions are unverified. Earth grids need an approved metric preparation policy. | BLOCKED |
| Yungay | Local Copernicus GLO-30 DSM tile covers the provisional manifest marker and the cited published hyper-arid-core reference. The marker is about 5.81 km from that field reference. The source manifest reports 100% valid cells for the full tile. | **BLOCKED.** The team must confirm which locality/process unit is intended; no authoritative geomorphic boundary for that selection is in the checkout. | Not computable for an AOI. The manifest's 100% is tile-level valid coverage and does not establish site-level support. | GLO-30 DSM, EGM2008 metres per product documentation; effective resolution and per-pixel quality are unverified. Five groups exist only for the provisional reference-centered pilot window. | BLOCKED |
| Mauna Kea | Local Copernicus GLO-30 DSM tile covers the USGS summit reference point. Separate local USGS 3DEP 1 m tiles have different projected CRSs; the eastern tile's vertical reference/units are unverified and the tile pair is not approved for mosaicking. | **BLOCKED.** Summit cones, lava-flow surfaces, glacially modified terrain, or a flank sector have not been selected and no selected-unit boundary is available. | Not computable for an AOI. Tile-level metrics are not AOI coverage. | Copernicus effective resolution is unverified. USGS nominal 1 m posting does not establish effective resolution; surface type and vertical-reference compatibility require resolution before combining sources. | BLOCKED |

The current source manifest's 100% values are whole-tile mask coverage only. No AOI valid-pixel percentage, edge-effect fraction, or feature support is claimed in this report.

## Comparability and existing pipeline

The canonical five-group extractor and matcher are already in `src/features/terrain_fingerprint.py` and `src/matching/`. The current checked-in rows in `data/processed/terrain_fingerprints.csv` and `data/processed/candidate_rankings.csv` are explicitly exploratory reference-window results, not results from the AOIs requested here. They remain the primary five-group presentation dataset on this branch; the Slope-only score remains a diagnostic field. No fingerprints or rankings were regenerated because no target/candidate AOI set, common metric grid, or study settings are established.

For clarity, the existing five-group pilot ranking remains: Haughton 73.7870 (weighted distance 0.3552523), Yungay 66.1325 (0.5121164), and Mauna Kea 27.3897 (2.6510027). Existing one-at-a-time tolerance scenarios retain Haughton at rank 1 in 11/11 cases; Yungay remains in the top two in 11/11; Mauna Kea is not in the top two. This is numerical sensitivity of the same provisional windows/settings, not validation of the AOIs or scientific ranking. The separate Slope-only diagnostic scores are 64.9452, 56.7559, and 22.0970, respectively.

No shared effective analysis scale can be supported from the available evidence. The previously used 30 m grid and feature tolerances remain exploratory assumptions. Earth GLO-30 is a DSM with product-level EGM2008 height metadata; the lunar source requires explicit treatment of its product frame and unresolved vertical reference. A common scale, resampling, AOI mask policy, neighborhood support and quality policy require documented study approval. This audit does not assume 5 m effective lunar detail or any other common scale.

## Implemented safeguards

`src/features/terrain_fingerprint.py` now rejects empty, malformed, non-polygonal, zero-area, or invalid AOI geometries before analysis. After applying the configured AOI CRS transformation, it rejects AOI geometry extending outside the DEM bounds. This prevents a cropped partial intersection from appearing to have complete AOI coverage. The existing extractor still requires a projected metre grid and explicit elevation units, vertical reference, and configured physical analysis settings; it calculates raster-mask support within the AOI and preserves NoData in derivative outputs.

The app on `main` continues to use the canonical five-group ranking. Its map caption identifies Earth markers as reference-window anchors, not AOI polygons. No AOI boundary is drawn where no geometry exists.

## Required evidence and next actions

1. Restore/provide the Site01 provider ROI source files and the product/frame evidence needed to transform them without guessing; select the exact provider feature(s) for the target.
2. For Haughton, select the central basin, final rim/faulted terraces, or another mapped unit, then obtain the cited geological map in usable form and record georeferencing controls/residuals before digitization.
3. Confirm whether Yungay means the cited field locality or another area and obtain a boundary source for that landform.
4. Select a Mauna Kea geomorphic unit and obtain a defensible mapped boundary. Resolve which DEM product/surface type is appropriate and the USGS tile metadata before using either local 1 m tile.
5. Only after the four polygons and stable IDs exist, compute their intersections with the source rasters and report AOI-specific valid support, edge/mask effects, and geometry area/bounds.
6. Team/Hiba/Omar must then settle a common analysis scale and grid, vertical/frame policy, feature settings, weights/tolerances, and acceptance/quality criteria. Run the canonical five-group extraction and matching/robustness commands only on that frozen input set.

No AOI is approved by this implementation. Geometry creation remains blocked where it would require inventing a boundary or choosing a study landform without evidence.

## Validation

- Added synthetic regression tests for invalid polygon rejection and AOI extent exceeding raster bounds; the existing GeoTIFF tests cover explicit AOI CRS transformation, metric-grid enforcement, NoData masks, and feature support.
- Local Python compilation is available; local raster/GIS Python dependencies are not installed in this workstation interpreter. Full CI and Streamlit AppTest should be reported from the pushed PR run, not inferred from earlier runs.
- No raw raster was edited, moved, clipped, reprojected, resampled, mosaicked, or regenerated.

## Reproduction after AOI/data decisions

Use the repository's existing canonical five-group pipeline and matching CLI after copying the approved geometries and filling the run template with explicitly approved values. The current pilot builder/configuration must not be used to relabel reference windows as geomorphic AOIs. Raw acquisition and derived raster outputs remain local/ignored as documented in the existing data workflow.
