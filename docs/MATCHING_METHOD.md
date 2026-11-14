# AREA 67 matching method — current implementation

## Scope

The matcher currently ranks candidates from **already-computed, non-negative, comparable group distances**. It does not derive distances from raw target/candidate fingerprint values, select normalization ranges, or read DEMs. That upstream feature-to-distance step must be specified and validated before these utilities produce scientific Earth–Moon analog rankings.

The initial profile is **Rover Navigation / Terrain Traversal**. Its weights are prototype hypotheses, not NASA or rover-manufacturer specifications:

| Feature group | Weight |
|---|---:|
| Slope | 0.30 |
| TRI | 0.25 |
| Local relief | 0.20 |
| Spatial pattern | 0.20 |
| Terrain distribution | 0.05 |

The weights sum to 1.0. Slope and terrain distribution are correlated because distribution is derived from slope; the low distribution weight is an initial team choice, not a validated correction for dependence.

## Weighted distance and missing groups

For candidate (x) and target (t), with available feature-group distances (d_g(x,t)) and profile weights (w_g), the implementation calculates:

[
D(x,t)=\sqrt{\frac{\sum_{g\in A}w_gd_g(x,t)^2}{\sum_{g\in A}w_g}}
]

where (A) is the set of groups with a supplied, valid distance and a positive weight.

- Missing groups are excluded; their weights are not silently treated as zero.
- Remaining active weights are renormalized in the distance calculation.
- `data_completeness` is the available positive weight divided by the total configured weight.
- A caller may set `min_completeness` to reject candidates below an explicit coverage threshold.
- Candidate rows that fail validation are returned under `rejected_candidates` with a reason; they are not assigned an artificial score.

All supplied group distances must already be on documented, comparable scales. The matcher does not make unlike units comparable by itself.

## Contributions

For each available group, the matcher reports:

- `group_distance`: the supplied distance for that group.
- `weight`: its mission-profile weight.
- `weighted_squared_contribution`: its weighted squared-distance term after active-weight normalization.
- `distance_share`: that group's share of the total weighted squared-distance sum.

The CSV `*_contribution` columns export `distance_share`. These are relative shares of squared distance (they sum to 1 when total distance is non-zero), not feature differences, feature weights, or similarity probabilities.

## Ranking and export contract

Every exported ranking row includes:
`target_site_id, site_id, rank, mission_profile, similarity_distance, relative_similarity`.

`target_site_id` is mandatory and must be an explicit Moon/Mars target identifier; `site_id` is the Earth candidate identifier. The export also includes per-group contribution columns, `data_completeness`, and `ranking_stability_note`.

The relative similarity index is:

[
S=\frac{100}{1+D}
]

It is a monotonic display index for the current distance scale, not a probability of mission success and not a certification of site suitability. Changing the distance normalization changes the numerical index.

## Sensitivity and baseline

The weight-sensitivity utility runs the baseline profile and one-at-a-time ±20% perturbations for each group, renormalizing weights after each change. With five groups, it evaluates 11 scenarios. Top-3/Top-5 counts report how often a candidate appears in those scenario lists; counts are not probabilities.

The same call also reports a **slope-only baseline**. Compare the full-profile ordering and distances with this baseline to check whether the additional feature groups change the ordering. The current tests exercise deterministic synthetic fixtures only.

## Not yet implemented or validated

- Deriving per-group distances from Hiba's real terrain-fingerprint table.
- Selecting/justifying a common physical scale and a documented normalization/tolerance method for each metric.
- Quality/uncertainty-aware feature distances, including treatment of interpolated LOLA cells.
- A real target/candidate join and rankings from measured Moon and Earth data.
- Ranking stability from real candidates and an end-to-end app import of the exported CSV.
- Validation of the initial weights against a mission-specific external standard or engineering requirement.

Until those steps are completed, this is a tested **matching utility**, not a validated planetary analog result.
