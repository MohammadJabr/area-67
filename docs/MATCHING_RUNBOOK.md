# AREA 67 — Omar matching workflow runbook

## What this workflow consumes

The matching engine consumes **terrain fingerprints**, not raw DEM files. Ghassan prepares documented raster data and source metadata; Hiba derives the five fingerprint groups. Omar's workflow then compares one Moon/Mars target against Earth candidates.

Input file:

- \`data/processed/terrain_fingerprints.csv\`

The loader expects at least \`site_id\` and \`planet\`. The matcher additionally needs the fields and method metadata documented in \`MATCHING_METHOD.md\`. Missing values remain missing; they are not changed to zero.

## Before running on team data

1. Confirm the target area and mission profile with the team. Site04 (Shackleton rim) is currently documented as a **provisional** lunar target, not a finalized team decision.
2. Confirm that the fingerprint CSV includes exactly one row for the chosen target site and Earth rows for candidate sites.
3. Confirm that all rows use a comparable, documented \`analysis_scale_m\`.
4. Confirm the exact units and method metadata: slope units, elevation units, TRI definition/window, relief physical window, terrain-class thresholds, and spatial-pattern definition/connectivity.
5. Ask the feature/data owners to confirm that TRI values are expressed in the declared elevation unit.
6. Agree explicit per-feature tolerances with the team. The tolerance values define the distance scale and therefore directly affect ranks and display scores. They are **not** automatically derived from the input sample and are not official NASA or rover specifications.
7. Review NoData, direct instrument support, and uncertainty separately. A valid raster mask is not the same as direct instrument observation.

For the provisional Site04 product, the GIS handoff reports that 9.1541% of valid cells have positive LOLA spot counts and 90.8459% are interpolated. That support value must not be confused with \`valid_coverage_pct\` or \`nodata_pct\`.

## Configure feature tolerances

Copy the blank template:

PowerShell:

\`\`\`powershell
Copy-Item config/matching_tolerances.template.json config/matching_tolerances.json
\`\`\`

Edit \`config/matching_tolerances.json\` and replace every \`null\` with a positive number approved for the study:

| Key | Units |
|---|---|
| \`slope_deg\` | degrees |
| \`tri_m\` | metres of TRI |
| \`local_relief_m\` | metres of local relief |
| \`terrain_distribution_pp\` | percentage points |
| \`spatial_pattern_pct\` | percentage points for largest steep-patch area |

If the fingerprint table uses \`spatial_pattern_metric\` instead of \`largest_steep_patch_pct\`, use a key called \`spatial_pattern_metric\` instead, with units appropriate to that documented metric. Do not use the percentage tolerance for an arbitrary metric.

The JSON file with team-approved tolerances should be retained with the analysis record. Do not overwrite the blank template.

## Run the matching workflow

From the repository root, with the project environment active:

\`\`\`powershell
python -m src.matching.cli --fingerprints data/processed/terrain_fingerprints.csv --target-site-id MOON_SITE04 --tolerances-json config/matching_tolerances.json
\`\`\`

Replace \`MOON_SITE04\` with the exact target \`site_id\` from the CSV if the team selects another site.

Optional safeguards:

- \`--min-feature-group-completeness 0.60\` requires at least 60% of the configured positive mission weight to be represented by available feature groups. The threshold is a team choice.
- \`--min-data-completeness 0.60\` requires at least 60% under the pipeline's conservative completeness definition.
- \`--scale-relative-tolerance 0.01\` sets the allowed relative difference in \`analysis_scale_m\`. The default 1% is a software default, not a universal physical rule.

If a candidate has incompatible method definitions or spatial scales, it is reported in \`rejected_candidates\` with a reason. A group whose required method metadata or metric is absent is reported as missing and excluded; it is not imputed as zero.

## Outputs

The workflow writes:

- \`data/processed/candidate_rankings.csv\` — app-facing results with \`target_site_id\`, \`candidate_site_id\`, \`mission_profile\`, \`rank\`, \`similarity_score\`, \`weighted_distance\`, feature contributions, completeness, and method/quality context.
- \`data/processed/ranking_robustness.json\` — one-at-a-time ±20% weight scenarios, Top-3/Top-5 appearance counts, and the Slope-only baseline/rank comparison.

The display score is \`100 / (1 + weighted_distance)\`. It is a monotonic relative ranking index on the configured tolerance scale, not a probability, physical-equivalence percentage, mission-success estimate, or site certification.

## Validation and limitations

- Run \`python -m pytest -q\` after changes.
- CI also compiles \`src\` and \`tests\` before running the full test suite.
- Synthetic tests validate code behavior only; they are not scientific site results.
- Weight sensitivity counts are descriptive counts, not probabilities.
- Slope, TRI, and Terrain Distribution may be correlated; assess double-counting with the real fingerprints.
- Current code reports direct-observation support when supplied but does not propagate the RMS uncertainty layers into the score.
- A* routing is not part of this CSV-to-ranking workflow and must be treated as a separate, explicitly modeled extension.
