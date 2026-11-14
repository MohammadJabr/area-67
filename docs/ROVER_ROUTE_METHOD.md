# AREA 67 — Rover Gauntlet A* route method

## Scope and status

The route module implements a grid-based A* least-cost path over aligned elevation, slope, and TRI rasters. It is an optional engineering simulation. Its current tests use synthetic grids; **no real rover route has been calculated or validated** because a selected candidate DEM and compatible TRI layer are not yet available.

This module must not be presented as a rover-safety planner or as a certified route.

## Required raster inputs

The raster workflow accepts three single-band GeoTIFFs:

1. Elevation.
2. Slope.
3. Terrain Ruggedness Index (TRI).

All three must share the same dimensions, CRS, affine transform, and NoData alignment. The CRS must be projected, use square pixels, and declare linear units that can be converted to metres. The affine row/column basis vectors must also be orthogonal; equal basis lengths alone do not rule out a sheared grid. The loader converts horizontal pixel size to metres, elevation and TRI to metres, and slope to degrees. Units are explicit function arguments; the code does not guess them.

Invalid/NoData cells are combined across all three rasters and remain invalid. The A* search also accepts an optional blocked-cell mask and an optional non-negative penalty grid. The raster loader and array planner both enforce `max_grid_cells` (default 250,000) before the Python A* search structures are built. This is a software memory/performance guard, not a scientific or rover threshold. Crop to an approved ROI before routing; raise the limit only after benchmarking the target environment.

The current provisional LOLA Site04 package has elevation and slope layers plus observation/uncertainty products, but this does not imply that an aligned TRI raster or Earth candidate rasters are ready. Do not run a route merely because one of the layers exists.

## Cost model

The implementation follows the role playbook's least-cost structure:

\[
\operatorname{stepCost}
=
\operatorname{distance}
\left(
1+\alpha\,\operatorname{slopeNorm}
+\beta\,\operatorname{triNorm}
+\operatorname{penaltyNorm}
\right)
\]

For a traversed pair of cells, slopeNorm and triNorm are the averages of the endpoint measurements divided by the explicit slope and TRI scales. penaltyNorm is the average of an optional non-negative, dimensionless penalty grid. The base distance is one cell width for cardinal steps and square-root-of-two cell widths for diagonal steps.

The scales, alpha, beta, and penalty values are operating assumptions selected for a simulation; they are not NASA or rover-manufacturer limits. The module rejects negative penalties, invalid slope values, and negative TRI values.

## A* heuristic and grid movement

- The heuristic is Euclidean distance in metres.
- It is admissible because every step costs at least its physical travel distance; terrain and extra penalties are non-negative.
- The grid supports 4-neighbour or 8-neighbour connectivity.
- Diagonal corner-cutting is disabled: a diagonal move is allowed only if both orthogonally adjacent cells are valid.
- NoData and blocked cells are excluded from the graph, not assigned an elevation of zero.
- If start/goal is invalid or no path exists, the function returns an explicit error instead of inventing a route.

## Outputs

The route result includes:

- Ordered row/column cells.
- Total modeled cost and physical path length.
- Elevation, slope, and TRI profiles along the path.
- Per-step and cumulative modeled costs.
- Assumptions and model description.

The CSV exporter records each path cell, the terrain profiles, per-step/cumulative cost, and optional map coordinates in the raster's **native CRS units**, with the CRS identifier in a column. Reproject coordinates before putting them on a basemap.

A JSON sidecar is also written (default: `data/processed/rover_route_metadata.json`). It records start/goal, units, normalization scales, alpha/beta weights, connectivity, maximum grid size, raster CRS/transform/resolution, input raster SHA-256 checksums, optional blocked/penalty layer fingerprints, route summary, and model limitations. Keep the CSV and sidecar together when sharing a route.

## Run from aligned rasters

Example API call (replace paths, units, start/goal cells, and scales with the actual candidate data and documented study settings):

```python
from src.routes.workflow import plan_route_from_rasters

result = plan_route_from_rasters(
    "data/processed/candidate_elevation.tif",
    "data/processed/candidate_slope.tif",
    "data/processed/candidate_tri.tif",
    start=(10, 10),
    goal=(180, 200),
    elevation_unit="m",
    slope_unit="degrees",
    tri_unit="m",
    slope_scale_deg=10.0,
    tri_scale_m=2.0,
    alpha=1.0,
    beta=1.0,
    connectivity=8,
    output_path="data/processed/rover_route.csv",
    metadata_output_path="data/processed/rover_route_metadata.json",
    max_grid_cells=250_000,
)
print(result["route"]["total_cost_m"])
print(result["route_metadata_json"])
```

The numeric scales in this example are placeholders, not recommended values. The project team must agree them after reviewing the candidate dataset and mission objective.

## Scientific limitations

A DEM-derived path does not include, unless separately modeled and validated:

- Rock size, loose soil, regolith bearing strength, wheel/track traction, or wheel sinkage.
- Rover chassis geometry, wheel torque, drive limits, energy budget, or turning radius.
- Sub-pixel obstacles, cliffs hidden by the DEM resolution, local hazards, or perception uncertainty.
- Instrument/DEM uncertainty propagation into route cost.
- Communications, illumination, temperature, or mission operations constraints.

A least-cost raster path is a reproducible terrain-cost demonstration, not proof of physical traversability or safety. Any route shown in a demo must disclose the cost assumptions, grid resolution, source metadata, and limitations.
