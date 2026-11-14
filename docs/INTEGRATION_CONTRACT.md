# AREA 67 — Application Integration Contract

This contract connects the GIS, terrain-analysis, matching, and application workstreams. The application consumes files; it does not silently recompute upstream scientific results.

## Canonical files

- `data/processed/terrain_fingerprints.csv` — one row per target/candidate site, produced by terrain analysis.
- `data/processed/candidate_rankings.csv` — one row per candidate/target/mission-profile ranking, produced by matching.
- Optional supporting boundaries/routes may be supplied as GeoJSON once agreed and tested. The first app does not require them.

Large source DEMs stay outside Git. Keep a manifest with exact product/source IDs, versions, access dates, CRS, vertical reference, units, resolution, coverage, NoData handling, quality information, and usage terms.

## `terrain_fingerprints.csv`

Required columns (one row per site):

| Column | Meaning |
|---|---|
| `site_id` | Stable unique site key shared across all files |
| `planet` | Earth, Moon, or Mars |
| `source_id` | Source product identifier |
| `analysis_scale_m` | Physical analysis scale in metres; document resampling/windowing |
| `slope_median` | Median slope angle; record units (recommended degrees) |
| `slope_p90` | 90th percentile slope; record units |
| `tri_median` | Median TRI; document formulation and neighborhood |
| `local_relief_p95_p5` | Local relief percentile range; document window and vertical units |
| `terrain_flat_pct` | Percentage of valid area classified as flat |
| `terrain_moderate_pct` | Percentage of valid area classified as moderate |
| `terrain_steep_pct` | Percentage of valid area classified as steep |
| `spatial_pattern_metric` | Interpretable spatial-pattern statistic; document definition and scale |
| `nodata_pct` | Percentage of analysis cells with missing/invalid data |

Recommended optional columns: `site_name`, `source_name`, `product_version`, `access_date`, `crs`, `vertical_reference`, `license`, `latitude`, `longitude`, `area_km2`, `valid_cell_count`, `slope_unit`, `tri_definition`, `tri_window_cells`, `relief_window_m`, `terrain_class_thresholds`, and `spatial_pattern_definition`.

Do not assume a column name establishes units or scientific comparability.

## `candidate_rankings.csv`

Required columns:

| Column | Meaning |
|---|---|
| `target_site_id` | Target key from `terrain_fingerprints.csv` |
| `candidate_site_id` | Earth candidate key from `terrain_fingerprints.csv` |
| `rank` | Candidate rank within target and profile |
| `similarity_score` | Relative score; document range and direction |
| `mission_profile` | Named mission profile used for the ranking |

Recommended optional fields: `weighted_distance`, per-feature `*_contribution` fields, and `ranking_note`. Matching owner documents scaling, weights, missing-data behavior, and contribution interpretation.

## Application behavior

- Uses real processed files only when both are present.
- If neither real file exists, uses paired synthetic sample CSVs and shows DEMO MODE warning.
- If only one real output exists, stops instead of mixing real and synthetic results.
- Missing feature values remain missing, not zero.
- Mission profile selection filters matching outputs; does not pretend to recalculate weights.
- Passport uses supplied site and ranking rows. Unknown provenance remains unknown.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
streamlit run app/main.py
```

Test with `pytest -q`.
