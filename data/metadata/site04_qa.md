# NASA LOLA Site04 Raster QA

**Study area:** NASA LOLA Site04 (Shackleton rim) — Provisional working choice; not an officially approved team decision.

Catalog: https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/
Method reference: Barker et al. (2021), https://doi.org/10.1016/j.pss.2020.105119

## Executive QA results

- Dimensions: 3200 × 3200 pixels.
- Common valid coverage: 100.000000% (10,240,000 pixels).
- Identical GDAL masks: True; identical finite masks: True.
- Per-pixel direct LOLA support (LDEC > 0): 9.1541% of valid pixels.
- Valid zero-count/interpolated cells: 90.8459% of valid pixels.

## Product definitions and distributions

| Asset | Meaning and unit | Valid pixels | Min | Median | Mean | Max | Review flags |
|---|---|---:|---:|---:|---:|---:|---|
| `elevation` | m (surface height Z, per PGDA catalog) — LDEM surface-interpolated elevation | 10,240,000 | -2847.88 | 668.188 | 245.344 | 1805.07 | `{"exploratory_3iqr_review_only": 0}` |
| `counts` | LOLA spot count per pixel (dimensionless count) — LDEC | 10,240,000 | 0 | 0 | 0.0960853 | 5 | `{"negative_values": 0, "non_integer_values": 0}` |
| `slope` | degrees — Slope map | 10,240,000 | 0 | 20.5505 | 20.6641 | 69.6472 | `{"outside_0_to_90_degrees": 0}` |
| `z_uncertainty` | m RMS error (per PGDA catalog) — Total Z uncertainty | 10,240,000 | 0.0638568 | 0.359682 | 0.411665 | 7.6351 | `{"exploratory_3iqr_review_only": 88176, "negative_values": 0}` |
| `slope_uncertainty` | degrees RMS error (per PGDA catalog) — Slope uncertainty | 10,240,000 | 0.500015 | 1.49645 | 1.77078 | 28.143 | `{"exploratory_3iqr_review_only": 340478, "negative_values": 0}` |

### Observation support and uncertainty

LDEC is the number of LOLA spots binned per pixel. A positive LDEC denotes direct spot support; zero means no spot was binned and the elevation was interpolated. Thus valid-data coverage and observation coverage are different quantities.

| Support class | Pixels | Median Z RMS (m) | P95 Z RMS (m) |
|---|---:|---:|---:|
| LDEC > 0 | 937,381 | 0.35696 | 1.26246 |
| LDEC = 0 | 9,302,619 | 0.359821 | 0.777093 |

### NoData and non-finite pixels

| Asset | NoData-masked pixels | Non-finite band 1 pixels |
|---|---:|---:|
| `elevation` | 0 | 0 |
| `counts` | 0 | 0 |
| `slope` | 0 | 0 |
| `z_uncertainty` | 0 | 0 |
| `slope_uncertainty` | 0 | 0 |

### Lowest direct-support tiles

Tiles are 100×100 pixels (nominally 500 m × 500 m). Coordinates are centers in the dataset's south polar stereographic X/Y frame, meters. The lowest 12 tiles by percentage of pixels with LDEC > 0 are shown; this is a relative ranking, not a pass/fail threshold.

| Center X (m) | Center Y (m) | Positive-count pixels (%) | Zero-count pixels (%) | Median Z RMS (m) |
|---:|---:|---:|---:|---:|
| -2250.0 | -750.0 | 4.840 | 95.160 | 0.4624 |
| -4250.0 | -5250.0 | 5.010 | 94.990 | 0.4013 |
| -2750.0 | -1250.0 | 5.090 | 94.910 | 0.4411 |
| -3750.0 | -2250.0 | 5.090 | 94.910 | 0.4302 |
| -3250.0 | -1750.0 | 5.220 | 94.780 | 0.4106 |
| -2750.0 | -250.0 | 5.430 | 94.570 | 0.4409 |
| -4250.0 | 750.0 | 5.440 | 94.560 | 0.3806 |
| -1750.0 | -9250.0 | 5.560 | 94.440 | 0.4785 |
| -4250.0 | -5750.0 | 5.600 | 94.400 | 0.4106 |
| -3750.0 | -6250.0 | 5.620 | 94.380 | 0.374 |
| -3250.0 | -250.0 | 5.640 | 94.360 | 0.4198 |
| -4250.0 | -6750.0 | 5.700 | 94.300 | 0.3843 |

### Highest median elevation-uncertainty tiles

| Center X (m) | Center Y (m) | Median Z RMS (m) | P95 Z RMS (m) | Positive-count pixels (%) |
|---:|---:|---:|---:|---:|
| 6750.0 | 750.0 | 0.5754 | 1.365 | 8.060 |
| 5250.0 | 750.0 | 0.5669 | 1.341 | 6.990 |
| 1750.0 | -1750.0 | 0.5433 | 1.103 | 7.540 |
| 6750.0 | -14750.0 | 0.5411 | 1.523 | 7.340 |
| 750.0 | -1250.0 | 0.5396 | 1.111 | 7.390 |
| 1250.0 | -1250.0 | 0.5358 | 1.113 | 7.260 |
| 6250.0 | 750.0 | 0.5354 | 1.337 | 8.880 |
| 3250.0 | -1750.0 | 0.5306 | 0.9925 | 6.870 |
| 2750.0 | -750.0 | 0.5278 | 0.9394 | 5.870 |
| 4250.0 | 750.0 | 0.5261 | 1.497 | 7.530 |
| 6250.0 | 250.0 | 0.5257 | 0.9488 | 8.210 |
| 6750.0 | -750.0 | 0.5242 | 0.98 | 8.330 |

### Highest median slope-uncertainty tiles

| Center X (m) | Center Y (m) | Median slope RMS (degrees) | Positive-count pixels (%) |
|---:|---:|---:|---:|
| 3250.0 | -13250.0 | 1.945 | 14.420 |
| 4750.0 | -14750.0 | 1.922 | 12.430 |
| 5250.0 | -14750.0 | 1.914 | 10.900 |
| 3750.0 | -13250.0 | 1.9 | 13.060 |
| 6250.0 | -12750.0 | 1.892 | 14.220 |
| 2750.0 | -13250.0 | 1.877 | 15.010 |
| 2250.0 | -13250.0 | 1.877 | 15.120 |
| 5250.0 | -13750.0 | 1.874 | 13.390 |
| 5750.0 | -12750.0 | 1.864 | 13.650 |
| 6750.0 | -12750.0 | 1.855 | 13.520 |
| 6250.0 | -14250.0 | 1.836 | 11.340 |
| 3250.0 | -13750.0 | 1.833 | 12.050 |

## Grid, masks, and value screening

Grid dimensions match: **True**. GDAL masks identical across assets: **True**. Finite valid masks identical: **True**. Grid georeferencing (CRS, transform, and dimensions) is compared exactly by the script before producing this report.

- NoData is read from the TIFF metadata; non-finite values are counted separately.
- Slope values outside 0–90° and negative count/uncertainty values are flagged as physically suspicious.
- Elevation and uncertainty Tukey 3-IQR fences are exploratory outlier screens only; flagged values are not automatically treated as errors.
- Global p95 uncertainty cutoffs are relative data percentiles, not source-defined acceptance limits.

## Metadata and limitations

- The 100% valid data mask describes finite raster pixels, not direct instrument observations.
- LDEC counts binned LOLA spots; zero-count cells have interpolated LDEM elevations per the product method.
- The exact slope numerical operator and neighborhood are not specified in the retrieved PGDA catalog and remain unknown here.
- A quality raster's RMS estimate is not a guarantee that every individual cell's true error equals that value.
- Empirical p95 and tile rankings are QA prioritization aids, not mission suitability thresholds.
- The local GeoTIFF CRS WKT identifies the lunar radius and polar stereographic parameters, but names the datum unknown; do not substitute an Earth EPSG CRS.
- Embedded GMT history metadata includes the generic output name test.grd; it is retained as source metadata but is not treated as independent evidence of processing provenance.

The machine-readable details, transforms, CRS WKT, tags, per-layer distributions, masks, and tile rankings are in `site04_qa.json`.
