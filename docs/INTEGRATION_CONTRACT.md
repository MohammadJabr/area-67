# AREA 67 — Application Integration Contract

This contract connects Ghassan's GIS/source preparation, Hiba's Terrain Fingerprint, Omar's matching/planning, and Mohammed's application. The app consumes upstream files; it does not silently recalculate scientific measurements or candidate rankings.

## Canonical files

- data/processed/terrain_fingerprints.csv — one row per target/candidate site, produced by Hiba from Ghassan's analysis-ready rasters and manifest.
- data/processed/candidate_rankings.csv — one row per candidate/target/mission-profile ranking, produced by Omar.
- Optional data/processed/sites.geojson or route GeoJSON/CSV may be provided after the team agrees and tests the schema.

Large DEMs and source archives remain outside Git. Commit small reproducible tests and metadata, not large raster binaries.

## Shared identifiers

Every target and candidate must have a stable unique `site_id` in `terrain_fingerprints.csv`.

The ranking output must contain **both**:

- `target_site_id` — the Moon/Mars target compared against.
- `candidate_site_id` — the Earth candidate being ranked.

Omar's role playbook lists a candidate-side `site_id` output field. For integration, that field can be supplied in place of `candidate_site_id`; the application normalizes `site_id` to `candidate_site_id`. The target ID cannot be inferred and must be explicit.

## `terrain_fingerprints.csv`

One row per analyzed site. Required common columns:

| Column | Meaning |
|---|---|
| `site_id` | Stable unique site identifier shared across all files |
| `planet` | Earth, Moon, or Mars |
| `source_id` | Exact source product identifier, linked to Ghassan's manifest |
| `analysis_scale_m` | Declared physical analysis scale in metres |
| `slope_median` | Median slope in the declared `slope_unit` |
| `slope_p90` | 90th percentile slope |
| `tri_median` | Median Terrain Ruggedness Index |
| `local_relief_p95_p5` | Local relief P95–P5 in the declared vertical unit/window |
| `nodata_pct` | Percentage of invalid/NoData cells in the AOI |

Hiba's preferred MVP output includes `slope_p95`, `tri_p90`, `relief_window_m`, `tri_definition`, `tri_window_cells`, `slope_unit`, and `terrain_class_thresholds` as additional method/statistic fields.

### Terrain Distribution naming variants

Hiba's playbook specifies these three required percentage columns:

- `terrain_low_pct`
- `terrain_mid_pct`
- `terrain_high_pct`

The earlier Mohammed integration draft used these equivalent schema slots:

- `terrain_flat_pct`
- `terrain_moderate_pct`
- `terrain_steep_pct`

The application accepts either complete three-column set, without silently renaming or reinterpreting class labels. The team must document the exact slope thresholds and label meanings. Percentages are calculated by valid area and should sum to approximately 100%.

### Spatial Pattern naming variants

Hiba's preferred MVP statistic is:

- `largest_steep_patch_pct` — the percentage of valid area occupied by the largest connected patch of cells classified as high/steep slope. Document the threshold and whether connectivity is 4-neighbour or 8-neighbour.

The earlier integration draft used:

- `spatial_pattern_metric` — accepted if the precise statistic, units/range, threshold, and scale are documented.

The app accepts either field. It does not assume the two metrics are numerically interchangeable.

### Quality and provenance fields

Required for the current validation contract: `analysis_scale_m` and `nodata_pct`; if `valid_coverage_pct` is supplied, it should complement NoData so the two sum to approximately 100%.

Recommended/expected metadata from Ghassan's manifest:

- `site_name`, `source_name`, `source_url`, `product_version`, `access_date` / acquisition or release date
- `pixel_width_m`, `pixel_height_m`, `crs`, `vertical_reference`
- `elevation_unit`, `nodata_value`, `valid_coverage_pct`
- `quality_layer`, `uncertainty_note`, `processing_steps`
- `latitude`, `longitude`, `area_km2`, `valid_cell_count`

Recommended Hiba method fields:

- `slope_unit`
- `tri_definition`, `tri_window_cells`
- `relief_window_m`
- `terrain_class_thresholds`
- `spatial_pattern_definition`

The app warns when recommended provenance/method metadata is absent. Missing optional statistics remain null. Required MVP groups must still be represented for each site. NoData is never replaced by zero.

## `candidate_rankings.csv`

Canonical app field names:

| Column | Meaning |
|---|---|
| `target_site_id` | Lunar/Martian target site |
| `candidate_site_id` | Earth candidate site |
| `rank` | Positive integer rank within target and mission profile |
| `similarity_score` | Relative ranking score; document range and direction |
| `mission_profile` | Mission profile used for the result |

Omar's playbook documents these output aliases, which the app normalizes:

| Omar's field | App's canonical field |
|---|---|
| `site_id` | `candidate_site_id` |
| `relative_similarity` | `similarity_score` |
| `similarity_distance` | `weighted_distance` |

**`target_site_id` is mandatory**, even when `site_id` is used for the candidate, so rankings remain traceable to their target.

Recommended Omar output fields:

- `slope_contribution`
- `tri_contribution`
- `relief_contribution`
- `distribution_contribution`
- `spatial_pattern_contribution`
- `data_completeness`
- `ranking_stability_note`
- `ranking_note`

Optional route deliverables: `route.geojson` or a documented route CSV with cell/coordinate references, route cost assumptions, and a clear note that a DEM least-cost path is not a rover safety certification.

### Matching method metadata

Omar must document:

- The formula used for group distances and the normalization/scaling method.
- The five group definitions and how their feature values are combined.
- The mission weights and the fact that they are team-selected operational assumptions, not NASA or rover-manufacturer standards.
- How missing feature groups are handled (never impute zero).
- How per-group contributions relate to total distance/score.
- The direction and range of `similarity_score` / `relative_similarity`.
- How `data_completeness` and any ranking-stability summary are calculated.

The app accepts either score/distance naming variant but does not invent a score or assume an undocumented score range. Similarity is a relative comparison, not a probability or certification.

## Active MVP: Space-to-Earth

- Every target must have `planet` = Moon or Mars.
- Every candidate must have `planet` = Earth.
- The ranking file must include target, candidate, rank, score/relative similarity, and mission profile.
- Use one profile for the MVP: **Rover Navigation / Terrain Traversal**.
- Provide at least three Earth candidates if available; the app displays the actual count and warns if fewer are supplied.

Earth-to-Space remains in the product vision but is not the active CSV workflow.

## Application behavior

- Real data is loaded only when both canonical processed files exist.
- If neither real file exists, the app may use paired synthetic fixtures from data/sample for interface development and smoke testing. The UI and exported Passport label them synthetic.
- If only one real output exists, the app stops instead of mixing real and synthetic data.
- The app normalizes only the documented ranking aliases above. It does not infer a target ID.
- Mission selection filters upstream results; it does not recalculate Omar's weights or ranking.
- The Single-Parameter Explorer displays supplied metrics; it does not recompute Hiba's fingerprint.
- The map plots Earth candidate coordinates only. Lunar/Martian coordinates are not plotted on an Earth basemap.
- The Passport shows site identity, source/quality metadata, five fingerprint groups, ranking fields, available matcher explanations, missing data, and limitations.
- Any missing measurements or matcher differences remain explicitly missing; the app does not invent them.

## Run locally

    python -m venv .venv
    # Windows PowerShell: .venv\Scripts\Activate.ps1
    # Git Bash on Windows: source .venv/Scripts/activate
    # macOS / Linux: source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app/main.py

Run tests with `pytest -q`.
