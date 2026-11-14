# AREA 67 — Application Integration Contract

This contract connects the GIS, terrain-analysis, matching, and application workstreams. The application consumes upstream files; it does not silently recompute scientific results.

## Canonical files

- data/processed/terrain_fingerprints.csv — one row per target/candidate site, produced by terrain analysis.
- data/processed/candidate_rankings.csv — one row per candidate/target/mission-profile ranking, produced by matching.
- Optional boundaries/routes may be supplied as GeoJSON after the team agrees and tests the schema. They are not required for the first MVP.

Large source DEMs stay outside Git. Keep a source manifest with exact product/source IDs, versions, access dates, CRS, vertical reference, units, resolution, coverage, NoData handling, quality information, and usage terms.

## terrain_fingerprints.csv

One row per analyzed site. Required columns:

| Column | Meaning |
|---|---|
| site_id | Stable unique site key shared across all files |
| planet | Earth, Moon, or Mars |
| source_id | Source product identifier |
| analysis_scale_m | Physical analysis scale in metres; document resampling/windowing |
| slope_median | Median slope angle; state units |
| slope_p90 | 90th percentile slope; state units |
| tri_median | Median TRI; document formulation and neighborhood |
| local_relief_p95_p5 | Local relief percentile range; document window and vertical units |
| terrain_flat_pct | Percentage of valid area classified as flat |
| terrain_moderate_pct | Percentage of valid area classified as moderate |
| terrain_steep_pct | Percentage of valid area classified as steep |
| spatial_pattern_metric | Interpretable spatial-pattern statistic; document definition and scale |
| nodata_pct | Percentage of analysis cells with missing/invalid data |

### Structural and numeric validation

- site_id must be present and unique; planet and source_id must be non-empty.
- analysis_scale_m must be a finite value greater than zero.
- required numeric columns must contain numeric finite values. Missing metric groups must not be disguised as zero.
- slope statistics cannot be negative; slope_p90 must be greater than or equal to slope_median.
- local_relief_p95_p5 cannot be negative.
- terrain class percentages and nodata_pct must be in the range 0–100.
- the three terrain-class percentages should sum to approximately 100% (within rounding tolerance) when classes cover all valid cells. The app reports a quality warning rather than altering values.

Recommended method/provenance metadata: site_name, source_name, product_version, access_date, crs, vertical_reference, license, latitude, longitude, area_km2, valid_cell_count, slope_unit, tri_definition, tri_window_cells, relief_window_m, terrain_class_thresholds, spatial_pattern_definition, and suggested_test.

Each of the five feature groups must have at least one usable metric per site for the MVP. The application warns where a group is entirely missing. Null individual metrics remain null and are displayed as gaps. Do not assume a column name establishes units or scientific comparability.

## candidate_rankings.csv

Required columns:

| Column | Meaning |
|---|---|
| target_site_id | Target key from terrain_fingerprints.csv |
| candidate_site_id | Candidate key from terrain_fingerprints.csv |
| rank | Positive integer rank within target and mission profile |
| similarity_score | Relative score; document range and direction |
| mission_profile | Named mission profile used for the ranking |

### Structural and join validation

- target_site_id, candidate_site_id, and mission_profile must be present and non-empty.
- rank and similarity_score must be numeric and finite. Rank must be a positive integer.
- each target/candidate/mission_profile combination must be unique.
- ranks must be unique within each target and mission profile.
- every target and candidate ID must refer to a row in terrain_fingerprints.csv.
- for the active Space-to-Earth MVP, every target must be Moon or Mars and every candidate must be Earth. Earth-to-Space is a separate future workflow, not an implicit variation of this CSV.

Recommended optional fields:

- weighted_distance
- slope_contribution, tri_contribution, local_relief_contribution, terrain_distribution_contribution, spatial_pattern_contribution
- slope_difference, tri_difference, local_relief_difference, terrain_distribution_difference, spatial_pattern_difference
- ranking_note, suggested_test

The matching owner must document scaling, weights, missing-data behavior, score direction, the definition of each reported difference, and whether contribution fields sum to the reported distance/score. The app displays matcher-reported differences and contributions; it does not invent them or impose an undocumented score range.

## Application behavior

- Uses the real processed file pair only when both are present.
- If neither real file exists, it may use paired, clearly labelled synthetic fixtures in data/sample/ for interface development. The UI and exported Passport identify these as synthetic.
- If only one real output exists, it stops instead of mixing real and synthetic results.
- Missing feature values remain missing, not zero.
- The 24-hour MVP implements Space-to-Earth: one lunar/Martian target, one mission profile, and at least three Earth candidates. Earth-to-Space remains in the product architecture as a future direction.
- Mission-profile selection filters the matching output. It does not pretend to recalculate weights or rankings.
- The Single-Parameter Explorer displays supplied feature values; it does not recompute the Terrain Fingerprint.
- The candidate map displays Earth candidates only. Planetary coordinates must not be plotted on an Earth basemap.
- Passport uses supplied site, provenance, ranking, and optional comparison rows. Unknown provenance and unreported differences remain explicitly unknown.
- Thermal, geological, environmental, and subsurface layers are context-only until compatible source data and calculations have been validated. They are not added to the core similarity score by default.

## Run locally

    python -m venv .venv
    # Windows PowerShell: .venv\Scripts\Activate.ps1
    # Git Bash on Windows: source .venv/Scripts/activate
    # macOS / Linux: source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app/main.py

Run tests with pytest -q.
