# AREA 67 matching method — current implementation

## Scope and status

The matching workstream now has two layers:

1. Convert a pair of target/candidate terrain fingerprints into five group distances.
2. Aggregate those group distances with the selected mission profile, rank Earth candidates, and export the application contract.

This is a tested implementation using synthetic fixtures. It is **not yet a validated Earth–Moon or Earth–Mars result**. Real Earth candidate fingerprints, approved analysis scales, team-approved tolerances, and an end-to-end run remain required.

The active MVP direction is **Space-to-Earth**: one Moon/Mars target and Earth candidates. The initial profile is **Rover Navigation / Terrain Traversal**.

## Inputs and comparability safeguards

The matcher consumes the canonical terrain fingerprint fields described in `docs/INTEGRATION_CONTRACT.md`:

- `site_id`, `planet`, `source_id`, `analysis_scale_m`, `slope_unit`, `elevation_unit`, `nodata_pct`
- Slope: `slope_median`, `slope_p90`
- TRI: `tri_median`, `tri_p90`, `tri_definition`, `tri_window_cells`
- Local relief: `local_relief_p95_p5`, `relief_window_m`
- Terrain distribution: one complete class set (`terrain_low_pct`, `terrain_mid_pct`, `terrain_high_pct` or `terrain_flat_pct`, `terrain_moderate_pct`, `terrain_steep_pct`) plus `terrain_class_thresholds`
- Spatial pattern: the same statistic on both sites (`largest_steep_patch_pct` or `spatial_pattern_metric`) plus `spatial_pattern_definition`

Known method conflicts are rejected. If method metadata required to interpret a group is absent, that group is reported as missing and is not compared. Low/mid/high class labels are not silently reinterpreted as flat/moderate/steep. A generic spatial-pattern metric is not treated as interchangeable with largest connected steep-patch percentage.

The default analysis-scale relative tolerance is 1%. This is a configurable engineering check, not a universal scientific standard. A team may require exact equality or choose another documented threshold after reviewing the datasets.

Slope values are converted to degrees from supported degree/radian units. TRI and local-relief values are converted to metres using each fingerprint's `elevation_unit`; the implementation assumes TRI is expressed in the elevation unit. The feature producer must confirm this before real-data use.

## Feature-group distances

All tolerances are explicit function inputs; the implementation does not silently invent scientific thresholds. Tolerances must be positive and are expressed in the units named below.

| Group | Inputs compared | Distance calculation | Tolerance key |
|---|---|---|---|
| Slope | Median and P90 | RMS of the two absolute differences after conversion to degrees | `slope_deg` |
| TRI | Median and P90, only when definition and neighbourhood match | RMS of the two absolute differences after conversion to metres | `tri_m` |
| Local relief | P95–P5, only when physical window matches | Absolute difference after conversion to metres | `local_relief_m` |
| Terrain distribution | The same three class percentages and same declared thresholds | RMS of class percentage-point differences | `terrain_distribution_pp` |
| Spatial pattern | Same statistic and documented definition | Absolute difference; percentage points for largest steep-patch share | `spatial_pattern_pct` or `spatial_pattern_metric` |

Each difference is divided by its declared tolerance. Group distances are therefore measured in **tolerance units**, may exceed 1, and are not probabilities or automatically bounded normalized scores. Example test tolerances are illustrative only and must not be presented as approved project parameters.

A complete terrain distribution must have values in [0, 100] and sum to 100 within the configured percentage-point tolerance. Slope degrees must be in [0, 90]. TRI and local relief must be non-negative. Non-finite values are rejected.

## Weighted aggregation, completeness, and explainability

The initial mission weights are operational hypotheses, not NASA or rover-manufacturer specifications:

| Feature group | Weight |
|---|---:|
| Slope | 0.30 |
| TRI | 0.25 |
| Local relief | 0.20 |
| Spatial pattern | 0.20 |
| Terrain distribution | 0.05 |

For the available, valid, positive-weight groups A:

\[
D(x,t)=\sqrt{\frac{\sum_{g\in A}w_gd_g(x,t)^2}{\sum_{g\in A}w_g}}
\]

- Missing groups are excluded; they are never filled with zero.
- Remaining active weights are renormalized.
- `feature_group_completeness` is the available positive mission weight divided by total configured positive weight.
- `valid_raster_coverage_completeness` is the lower valid-pixel coverage of the target and candidate, derived from `nodata_pct`.
- `data_completeness` is the conservative minimum of those two completeness measures.

Valid raster coverage must not be confused with direct instrument support. For the provisional NASA LOLA Site04 handoff, the GIS QA reports that 9.1541% of valid cells have positive LOLA spot counts while 90.8459% have zero counts and interpolated elevation. The valid mask alone does not establish direct observation. When `direct_observation_coverage_pct` is supplied, it is reported separately; it is not currently used as a score weight. RMS uncertainty layers are also not yet propagated into the matching distance.

For each available feature group the matcher reports `group_distance`, `weight`, `weighted_squared_contribution`, and `distance_share`. The CSV contribution columns are shares of weighted squared distance; they are not the feature weights, raw feature differences, or similarity probabilities.

## Similarity score and ranking

The display score is:

\[
S=\frac{100}{1+D}
\]

It is a monotonic index from 0 to 100 for the current tolerance-scaled distance definition. It is not a percentage of physical equivalence, probability of mission success, or site-suitability certification. Changing the feature tolerances changes the numerical score.

Candidates are sorted by ascending weighted distance. Ties are resolved by `site_id`. Invalid or incomparable candidates are listed in `rejected_candidates` with a reason; they are not assigned artificial rankings.

## Baseline and sensitivity

- The Slope-only baseline ranks the same accepted candidates using only the Slope group. Rank changes are descriptive and help show whether adding other groups changes the ordering.
- Weight sensitivity runs the baseline profile plus one-at-a-time ±20% perturbations for each group, renormalizing weights after each change. Five groups produce 11 scenarios.
- Tolerance sensitivity runs one baseline plus one-at-a-time 0.5× and 1.5× perturbations for each declared feature tolerance, holding all other tolerances, weights, completeness gates, and fingerprints fixed. With five tolerance keys this produces 11 scenarios. Rank/Top-K changes and rejection reasons are recorded; counts are descriptive, not probabilities.
- Top-3/Top-5 appearances are reported as counts across tested scenarios. They are not probabilities or confidence levels.
- Run these analyses on real candidate group distances before reporting scientific ranking stability.

## Application export

`src/reporting/ranking_export.py` exports `candidate_rankings.csv` using canonical fields required by the application:

`target_site_id, candidate_site_id, mission_profile, rank, similarity_score, weighted_distance`

It also includes feature-contribution shares, data-completeness fields, a ranking-stability note, and a note defining the score formula. The export uses the explicit target ID; it does not infer one from the candidate.

## Example pipeline call

The following is the intended API shape. The tolerance values below are **illustrative test values only**; the team must approve values appropriate to the selected data products and common physical scale.

```python
from src.matching.mission_profiles import get_mission_weights
from src.matching.pipeline import rank_terrain_fingerprints
from src.matching.sensitivity import run_matching_robustness
from src.reporting.ranking_export import export_rankings_csv

tolerances = {
    "slope_deg": 5.0,
    "tri_m": 2.0,
    "local_relief_m": 10.0,
    "terrain_distribution_pp": 10.0,
    "spatial_pattern_pct": 10.0,
}

ranking = rank_terrain_fingerprints(
    target_fingerprint=target_row,
    candidate_fingerprints=earth_candidate_rows,
    weights=get_mission_weights(),
    tolerances=tolerances,
    mission_profile="Rover Navigation / Terrain Traversal",
    min_feature_group_completeness=0.60,
)

robustness = run_matching_robustness(ranking, get_mission_weights())

export_rankings_csv(
    ranking,
    "Rover Navigation / Terrain Traversal",
    "data/processed/candidate_rankings.csv",
    ranking_stability_note="Populate from the actual sensitivity result.",
)
```

## Not yet implemented or validated

- Actual import, join, and provenance validation for Hiba's delivered fingerprint table.
- Team-approved tolerance values and a documented scientific basis for each tolerance.
- Propagation or explicit weighting of RMS uncertainty and direct-observation support.
- Correlation/double-counting analysis for Slope, TRI, and Terrain Distribution using real site features.
- Real Earth candidate DEMs and a measured Moon/Earth or Mars/Earth ranking.
- End-to-end app import and display using the produced CSV.
- External validation of mission weights against an engineering requirement.
- A* route planning over an agreed, analysis-ready candidate DEM.

Until these items are completed, this is a tested matching implementation and synthetic validation suite, not a validated planetary analog result.
