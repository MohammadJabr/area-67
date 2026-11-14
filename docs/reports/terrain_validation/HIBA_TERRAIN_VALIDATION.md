# Hiba Terrain Validation — Implementation Record

**Project:** AREA 67 · NASA Space Apps Challenge 2026  
**Workstream:** Terrain Fingerprint · Statistics · Quality Validation  
**Record date:** 2026-11-15  
**Status:** Code + synthetic tests implemented; real measurements blocked by upstream AOI/scale decisions and raster availability.

## Delivered in this workstream

- `src/features/terrain_fingerprint.py`: array-based feature calculations, fail-closed GeoTIFF/AOI processing, configurable physical scale/window, canonical CSV output and optional derived GeoTIFF maps. Masked integer DEMs are safely converted to floating point before NoData filling.
- `src/features/validation.py`: integration-contract checks, a Spearman feature-correlation audit and a two-scale sensitivity comparison utility.
- `tests/test_terrain_fingerprint.py`: synthetic flat, plane, bump, NoData, area-class, connected-patch, scale-guard, output-contract, correlation minimum-sample and sensitivity tests.
- `docs/TERRAIN_FINGERPRINT_METHOD.md`: feature definitions, formulae, units, scale assumptions, QA rules and usage.

## Test evidence

The focused test module was run in the development workspace using `python -m pytest -q tests/test_terrain_fingerprint.py`.

- **15 passed**
- Tests cover the analytic slope of a plane, near-zero derivatives for a flat surface, positive TRI around a synthetic bump, strict NoData propagation, percentage closure, spatial connectivity, scale mismatch rejection, integer-valued GeoTIFF ingestion, direct-observation provenance without an invented cutoff, contract consistency, correlation sample-size guard and resolution-sensitivity calculation.

These tests validate the implemented calculations on constructed surfaces; they are not validation against NASA or Earth reference terrain products.

## Real-data readiness review

The latest Ghassan handover records five Copernicus GLO-30 Earth DSM source tiles and a provisional USGS Mauna Kea 1 m alternative, but explicitly states that candidate coordinates/AOIs, source combinations and analysis scale are not approved. Several other regional datasets are catalog-level coverage only, not downloaded analysis-ready rasters.

The provisional lunar target is LOLA Site04. The local QA record states 100% valid raster coverage but only 9.1541% positive LDEC direct-observation support; these are different quantities. Its embedded CRS datum is recorded as unknown, and its nominal 5 m posting is not demonstrated effective resolution.

Accordingly, no real `terrain_fingerprints.csv`, ranking-ready measured feature values, feature correlation result or scale-sensitivity result is claimed in this record. Creating one before the AOI/common-grid decisions would create false precision.

## Decisions required before a real run

1. Approve the lunar target sub-area and stable `site_id`.
2. Approve 3–5 Earth candidate AOI polygons and stable IDs; do not use full 1° source tiles as candidate sites.
3. Agree the shared physical analysis scale, reprojection method and vertical-unit/reference policy.
4. Decide whether a consistent DSM source is acceptable for the baseline or whether a DTM is required; record surface-type limitations if sources differ.
5. Approve the relief-window size and any alternate class thresholds/connectivity.
6. Confirm how Site04 LDEC direct-observation support and RMS uncertainty layers should be shown alongside, not substituted for, raster valid coverage.

## Handoff

After those decisions, Ghassan supplies analysis-ready DEMs, AOIs and the manifest; Hiba runs the extraction and QA pipeline; Omar consumes the resulting one-row-per-site CSV; Mohammed integrates the real CSV pair only after the output contract and candidate rankings validate. The Streamlit application must remain in clearly labelled DEMO MODE until both real processed CSVs exist and pass end-to-end checks.
