# Canonical terrain-fingerprint run — release checklist

This is the handoff checklist for the first canonical Hiba extraction run. It is deliberately not executable until the team supplies and approves the missing study decisions. Do not fill blanks with pilot defaults.

## Run-config template

Copy `config/terrain_fingerprint_run.template.json` to a working file such as `config/terrain_fingerprint_run.json`. The template contains only the extractor's explicit run-level settings; populate `sites` with one record per approved target/candidate.

Each site record must include at minimum:

- `site_id`, `planet`, `source_id`
- `dem_path`, `aoi_path`
- `elevation_unit` (must be metres at extractor input)
- `vertical_reference` (state the documented value, or a precise unresolved/unknown label; this field is metadata and does not validate a physical datum)
- `aoi_crs` (defaults to EPSG:4326 only when the AOI is actually WGS84)
- source/version/date/URL, quality-layer and uncertainty notes, effective-resolution note
- `direct_observation_coverage_pct` only when defensibly computed for the exact AOI; never substitute raster-valid coverage

## Required approvals before execution

| Gate | Required decision/evidence | Owner |
|---|---|---|
| Lunar target | Site01 vs Site04; exact valid provider ROI or independently digitized AOI; coordinate-frame evidence for ROI geometry | Hiba + GIS owner |
| Earth AOIs | Geomorphic polygon and source map/DEM for each candidate; valid geometry, coverage and exclusions | Ghassan |
| Common grid | Planet-specific projected metric CRS, origin/alignment, pixel scale, resampling/aggregation per data layer, NoData policy | Ghassan + Hiba |
| Lunar quality | Separate treatment for surface elevation, LDEC counts, Z RMS, slope and slope RMS; preserve support/uncertainty | Hiba |
| Fingerprint settings | Analysis scale, relief window, minimum neighbourhood fraction, slope thresholds, steep threshold and connectivity | Hiba + team |
| Matching settings | Positive tolerances, mission weights, minimum feature-group and data completeness; retain robustness sidecar | Omar + team |

## Extractor invocation

After the config is complete and all inputs exist:

```bash
python -m src.features.terrain_fingerprint --config config/terrain_fingerprint_run.json --output data/processed/terrain_fingerprints_canonical.csv --maps-dir data/processed/terrain_maps
```

Check the exact CLI options with `python -m src.features.terrain_fingerprint --help` before execution; this document does not replace CLI help.

Then validate the generated fingerprint rows, review per-site quality flags and metadata, and only then run Omar's matcher with the explicitly approved tolerances and completeness thresholds. Keep the exploratory pilot files separate until the canonical pair has passed validation; do not overwrite the demo/pilot evidence in place.

## Hard stops

- Never call a reference-centred sample window an approved geomorphic AOI.
- Never invent an AOI polygon from a centre coordinate or crater diameter.
- Never silently repair invalid provider polygons.
- Never treat native posting as effective resolution.
- Never infer vertical datum or physical frame from a placeholder WKT.
- Never compare absolute Earth/Moon elevations without a defensible frame and vertical transformation.
- Never convert NoData or missing features to zero.
- Never treat LOLA LDEC support, raster-valid coverage and RMS uncertainty as the same quantity.
- A successful software run does not itself approve the science.

## Current known status (2026-11-15)

The merged real-data pilot is available for an exploratory demo. The Site01/Site04 provider ROI support audit and Haughton boundary literature review are documented. The canonical run remains blocked by the approvals and evidence in the table above. The matching tolerance template intentionally remains null; no team-approved real-study tolerance set is committed.
