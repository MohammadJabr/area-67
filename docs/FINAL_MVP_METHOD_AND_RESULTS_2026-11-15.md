# AREA 67 exploratory MVP - method and results

**Release status: PRESENTATION-READY EXPLORATORY SOFTWARE MVP; NOT A SCIENTIFICALLY APPROVED SITE RANKING.**

Here, "final MVP" means the deliberately reduced demo scope. It does not mean AOIs, scale, matching settings, or site suitability have been approved.

## Scope and target

The MVP uses NASA PGDA LOLA **Site01 / Connecting Ridge** as its one lunar target. This is the current project baseline because the repository science decision identifies Site01 as the illumination/SDEM evidence anchor: NASA Product 78 reports a high-illumination context and Product 104 provides the A306 SDEM context. This is a scope choice grounded in those separate evidence sources, not a claim that Site01 is the best lunar base location. Site04 is excluded from the ranking: its separate exploratory run uses a provisional operational window, has unresolved physical lunar frame provenance, and reports only 8.292% direct support for that run. These runs are not a like-for-like target comparison.

The target row, `MOON_SITE01_PILOT990`, is a 990 m square context window. Its provider-ROI-union overlap diagnostic is 3.8657%; it is not the provider ROI or an approved geomorphic AOI.

## Earth comparison set

The reduced tracked comparison contains three 990 m reference-centered Copernicus GLO-30 windows: Haughton, Yungay, and Mauna Kea. The common source family and existing complete fingerprints make them usable for this engineering demo. They are provisional sample windows, not approved geomorphic AOIs. Askja is held out because its current reference-centered diagnostic window is dominated by near-flat/equal-elevation samples; that is not a finding about all Askja terrain. McMurdo is not in this ranked set. Yungay's reference marker differs from a published field reference by about 5.81 km, so its identity remains a material caveat.

The current feature set reuses the existing canonical five groups: Slope, Riley 8-neighbor TRI, moving-window Local Relief, Terrain Distribution, and Spatial Pattern. No feature algorithm is added here. The method's provisional 30 m grid, requested 150 m relief window (five cells; 120 m center-to-center span), class thresholds, weights, tolerances, and completeness settings remain experiment assumptions, not team-approved scientific policies. The existing Slope-only result is retained as a diagnostic baseline. A one-at-a-time feature-tolerance sensitivity check (baseline plus 0.5× and 1.5× for each of the five tolerances) was also run on these same tracked exploratory fingerprints: Haughton remained rank 1 in 11/11 scenarios, Yungay rank 2 in 11/11, and Mauna Kea rank 3 in 11/11. This checks numerical ranking sensitivity only; it does not validate the provisional tolerance values or the candidate identities.

## Existing app-facing results

These values are read from `data/processed/candidate_rankings.csv`; this documentation change does not regenerate or overwrite them.

| Rank | Earth reference window | Relative similarity index | Weighted distance | Weight Top-1 / Top-2 scenarios | Tolerance Top-1 scenarios |
|---:|---|---:|---:|---|---|
| 1 | Haughton | 73.7870 | 0.3552523 | Top-1 11/11; Top-2 11/11 | 11/11 |
| 2 | Yungay | 66.1325 | 0.5121164 | Top-1 0/11; Top-2 11/11 | 0/11 |
| 3 | Mauna Kea | 27.3897 | 2.6510027 | Top-1 0/11; Top-2 0/11 | 0/11 |

The tolerance Top-1 counts above are computed from the 11 per-scenario rank records in the robustness sidecar. They indicate that the order is stable under the tested numerical perturbations, not that the candidates or tolerances are scientifically validated. The Slope-only baseline ranks the same three windows in the same order (scores 64.9452, 56.7559, and 22.0970). This small pilot does not show that using the additional groups improves predictive validity. Feature contributions are available in the ranking CSV and appear in the Results & Comparison view. Scores and sensitivity counts are relative method outputs, not probabilities, physical-equivalence percentages, mission-success estimates, safety assessments, or suitability certification.

## Data and limitations

- Lunar source: NASA PGDA Product 78 Site01 LOLA elevation and native LDEC, total-error, and slope-error companions. The pilot reports **9.235% positive LDEC support** in its context window, separately from 100% valid elevation-mask coverage. Zero-count/interpolated cells are not direct shots and are not NoData.
- Product 90 bounded inspection reports Site01 EFFRES P50 15.78 m and P90 24.08 m. Native 5 m posting is not effective resolution.
- Earth source: Copernicus DEM GLO-30 DSM windows; product documentation identifies EGM2008 metres. The source family is consistent across these three windows, but effective terrain resolution was not independently established and no per-pixel quality companions were retrieved.
- No absolute lunar-to-Earth elevation comparison is made. The lunar local datum/physical frame and provider ROI shapefile frame remain unresolved; no guessed frame shift is applied.
- All footprints and analytical settings remain provisional. Earth gravity, atmosphere, radiation, vacuum, and surface-condition differences are outside this terrain-only comparison.

## Implementation and reproduction

The integrated builder in `src/data/build_exploratory_pilot.py` calls the canonical `calculate_terrain_fingerprint`, `rank_terrain_fingerprints`, and `run_matching_robustness` implementations. It records source/output checksums, processing grids, windows, and the run configuration. The normal output pair used by the app is already committed at `data/processed/terrain_fingerprints.csv` and `data/processed/candidate_rankings.csv`.

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

The builder fails if any configured raster or required Site01 quality layer is missing. This workstation checkout does not currently contain `data/raw/moon/site01/`; therefore the raw-raster rebuild was not run here. The documented manual acquisition workflow is `.github/workflows/gis-data-acquisition.yml` (`workflow_dispatch`, dataset `both`), and acquisition artifacts must be kept outside Git. The launch command uses the checked-in result pair and does not need raw rasters.

## Release gates still open

Team approval is still needed for the actual lunar and Earth geomorphic AOIs, common analysis scale and grid/mask policy, vertical/coordinate-frame treatment, quality policy, and matching weights/tolerances/completeness. Hiba's independent scientific validation and Omar's review of the matching configuration remain needed before promoting this exploratory demonstration to a validated result. Do not hide the app's exploratory warning.
