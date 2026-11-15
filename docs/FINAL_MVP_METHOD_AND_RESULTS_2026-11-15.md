# AREA 67 exploratory MVP - method and results

**Release status: PRESENTATION-READY EXPLORATORY SOFTWARE MVP; NOT A SCIENTIFICALLY APPROVED SITE RANKING.**

Here, "final MVP" means the deliberately reduced demo scope. It does not mean AOIs, scale, matching settings, or site suitability have been approved.

## Scope and target

The MVP uses NASA PGDA LOLA **Site01 / Connecting Ridge** as its one lunar target. This is the current project baseline because the repository science decision identifies Site01 as the illumination/SDEM evidence anchor: NASA Product 78 reports a high-illumination context and Product 104 provides the A306 SDEM context. This is a scope choice grounded in those separate evidence sources, not a claim that Site01 is the best lunar base location. Site04 is excluded from the ranking: its separate exploratory run uses a provisional operational window, has unresolved physical lunar frame provenance, and reports only 8.292% direct support for that run. These runs are not a like-for-like target comparison.

The target row, `MOON_SITE01_PILOT990`, is a 990 m square context window. Its provider-ROI-union overlap diagnostic is 3.8657%; it is not the provider ROI or an approved geomorphic AOI.

## Earth comparison set

The reduced tracked comparison contains three 990 m reference-centered Copernicus GLO-30 windows: Haughton, Yungay, and Mauna Kea. The common source family and existing complete fingerprints make them usable for this engineering demo. They are provisional sample windows, not approved geomorphic AOIs. Askja is held out because its current reference-centered diagnostic window is dominated by near-flat/equal-elevation samples; that is not a finding about all Askja terrain. McMurdo is not in this ranked set. Yungay's reference marker differs from a published field reference by about 5.81 km, so its identity remains a material caveat.

The reduced demo ranking uses the existing canonical matcher **Slope-only baseline**, based on Slope P50 and P90. This is the smallest already-computed feature subset and introduces no new feature or matching algorithm. The curated fingerprint CSV retains the full supplied five-group rows for provenance/context, but non-Slope groups do not contribute to these rankings. The full five-group result remains unchanged in its original files as a separate exploratory comparison.

A separate one-at-a-time feature-tolerance sensitivity check was run for the existing five-group ranking (baseline plus 0.5x and 1.5x for each of its five tolerances): Haughton remained rank 1 in 11/11 scenarios, Yungay rank 2 in 11/11, and Mauna Kea rank 3 in 11/11. This is not sensitivity analysis for the active Slope-only package and does not validate the provisional tolerance values or candidate identities.

The source run's provisional 30 m grid, requested 150 m relief window (five cells; 120 m center-to-center span), class thresholds, multi-feature weights, tolerances, and completeness settings remain experiment assumptions, not team-approved scientific policies. No sensitivity scenarios were run for the Slope-only baseline.
## Existing app-facing results

These values are from `data/processed/exploratory_mvp_2026-11-15_v2/candidate_rankings.csv`, packaged from the current canonical matcher's Slope-only baseline. The original five-group scores remain unchanged in `data/processed/candidate_rankings.csv`. The earlier `exploratory_mvp_2026-11-15/` package is retained as a snapshot of the prior source sidecar; the app defaults to v2.

| Rank | Earth reference window | Slope-only relative index | Slope-group distance | Prior five-group rank |
|---:|---|---:|---:|---:|
| 1 | Haughton | 64.9452 | 0.5397594 | 1 |
| 2 | Yungay | 56.7559 | 0.7619318 | 2 |
| 3 | Mauna Kea | 22.0970 | 3.5255036 | 3 |

The prior five-group ordering is the same, but this is a descriptive result for these windows, not evidence that either feature set predicts analog usefulness. The app displays the supplied Slope-group distance and the target/candidate Slope values; it does not create new feature contributions. Scores are relative method outputs, not probabilities, physical-equivalence percentages, mission-success estimates, safety assessments, or suitability certification.

## Data and limitations

- Lunar source: NASA PGDA Product 78 Site01 LOLA elevation and native LDEC, total-error, and slope-error companions. The pilot reports **9.235% positive LDEC support** in its context window, separately from 100% valid elevation-mask coverage. Zero-count/interpolated cells are not direct shots and are not NoData.
- Product 90 bounded inspection reports Site01 EFFRES P50 15.78 m and P90 24.08 m. Native 5 m posting is not effective resolution.
- Earth source: Copernicus DEM GLO-30 DSM windows; product documentation identifies EGM2008 metres. The source family is consistent across these three windows, but effective terrain resolution was not independently established and no per-pixel quality companions were retrieved.
- No absolute lunar-to-Earth elevation comparison is made. The lunar local datum/physical frame and provider ROI shapefile frame remain unresolved; no guessed frame shift is applied.
- All footprints and analytical settings remain provisional. Earth gravity, atmosphere, radiation, vacuum, and surface-condition differences are outside this terrain-only comparison.

## Implementation and reproduction

The integrated builder in `src/data/build_exploratory_pilot.py` calls the canonical `calculate_terrain_fingerprint`, `rank_terrain_fingerprints`, and `run_matching_robustness` implementations. `src/data/package_reduced_mvp.py` then selects the existing Slope-only baseline and the one-target/three-candidate rows into `data/processed/exploratory_mvp_2026-11-15_v2/`; it does not calculate fingerprints or rankings. Its manifest records source and package checksums. The original full five-group outputs remain unchanged at the top level of `data/processed/`.

Install the repository dependencies and launch the app from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app/main.py
```

To rebuild from locally acquired Site01 plus the configured Earth source rasters without overwriting the tracked app-facing or historical outputs, use a new output location:

```powershell
python -m src.data.build_exploratory_pilot `
  --raw-root data/raw `
  --output-dir outputs/final_mvp_rebuild_2026-11-15 `
  --metadata-dir outputs/final_mvp_rebuild_2026-11-15_metadata `
  --config config/exploratory_pilot_2026-11-15.json
```

Package the Slope-only baseline from that rebuild into a fresh directory, then launch the app against it:

```powershell
python -m src.data.package_reduced_mvp `
  --fingerprints outputs/final_mvp_rebuild_2026-11-15/terrain_fingerprints.csv `
  --rankings outputs/final_mvp_rebuild_2026-11-15/candidate_rankings.csv `
  --robustness outputs/final_mvp_rebuild_2026-11-15/ranking_robustness.json `
  --output-dir outputs/final_mvp_package_rebuild_2026-11-15
$env:AREA67_MVP_DATA_DIR = "outputs/final_mvp_package_rebuild_2026-11-15"
streamlit run app/main.py
```

The package command refuses an existing output path. Choose a new directory for each rebuild so prior outputs remain intact.

The builder fails if any configured raster or required Site01 quality layer is missing. This workstation checkout does not currently contain `data/raw/moon/site01/`; therefore the raw-raster rebuild was not run here. The documented manual acquisition workflow is `.github/workflows/gis-data-acquisition.yml` (`workflow_dispatch`, dataset `both`), and acquisition artifacts must be kept outside Git. The default launch uses the checked-in reduced package and does not need raw rasters. To point the app at a newly rebuilt package, set `AREA67_MVP_DATA_DIR` to that package directory before launching.

## Release gates still open

Team approval is still needed for the actual lunar and Earth geomorphic AOIs, common analysis scale and grid/mask policy, vertical/coordinate-frame treatment, quality policy, and matching weights/tolerances/completeness. Hiba's independent scientific validation and Omar's review of the matching configuration remain needed before promoting this exploratory demonstration to a validated result. Do not hide the app's exploratory warning.
