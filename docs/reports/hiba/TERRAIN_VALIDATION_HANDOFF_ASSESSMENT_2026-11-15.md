# Hiba Terrain Validation — Handoff Assessment

**Assessment date:** 2026-11-15  
**Source reviewed:** `03_Hiba_Sbouh_Terrain_Validation.pdf` (9-page personal 24-hour execution playbook).

## Executive decision

The original playbook defines a practical MVP method and execution schedule. It is not, by itself, evidence that the canonical real-data scientific validation has been completed.

The repository now contains the five-group extractor, synthetic tests, method report, test evidence, and a detailed execution-readiness runbook. PR #103 was merged and its PR CI plus post-merge main CI both passed.

## What the playbook requires and current evidence

| Playbook requirement | Current evidence | Status |
|---|---|---|
| One lunar/Martian target and at least three Earth candidates | Working sprint scope: Site01, Haughton, Askja, Mauna Kea | Selected shortlist; AOIs not approved |
| Five feature groups | Extractor implements Slope, Riley TRI, Local Relief, Terrain Distribution and Spatial Pattern | Software implemented |
| One documented indicator per group | Method report defines formulas, units and summaries | Documented |
| Unified one-row-per-site fingerprint table | App contract and extractor output schema exist | Canonical CSV pending |
| Synthetic tests | Tests cover flat/plane/bump, NoData, distribution, patch pattern, scale, raster pipeline and config | CI passed |
| Real DEM masks and scale checks | Source inventories, raster preflight and GIS acquisition/audit workflow exist | Raw/source QA exists; common-grid AOI inputs pending |
| Three Earth candidate fingerprints | No approved candidate AOIs/common analysis grid | Pending |
| Scale/window sensitivity | Comparison utility exists | Canonical two-scale results pending |
| Feature redundancy/correlation | Spearman audit exists; Terrain Distribution explicitly derived from Slope | Canonical audit pending until comparable rows exist |
| Independent reference comparison | No completed same-footprint reference comparison recorded | Optional; not yet done |
| Quality/uncertainty | Site01/Site04 provider ROI support audit reports valid coverage, positive LDEC support and RMS separately | Source audit exists; per-pixel quality propagation into fingerprints remains incomplete |
| Derived maps and handoff package | Extractor can write slope/TRI/local-relief GeoTIFFs; runbook and method package committed | Code/docs ready; canonical maps pending |

## Data availability and limitations

- Earth Copernicus GLO-30 DSM tiles are inventoried for Haughton, Askja, Mauna Kea, Yungay and McMurdo. Local per-pixel quality companions are absent; effective terrain resolution is not established.
- The local USGS 3DEP 1 m Mauna Kea tile has EPSG:26904 / NAVD88 and its provisional point is about 150 m from the eastern edge. Do not mix it with GLO-30 without a declared source, vertical-reference and resampling policy.
- NASA PGDA Site01/Site04 five-layer LOLA rasters and provider ROI support/uncertainty audits are available. The raster GeoTIFF frame is documented by Product 78; the provider ROI shapefile frame remains unverified. Invalid polygons remain unrepaired.
- Site01 Feature 4 is the current primary registration/quality review anchor and Feature 2 the direct-support cross-check. Neither is an approved operations AOI.

## Hard blockers for canonical scientific completion

1. Source-backed, approved Earth AOI polygons and complete DEM coverage.
2. Verified lunar ROI geometry frame and selected target footprint.
3. Common projected metric grid, alignment, scale(s), layer-specific resampling/aggregation and NoData policy.
4. Explicit vertical-reference handling and no unsupported cross-planet elevation comparison.
5. Approved Hiba settings: scale, relief window, local neighbourhood support fraction, slope classes, steep threshold and connectivity.
6. A populated canonical run config and real extraction outputs.
7. Quality/uncertainty reporting, scale sensitivity where valid, and downstream Omar/Mohammed handoff.

The canonical template is intentionally blank until these decisions are approved. Exploratory reference-centred pilot windows must not be substituted for geomorphic AOIs.

## Verified software/CI evidence

- PR #103: [full test suite passed](https://github.com/MohammadJabr/area-67/actions/runs/43708031319).
- PR #103 merged to main as `873ba8aa5773cf4cf7f9900f92914ea33d1bd626`.
- Post-merge main full test suite: [run #43708208185 passed](https://github.com/MohammadJabr/area-67/actions/runs/43708208185).

A passing CI run verifies the tested software behaviours. It does not approve the scientific inputs or validate a planetary-analog ranking.

## Final verdict

**Ready:** extractor implementation, synthetic test coverage, method documentation, execution runbook and CI for PR #103.

**Not yet complete:** canonical fingerprints/derived maps for Site01 plus Haughton, Askja and Mauna Kea, because AOIs, coordinate-frame handling, common-grid decisions and approved run settings are not yet available.

See [Hiba execution readiness](HIBA_EXECUTION_READINESS_2026-11-15.md) for the exact sequence and commands.
