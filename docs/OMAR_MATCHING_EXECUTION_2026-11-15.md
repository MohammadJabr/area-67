# Omar matching execution record — 2026-11-15

## Status

**EXPLORATORY PILOT REPRODUCTION ONLY — NOT A FINAL SCIENTIFIC RANKING.**

This record makes the currently committed pilot comparison reproducible without presenting provisional values as team-approved settings or overwriting the app-facing files.

## Inputs inspected

- Fingerprint input: `data/processed/terrain_fingerprints.csv`
- Target row: `MOON_SITE01_PILOT990` (NASA PGDA Site01 / Connecting Ridge; a 990 m × 990 m reference-centred sampling window, not an approved AOI)
- Earth rows:
  - `EARTH_HAUGHTON_REF990`
  - `EARTH_YUNGAY_HYPERARID_REF990`
  - `EARTH_MAUNAKEA_REF990`
- Askja is held out because its selected reference-centred window is dominated by near-flat/equal-elevation samples pending selection of a named caldera/lava/lake-margin landform.
- Site04 is a LOLA QA/comparator and is not a second ranked MVP target.

## Explicit pilot configuration

- Mission profile: Rover Navigation / Terrain Traversal.
- Weights: Slope 0.30, TRI 0.25, Local Relief 0.20, Spatial Pattern 0.20, Terrain Distribution 0.05.
- Tolerances: slope 5°, TRI 10 m, Local Relief 15 m, Terrain Distribution 20 percentage points, Spatial Pattern 15 percentage points.
- Minimum feature-group completeness: 1.00.
- Minimum data completeness: 0.95.
- Scale-relative tolerance: 0.01 (software safeguard).
- Distribution-sum tolerance: 0.5 percentage points.
- Weight sensitivity: one-at-a-time ±20%, with weights renormalized.

Every number above is a **provisional pilot assumption**. None is represented as a NASA, rover-manufacturer, or team-approved scientific threshold. The values are stored in `config/matching_tolerances.exploratory.json`; the blank `matching_tolerances.template.json` remains untouched.

## Existing exploratory output snapshot

The committed pilot output currently reports:

| Rank | Candidate | Similarity index | Weighted distance |
|---:|---|---:|---:|
| 1 | Haughton | 73.7870 | 0.3552523 |
| 2 | Yungay | 66.1325 | 0.5121164 |
| 3 | Mauna Kea | 27.3897 | 2.6510027 |

These are relative scores from the current pilot windows, not probabilities, physical-equivalence percentages, mission-success estimates, safety assessments, or site certifications. The first candidate remains top-1 in 11/11 tested one-at-a-time weight scenarios; that count is descriptive, not a confidence level.

## Reproduction command

Run from the repository root in the project environment:

```powershell
python -m src.matching.cli --fingerprints data/processed/terrain_fingerprints.csv --target-site-id MOON_SITE01_PILOT990 --tolerances-json config/matching_tolerances.exploratory.json --min-feature-group-completeness 1.0 --min-data-completeness 0.95 --output data/processed/omar_pilot_rankings.recomputed.csv --robustness-output data/processed/omar_pilot_robustness.recomputed.json
```

The separate output names prevent this exploratory reproduction from overwriting the app-facing ranking pair. This repository change records the command and configuration; it does not claim that a local CLI execution was performed by this PR.

## Why this is not the final Omar run

The current fingerprint rows are explicitly marked `EXPLORATORY_NOT_APPROVED`. Their footprints are provisional reference-centred windows, not approved geomorphic AOIs. The 30 m analysis scale and 150 m relief window are provisional. Earth effective terrain resolution and per-pixel quality companions have not been established; lunar ROI shapefile frame and final AOI geometry remain unresolved. Direct LOLA support is reported separately from raster-valid coverage. Absolute cross-body elevation is not compared.

A final ranking requires:
1. Ghassan/team approval of the target and named Earth geomorphic AOIs, with stable IDs and source-backed geometries.
2. A common analysis grid/scale/window and documented mask/NoData policy.
3. Hiba's canonical five-group fingerprints from those approved AOIs, with quality and uncertainty summaries.
4. Omar/team approval of all five tolerances and both completeness cutoffs for the selected mission profile.
5. A fresh canonical matcher run, review of exclusions/contributions, Slope-only baseline, and sensitivity outputs.
6. Mohammed's application integration check against the exact target/candidate IDs and paired output files.

Until those gates pass, keep the app's exploratory warning visible and do not describe this ranking as final.


## 2026-11-15 tolerance-sensitivity refresh

The app-facing pilot outputs were refreshed with a matching-only sensitivity calculation over the currently tracked exploratory fingerprint rows. The baseline calculation was independently checked against the committed weighted distances (maximum absolute difference below (5\times10^{-16})). One tolerance at a time was changed to 0.5× and 1.5× for all five groups, giving 11 scenarios including baseline.

| Candidate window | Baseline rank | Top-1 across tolerance scenarios | Rank across all 11 scenarios |
|---|---:|---:|---|
| Haughton | 1 | 11/11 | 1 in all scenarios |
| Yungay | 2 | 0/11 | 2 in all scenarios |
| Mauna Kea | 3 | 0/11 | 3 in all scenarios |

This is a deterministic sensitivity check on the existing exploratory feature measurements. It is not a confidence interval, probability, tolerance validation, AOI approval, or scientific certification. The ranking remains Haughton/Yungay/Mauna Kea reference-window pilot data; it does not replace the frozen Haughton/Askja/Mauna Kea canonical shortlist. No DEM extraction or raster processing was rerun by this matching-only refresh.

The refreshed `ranking_robustness.json` records the tolerance scenarios, candidate/ranked IDs, the fingerprint/config Git blob identifiers, and source-raster checksum inventory. The builder code in PR #106 has also been updated so future raw-raster rebuilds emit the same sensitivity section automatically.
