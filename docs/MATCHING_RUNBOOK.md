# AREA 67 — Omar matching workflow runbook

## What this workflow consumes

The matching engine consumes **terrain fingerprints**, not raw DEM files. Ghassan prepares documented raster data and source metadata; Hiba derives the five fingerprint groups. Omar's workflow then compares one Moon/Mars target against Earth candidates.

Input file:

- `data/processed/terrain_fingerprints.csv`

The loader expects at least `site_id` and `planet`. The matcher additionally needs the fields and method metadata documented in `MATCHING_METHOD.md`. Missing values remain missing; they are not changed to zero.

## Before running on team data

1. Confirm the target area and mission profile with the team. The current MVP target is NASA PGDA Site01 / Connecting Ridge. Site04 (Shackleton rim) is a LOLA QA/comparator, not a second ranked target. Neither provider ROI set is an approved AREA 67 study AOI.
2. Confirm that the fingerprint CSV includes exactly one row for the chosen target site and Earth rows for candidate sites.
3. Confirm that all rows use a comparable, documented `analysis_scale_m`.
4. Confirm the exact units and method metadata: slope units, elevation units, TRI definition/window, relief physical window, terrain-class thresholds, and spatial-pattern definition/connectivity.
5. Ask the feature/data owners to confirm that TRI values are expressed in the declared elevation unit.
6. Agree explicit per-feature tolerances with the team. The tolerance values define the distance scale and therefore directly affect ranks and display scores. They are **not** automatically derived from the input sample and are not official NASA or rover specifications.
7. Review NoData, direct instrument support, and uncertainty separately. A valid raster mask is not the same as direct instrument observation.

For context only, the Site04 whole-raster GIS audit reports 9.1541% positive LOLA spot-count support. The current Site01 pilot window reports 9.235% positive LDEC support. These are direct-observation support measures and must not be confused with `valid_coverage_pct` or `nodata_pct`.

## Current exploratory pilot (not a final Omar sign-off)

The committed `candidate_rankings.csv` and `ranking_robustness.json` describe an exploratory comparison of four provisional reference-centred windows: Site01 plus Haughton, Yungay, and Mauna Kea. Askja is held out because its sampled window is near-flat/equal-elevation. The current pilot uses the provisional tolerances in `config/matching_tolerances.exploratory.json`, the prototype mission weights, a 1.0 minimum feature-group completeness, and a 0.95 minimum data-completeness gate. These values reproduce a software pilot only; they are not team-approved scientific settings.

To rerun without overwriting the app-facing pilot outputs, write to separate filenames:

```powershell
python -m src.matching.cli --fingerprints data/processed/terrain_fingerprints.csv --target-site-id MOON_SITE01_PILOT990 --candidate-site-ids EARTH_HAUGHTON_REF990 EARTH_YUNGAY_HYPERARID_REF990 EARTH_MAUNAKEA_REF990 --tolerances-json config/matching_tolerances.exploratory.json --min-feature-group-completeness 1.0 --min-data-completeness 0.95 --output data/processed/omar_pilot_rankings.recomputed.csv --robustness-output data/processed/omar_pilot_robustness.recomputed.json
```

The run must still be labelled `EXPLORATORY_NOT_APPROVED`. Do not replace the canonical output pair or remove the application warning on the basis of this pilot rerun.

## Configure feature tolerances

Copy the blank template:

PowerShell:

```powershell
Copy-Item config/matching_tolerances.template.json config/matching_tolerances.json
```

Edit `config/matching_tolerances.json` and replace every `null` with a positive number approved for the study:

| Key | Units |
|---|---|
| `slope_deg` | degrees |
| `tri_m` | metres of TRI |
| `local_relief_m` | metres of local relief |
| `terrain_distribution_pp` | percentage points |
| `spatial_pattern_pct` | percentage points for largest steep-patch area |

If the fingerprint table uses `spatial_pattern_metric` instead of `largest_steep_patch_pct`, use a key called `spatial_pattern_metric` instead, with units appropriate to that documented metric. Do not use the percentage tolerance for an arbitrary metric.

The JSON file with team-approved tolerances should be retained with the analysis record. Do not overwrite the blank template.

## Run the matching workflow

From the repository root, with the project environment active:

```powershell
python -m src.matching.cli --fingerprints data/processed/terrain_fingerprints.csv --target-site-id MOON_SITE01_PILOT990 --tolerances-json config/matching_tolerances.json --min-feature-group-completeness <TEAM_APPROVED_FRACTION> --min-data-completeness <TEAM_APPROVED_FRACTION>
```

Replace `MOON_SITE01_PILOT990` with the exact target `site_id` from the approved canonical fingerprint CSV. The current identifier is explicitly a pilot-window ID, not an approved AOI ID.

**Required completeness policy:** replace both `<TEAM_APPROVED_FRACTION>` placeholders with values the team has explicitly approved for this study. The first sets the minimum fraction of mission weight represented by available feature groups; the second sets the minimum conservative data-completeness fraction. The CLI refuses to run when either is omitted. Even `0.0` must be an explicit decision; it is not a recommended scientific threshold.

Optional software safeguard:

- `--scale-relative-tolerance 0.01` sets the allowed relative difference in `analysis_scale_m`. The default 1% is a software default, not a universal physical rule.

If a candidate has incompatible method definitions or spatial scales, it is reported in `rejected_candidates` with a reason. A group whose required method metadata or metric is absent is reported as missing and excluded; it is not imputed as zero.

## Outputs

The workflow writes:

- `data/processed/candidate_rankings.csv` — app-facing results with `target_site_id`, `candidate_site_id`, `mission_profile`, `rank`, `similarity_score`, `weighted_distance`, feature contributions, completeness, and method/quality context.
- `data/processed/ranking_robustness.json` — one-at-a-time weight scenarios, Top-3/Top-5 appearance counts, the Slope-only baseline/rank comparison, and a `matching_configuration` block recording the exact feature/data completeness cutoffs, scale-relative tolerance, terrain-distribution sum tolerance, weight perturbation, and Top-K values used. Keep this sidecar with the ranking CSV; together they preserve the run settings needed to audit the result.

The display score is `100 / (1 + weighted_distance)`. It is a monotonic relative ranking index on the configured tolerance scale, not a probability, physical-equivalence percentage, mission-success estimate, or site certification.

## Validation and limitations

- Run `python -m pytest -q` after changes.
- CI also compiles `src` and `tests` before running the full test suite.
- Synthetic tests validate code behavior only; they are not scientific site results.
- Weight sensitivity counts are descriptive counts, not probabilities.
- Slope, TRI, and Terrain Distribution may be correlated; assess double-counting with the real fingerprints.
- Current code reports direct-observation support when supplied but does not propagate the RMS uncertainty layers into the score.
- A* routing is not part of this CSV-to-ranking workflow and must be treated as a separate, explicitly modeled extension.


## Tolerance sensitivity

Every matching workflow now records tolerance sensitivity in `data/processed/ranking_robustness.json`: one baseline plus one-at-a-time 0.5× and 1.5× changes for each feature tolerance. All other tolerances, weights, completeness gates, and fingerprint inputs are held fixed. The output records per-scenario ranks, Top-1/Top-3/Top-5 appearance counts, and rejection reasons. These are descriptive sensitivity results, not probabilities, confidence intervals, or a method for choosing scientifically valid tolerances automatically.


## Explicit candidate scope

Every CSV-driven CLI run requires `--candidate-site-ids`. This is an allowlist: only the named Earth rows are eligible, and any requested ID missing from the CSV or not labelled Earth causes a clear error. For the frozen canonical MVP, pass the exact approved Haughton, Askja, and Mauna Kea IDs supplied by the GIS/fingerprint handoff. Do not copy the exploratory Yungay ID into the canonical run. The exploratory reproduction test passes its historical Haughton/Yungay/Mauna Kea IDs explicitly to preserve reproducibility without changing the canonical shortlist.


## Reproducibility hashes and exclusions

The robustness JSON records the exact fingerprint CSV SHA-256, the exact tolerance JSON file SHA-256 when invoked through the CLI, and a canonical semantic configuration SHA-256 covering target, candidate allowlist, mission profile, weights, tolerances, completeness cutoffs, scale/distribution safeguards, and weight perturbation. It also lists the requested candidate IDs, ranked IDs, and baseline rejection reasons. Preserve the input CSV and tolerance JSON alongside the sidecar; a hash identifies bytes/configuration but does not itself establish scientific validity.
