# First provisional Earth–Moon terrain MVP execution

**Status: executable demonstrator; all AOIs, the common analysis grid, and matching tolerances remain provisional and require team review.**

## Lunar AOI and source

- Target: MOON_SITE04_OP_MVP; NASA PGDA Site04, cataloged as the Shackleton rim.
- Operational AOI: circle radius 5000 m centered at local DEM coordinates (-2735.00, -6352.50) m, derived from the envelope of all official ROI features.
- This circle is not the provider illumination ROI, a geological rim boundary, or a team-approved site boundary.
- Provider ROI feature vertices align exactly to DEM pixel centers (0 m max residual), supporting local-grid placement. The global lunar frame remains unresolved; no coordinate transformation was applied.
- Native ROI support: 3,141,548 pixel centers; positive LDEC 8.292%; median source Z RMS 0.371 m; slope RMS median 1.493 degrees.
- Site01 is not locally acquired. Site04 was used as the best available local lunar source; no other dataset was downloaded.

## Prepared products

- `data/processed/site04_operational_mvp_20261115_run5/site04_operational_dem_31m_provisional.tif`: average-resampled 31 m provisional elevation GeoTIFF; source unchanged.
- `data/processed/site04_operational_mvp_20261115_run5/site04_validity_mask.tif`: separate source-validity/AOI mask.
- `data/processed/site04_operational_mvp_20261115_run5/site04_aspect_degrees.tif` and `site04_hillshade_315_45.tif`.
- Hiba slope, Riley TRI roughness, and local-relief maps: `data/processed/site04_operational_mvp_20261115_run5/fingerprint_maps`.
- AOI GeoJSON/GPKG, run config, and source/processing manifest: `data/processed/site04_operational_mvp_20261115_run5`.

## Fingerprint and comparison

- Real Hiba fingerprint: `data/processed/site04_operational_mvp_20261115_run5/site04_fingerprint.csv`; generated with Hiba implementation from the sibling checkout `../area-67-gis-publishing`.
- Five existing Earth fingerprint rows plus one lunar row passed current data-contract validation; Hiba quality status is `REVIEW`.
- Direct LOLA support is 8.292% of valid native pixels in this AOI. The matcher reports this separately and does not include it or RMS uncertainty in the score.
- Omar's current matcher ranked five Earth candidates under the existing Rover Navigation / Terrain Traversal profile.
- `data_completeness=1.0` means all required feature groups are present and the raster masks have full valid coverage; it does not mean high measurement confidence or high direct LOLA support.
- Matching used documented example tolerances (slope 5 degrees, TRI 2 m, relief 10 m, distributions and pattern 10 percentage points); these remain illustrative, not approved.
- Score formula is 100/(1+weighted distance); scores are relative tolerance-scaled indices, not probabilities or certifications.

| Rank | Earth candidate | Score | Distance | Data completeness |
|---:|---|---:|---:|---:|
| 1 | EARTH_MCMURDO_OP_MVP | 32.4850 | 2.078346 | 1.000 |
| 2 | EARTH_MAUNA_KEA_OP_MVP | 17.6434 | 4.667855 | 1.000 |
| 3 | EARTH_YUNGAY_OP_MVP | 13.6458 | 6.328243 | 1.000 |
| 4 | EARTH_ASKJA_OP_MVP | 13.1196 | 6.622180 | 1.000 |
| 5 | EARTH_HAUGHTON_CENTRAL_BASIN_OP_MVP | 11.3160 | 7.837052 | 1.000 |

### Feature explanation for the lowest-distance candidate (EARTH_MCMURDO_OP_MVP)

Group distances are absolute feature differences divided by the illustrative tolerance; values are not probabilities.
| Feature group | Tolerance-scaled distance |
|---|---:|
| slope | 0.9262 |
| tri | 3.4555 |
| local_relief | 1.5049 |
| terrain_distribution | 2.4232 |
| spatial_pattern | 1.2853 |
The largest normalized difference for this candidate is **tri**. This describes the current comparison settings only and does not establish field suitability.

## Application integration

- Canonical files now exist: `data/processed/terrain_fingerprints.csv` and `data/processed/candidate_rankings.csv`.
- The existing app loads this complete real-data pair and exposes target selection, feature comparisons, scores, and site passports. No application code was changed.

## Limitations

- 31 m / 124 m settings, 10/25-degree terrain classes, 25-degree steep threshold, and 8-connectivity are demonstrator settings reused from the existing Earth run; they are not scientific approvals.
- Site04 nominal 5 m posting is not effective resolution. Most valid cells have zero LDEC and are interpolated.
- Site04 vertical reference and global lunar body-fixed ROI frame remain unresolved; the workflow compares local projected terrain without a global transformation.
- No uncertainty propagation, direct-observation scoring, effective-resolution correction, or geology-boundary claim is made.
- Rankings are provisional and depend on the illustrative tolerance set and existing operational mission weights.

## Reproducibility

Run `python scripts/run_earth_moon_mvp.py --hiba-root ../area-67-gis-publishing --output-dir data/processed/site04_operational_mvp_20261115_run5 --report docs/reports/earth_dem_preparation/deliverables/earth_moon_mvp_execution_20261115_validated.md` from the repository root. The command refuses to overwrite existing outputs.
