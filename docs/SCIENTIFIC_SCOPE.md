# Initial Scientific Scope

## Prototype question
For one selected lunar or Martian target and one explicit exploration task, which small set of Earth candidate areas most closely matches the target in the topographic characteristics that matter to that task?

## Core terrain fingerprint
1. **Slope:** distribution statistics of slope angle, not only a mean.
2. **Ruggedness / TRI:** local elevation variation using a documented TRI definition and neighborhood scale.
3. **Local relief:** local elevation range or robust percentile range within a documented window.
4. **Terrain distribution:** area fractions in explicitly defined slope/terrain classes.
5. **Spatial pattern:** at least one documented spatial metric, such as connected-patch statistics or spatial autocorrelation.

## Scientific safeguards
- Use comparable physical analysis scales. Resampling does not create new information.
- Record horizontal CRS, pixel size, vertical units and datum/reference, NoData handling, product version, and quality/uncertainty information.
- Do not directly compare raw absolute elevations across planetary bodies with different vertical references. Prefer local/relative terrain descriptors for cross-body matching.
- TRI, slope, and local relief depend on resolution and neighborhood/window size. Record these parameters and run a scale-sensitivity check.
- Terrain Distribution partly derives from slope. Avoid double-counting by grouping features or testing feature ablations/correlation.
- A similarity score is a relative ranking under chosen features and weights, not a probability of success or complete environmental equivalence.
- A location absent from a consulted catalog is only a candidate not represented in that reviewed catalog; absence is not proof of global novelty.
- A DEM does not establish soil strength, rock size, mineralogy, temperature, radiation, atmospheric conditions, or subsurface cavities.

## Minimum validation
1. Synthetic-surface unit tests for slope, TRI, and relief.
2. Comparison with an authoritative derived product where compatible products exist.
3. Resolution/window sensitivity analysis.
4. Weight sensitivity analysis for candidate ranking.
5. Source and quality metadata included in every candidate result.

## Initial output
An evidence-based candidate ranking and an initial Analog Passport for each tested Earth area, explicitly listing similarities, differences, data quality, assumptions, and limitations.
