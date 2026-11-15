"""Build and integrate a provisional Earth-to-Moon terrain MVP.

This script preserves source rasters and refuses to overwrite any deliverable.
Its Site04 AOI is a provisional operational circle in the DEM's native local
metric grid, centred on the envelope of the official ROI features. It does not
claim to resolve the global lunar body-fixed frame or geological boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS as PyCRS
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from shapely.geometry import Point, mapping

ROOT = Path(__file__).resolve().parents[1]
SITE_ID = "MOON_SITE04_OP_MVP"
SOURCE_ID = "NASA_PGDA_LOLA_Site04_final_adj_5mpp_surf"
SOURCE_URL = "https://pgda.gsfc.nasa.gov/products/78"
ROI_PATH = ROOT / "data/processed/site04_roi_archive_inspection_20261115/Site04_ROIs.shp"
DEM_PATH = ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_surf.tif"
LDEC_PATH = ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_ldec.tif"
ZERR_PATH = ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_toterr.tif"
SLPERR_PATH = ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_slperr.tif"
OUTPUT_DIR = ROOT / "data/processed/site04_operational_mvp_20261115"
EARTH_FINGERPRINTS = ROOT / "data/processed/earth_candidate_mvp_20261115/earth_fingerprints.csv"
CANONICAL_FINGERPRINTS = ROOT / "data/processed/terrain_fingerprints.csv"
CANONICAL_RANKINGS = ROOT / "data/processed/candidate_rankings.csv"
REPORT_PATH = ROOT / "docs/reports/earth_dem_preparation/deliverables/earth_moon_mvp_execution_20261115.md"
SCALE_M = 31.0
RELIEF_WINDOW_M = 124.0
RADIUS_M = 5000.0
NODATA = -9999.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_missing_values(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert CSV NaN sentinels to contract-level nulls without imputing values."""
    return frame.astype(object).where(pd.notna(frame), None)


def nominal_projection_signature(crs: PyCRS) -> tuple[Any, ...]:
    """Return the numeric projection definition, excluding placeholder names."""
    if not crs.is_projected or crs.geodetic_crs is None or crs.coordinate_operation is None:
        raise ValueError("ROI and DEM must declare projected lunar CRS definitions")
    geodetic = crs.geodetic_crs
    axes = tuple(
        (axis.direction.casefold(), float(axis.unit_conversion_factor))
        for axis in crs.axis_info
    )
    params = tuple(
        (parameter.name.casefold(), float(parameter.value),
         str(parameter.unit_name or "").casefold())
        for parameter in crs.coordinate_operation.params
    )
    return (
        round(float(geodetic.ellipsoid.semi_major_metre), 8),
        round(float(geodetic.ellipsoid.semi_minor_metre), 8),
        round(float(geodetic.prime_meridian.longitude) *
              float(geodetic.prime_meridian.unit_conversion_factor), 12),
        str(crs.coordinate_operation.method_name).casefold(),
        axes, params,
    )


def build_site04_aoi(roi_path: Path, dem_path: Path, radius_m: float = RADIUS_M):
    """Build a local operational circle without transforming lunar coordinates."""
    frame = gpd.read_file(roi_path)
    if frame.empty or frame.crs is None or frame.geometry.isna().any():
        raise ValueError("The official ROI archive must contain geometries with a declared CRS")
    if not math.isfinite(radius_m) or radius_m <= 0:
        raise ValueError("radius_m must be a finite positive value")
    with rasterio.open(dem_path) as raster:
        source_crs = raster.crs
        source_pycrs = PyCRS.from_user_input(source_crs)
        roi_crs = PyCRS.from_user_input(frame.crs)
        if not source_crs or not source_crs.is_projected:
            raise ValueError("Site04 DEM must declare a projected CRS")
        if not roi_crs.is_projected:
            raise ValueError("Site04 provider ROI must declare a projected CRS")
        if not ("met" in str(source_crs.linear_units or "").lower()):
            raise ValueError("Site04 DEM projected coordinate units must be metres")
        # The source ROI archive and DEM share projection mathematics and all
        # provider vertices fall exactly on DEM pixel centres. Keep their
        # coordinates in that shared local plane; do not claim a global frame.
        source_geodetic = source_pycrs.geodetic_crs
        roi_geodetic = roi_crs.geodetic_crs
        if not source_geodetic or not roi_geodetic:
            raise ValueError("Cannot compare the ROI and DEM projection definitions")
        for a, b in ((source_geodetic.ellipsoid.semi_major_metre, roi_geodetic.ellipsoid.semi_major_metre),
                     (source_geodetic.ellipsoid.semi_minor_metre, roi_geodetic.ellipsoid.semi_minor_metre)):
            if not math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-8):
                raise ValueError("ROI and DEM do not use the same lunar reference sphere")
        if nominal_projection_signature(source_pycrs) != nominal_projection_signature(roi_crs):
            # Prime-meridian/datum labels differ in the supplied files. They
            # are both zero/placeholder, while exact vertex-to-grid alignment
            # is checked below. No coordinate reprojection is performed.
            raise ValueError("ROI and DEM numeric projection definitions differ")
        transform = raster.transform
        vertices = [point for geom in frame.geometry for point in geom.exterior.coords]
        residuals = []
        for x, y in vertices:
            col, row = (~transform) @ (x, y)
            residuals.append(math.hypot((col - 0.5 - round(col - 0.5)) * transform.a,
                                        (row - 0.5 - round(row - 0.5)) * transform.e))
        if not residuals or max(residuals) > 1e-6:
            raise ValueError("Official ROI vertices are not exactly registered to DEM pixel centres")
        left, bottom, right, top = raster.bounds
        bounds = tuple(float(value) for value in frame.total_bounds)
        center = ((bounds[0] + bounds[2]) / 2.0, (bounds[1] + bounds[3]) / 2.0)
        circle = Point(*center).buffer(radius_m, quad_segs=256)
        circle_bounds = circle.bounds
        if not (left <= circle_bounds[0] and bottom <= circle_bounds[1]
                and right >= circle_bounds[2] and top >= circle_bounds[3]):
            raise ValueError("Provisional Site04 operational AOI exceeds DEM bounds")
        if not circle.is_valid:
            raise ValueError("Generated Site04 operational AOI is invalid")
        return circle, center, source_crs, frame, max(residuals)


def prepare_site04(output_dir: Path = OUTPUT_DIR, radius_m: float = RADIUS_M,
                   target_scale_m: float = SCALE_M) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {output_dir}")
    if not (math.isfinite(target_scale_m) and target_scale_m > 0):
        raise ValueError("target_scale_m must be finite and positive")
    for required in (ROI_PATH, DEM_PATH, LDEC_PATH, ZERR_PATH, SLPERR_PATH, EARTH_FINGERPRINTS):
        if not required.is_file():
            raise FileNotFoundError(required)
    aoi, center, crs, roi_frame, registration_residual = build_site04_aoi(ROI_PATH, DEM_PATH, radius_m)
    # Confirm every output path is new before creating any files.
    names = ["site04_operational_aoi.geojson", "site04_operational_aoi.gpkg",
             "site04_operational_dem_31m_provisional.tif", "site04_validity_mask.tif",
             "site04_aspect_degrees.tif", "site04_hillshade_315_45.tif",
             "site04_run.provisional.json", "site04_fingerprint.csv",
             "preparation_manifest.json"]
    if any((output_dir / name).exists() for name in names):
        raise FileExistsError("Refusing to overwrite an existing Site04 deliverable")

    source_hash = sha256(DEM_PATH)
    output_dir.mkdir(parents=True)
    geom = mapping(aoi)
    props = {
        "site_id": SITE_ID,
        "status": "PROVISIONAL_OPERATIONAL_AOI_NOT_TEAM_APPROVED",
        "aoi_type": "operational_analysis_footprint",
        "is_geological_boundary": False,
        "landform_context": "NASA PGDA Site04, identified by the catalog as Shackleton rim",
        "construction": "256-segment planar circle around midpoint of envelope of all four official Site04 ROI polygons in the DEM local coordinate plane",
        "center_x_m": center[0], "center_y_m": center[1], "radius_m": radius_m,
        "crs_wkt": crs.to_wkt(),
        "coordinate_frame_note": "ROI vertices align exactly to the Site04 DEM pixel-centre lattice; the provider ROI datum/global lunar frame remains unresolved. Geometry is applied directly in the DEM local projected coordinate plane, without reprojection or global frame assignment.",
        "provenance_url": SOURCE_URL,
        "rationale": "Operational context around the official provider ROI cluster; a 5 km radius fits within the local raster bounds and matches the existing provisional Haughton footprint size. Not an approved geology boundary or scientific scale choice.",
    }
    geojson = {
        "type": "FeatureCollection", "name": "site04_operational_aoi_provisional",
        "metadata": props,
        "features": [{"type": "Feature", "properties": props, "geometry": geom}],
    }
    (output_dir / "site04_operational_aoi.geojson").write_text(
        json.dumps(geojson, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    gpkg_frame = gpd.GeoDataFrame([props], geometry=[aoi], crs=crs)
    gpkg_frame.to_file(output_dir / "site04_operational_aoi.gpkg", layer="operational_aoi", driver="GPKG")

    with rasterio.open(DEM_PATH) as src:
        cell = target_scale_m
        left, bottom, right, top = aoi.bounds
        grid_left = math.floor(left / cell) * cell
        grid_top = math.ceil(top / cell) * cell
        width = int(math.ceil((right - grid_left) / cell))
        height = int(math.ceil((grid_top - bottom) / cell))
        target_transform = from_origin(grid_left, grid_top, cell, cell)
        source_data = src.read(1)
        source_valid = (src.read_masks(1) > 0) & np.isfinite(source_data)
        source_data = source_data.astype(np.float32, copy=False)
        source_data[~source_valid] = np.nan
        elevation = np.full((height, width), np.nan, dtype=np.float32)
        reproject(source=source_data, destination=elevation,
                  src_transform=src.transform, src_crs=src.crs, src_nodata=np.nan,
                  dst_transform=target_transform, dst_crs=src.crs, dst_nodata=np.nan,
                  resampling=Resampling.average, init_dest_nodata=True, num_threads=2)
        inside = geometry_mask([geom], (height, width), target_transform,
                               invert=True, all_touched=False)
        valid = inside & np.isfinite(elevation)
        elevation[~valid] = np.nan
        if int(valid.sum()) < 1000:
            raise ValueError("Site04 AOI has insufficient valid target cells")
        profile = src.profile.copy()
        profile.update(driver="GTiff", width=width, height=height, count=1,
                       dtype="float32", crs=src.crs, transform=target_transform,
                       nodata=NODATA, compress="deflate", predictor=3)
        dem_out = output_dir / "site04_operational_dem_31m_provisional.tif"
        with rasterio.open(dem_out, "w", **profile) as dst:
            dst.write(np.where(valid, elevation, NODATA), 1)
            dst.set_band_description(1, "NASA PGDA Site04 interpolated surface elevation Z (m)")
            dst.update_tags(SOURCE=SOURCE_ID, AOI_STATUS=props["status"],
                            RESAMPLING="average", TARGET_SCALE_M=str(cell),
                            VERTICAL_REFERENCE="UNRESOLVED; no transformation applied")
        mask_profile = profile.copy()
        mask_profile.update(dtype="uint8", nodata=255, predictor=1)
        with rasterio.open(output_dir / "site04_validity_mask.tif", "w", **mask_profile) as dst:
            mask_values = np.full((height, width), 255, dtype=np.uint8)
            mask_values[inside] = 0
            mask_values[valid] = 1
            dst.write(mask_values, 1)
            dst.set_band_description(1, "1 valid source-derived cell; 0 invalid inside AOI; 255 outside AOI")

        # Read-only support/uncertainty summaries in the original 5 m grid.
        native_window = rasterio.windows.from_bounds(*aoi.bounds, transform=src.transform)
        native_window = native_window.round_offsets().round_lengths().intersection(
            rasterio.windows.Window(0, 0, src.width, src.height)
        )
        native_transform = src.window_transform(native_window)
        native_shape = (int(native_window.height), int(native_window.width))
        native_inside = geometry_mask([geom], native_shape, native_transform,
                                      invert=True, all_touched=False)
        with rasterio.open(LDEC_PATH) as q, rasterio.open(ZERR_PATH) as zq, rasterio.open(SLPERR_PATH) as sq:
            counts = q.read(1, window=native_window, masked=True)
            zunc = zq.read(1, window=native_window, masked=True)
            sunc = sq.read(1, window=native_window, masked=True)
        count_valid = native_inside & ~np.ma.getmaskarray(counts) & np.isfinite(counts.data)
        direct_pct = 100.0 * float(((counts.data > 0) & count_valid).sum()) / max(1, int(count_valid.sum()))
        zvals = zunc.data[native_inside & ~np.ma.getmaskarray(zunc) & np.isfinite(zunc.data)]
        svals = sunc.data[native_inside & ~np.ma.getmaskarray(sunc) & np.isfinite(sunc.data)]
        coverage = {
            "target_grid_width": width, "target_grid_height": height,
            "target_grid_valid_cells": int(valid.sum()), "target_grid_aoi_cells": int(inside.sum()),
            "target_grid_valid_coverage_pct": 100.0 * float(valid.sum()) / max(1, int(inside.sum())),
            "target_grid_bounds": [grid_left, grid_top - height * cell, grid_left + width * cell, grid_top],
            "target_grid_transform": list(target_transform)[:6],
            "native_roi_cell_count": int(count_valid.sum()),
            "direct_lola_support_pct_native_roi": direct_pct,
            "z_rms_median_m": float(np.median(zvals)) if zvals.size else None,
            "slope_rms_median_deg": float(np.median(svals)) if svals.size else None,
            "native_roi_bounds_within_dem": bool(src.bounds.left <= left and src.bounds.bottom <= bottom
                                                   and src.bounds.right >= right and src.bounds.top >= top),
            "native_aoi_bounds": list(aoi.bounds),
            "source_bounds": list(src.bounds),
            "source_valid_cells_inside_target_aoi": int(valid.sum()),
        }

    # Reuse the existing Haughton visualization helper; do not create a second
    # fingerprint algorithm. It only derives aspect and hillshade previews.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.build_haughton_operational_mvp import _aspect_hillshade
    aspect, shade = _aspect_hillshade(elevation, valid, target_scale_m)
    derivative_profile = profile.copy()
    derivative_profile.update(dtype="float32", nodata=NODATA, predictor=3)
    for filename, values, description, unit in (
        ("site04_aspect_degrees.tif", aspect, "Aspect, degrees clockwise from north", "degrees"),
        ("site04_hillshade_315_45.tif", shade, "Hillshade; azimuth 315 degrees, altitude 45 degrees", "0-255"),
    ):
        with rasterio.open(output_dir / filename, "w", **derivative_profile) as dst:
            dst.write(np.where(np.isfinite(values), values, NODATA).astype(np.float32), 1)
            dst.set_band_description(1, description)
            dst.update_tags(UNITTYPE=unit, AREA67_STATUS=props["status"])

    wkt = crs.to_wkt()
    config = {
        "analysis_scale_m": target_scale_m,
        "relief_window_m": RELIEF_WINDOW_M,
        "local_relief_min_valid_fraction": 1.0,
        "slope_low_max_deg": 10.0, "slope_mid_max_deg": 25.0,
        "steep_threshold_deg": 25.0, "connectivity": 8,
        "minimum_valid_coverage_pct": 80.0,
        "settings_status": "PROVISIONAL_DEMONSTRATOR_SETTINGS_NOT_TEAM_APPROVED",
        "sites": [{
            "site_id": SITE_ID, "site_name": "NASA LOLA Site04 (Shackleton rim; provisional operational context)",
            "planet": "Moon", "source_id": SOURCE_ID,
            "dem_path": str(dem_out.resolve()),
            "aoi_path": str((output_dir / "site04_operational_aoi.geojson").resolve()),
            "aoi_crs": wkt, "elevation_unit": "m",
            "vertical_reference": "NASA PGDA surface height Z, metres; local vertical datum/frame unresolved; no transformation applied",
            "source_name": "NASA GSFC PGDA LRO-LOLA Site04 5 m/pixel LDEM",
            "source_url": SOURCE_URL, "product_version": "PGDA Product 78; file release unspecified",
            "access_date": "2026-11-15", "slope_unit": "degrees",
            "quality_layer": str(LDEC_PATH.resolve()),
            "direct_observation_coverage_pct": direct_pct,
            "uncertainty_note": f"Within this provisional AOI, median source RMS Z uncertainty={coverage['z_rms_median_m']}; median slope RMS uncertainty={coverage['slope_rms_median_deg']} degrees. LDEC positive support={direct_pct:.4f}%; interpolation dominates where LDEC is zero.",
            "effective_resolution_note": "5 m posting is not effective terrain resolution; product interpolation and LDEC support must be considered.",
            "surface_type": "LDEM surface-interpolated elevation",
        }],
    }
    config_path = output_dir / "site04_run.provisional.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "status": "PROVISIONAL_OPERATIONAL_MVP_NOT_TEAM_APPROVED",
        "source": {"path": str(DEM_PATH), "sha256": source_hash, "product": SOURCE_ID,
                   "catalog_url": SOURCE_URL, "height_unit": "m per PGDA catalog",
                   "vertical_reference": "UNRESOLVED; no transformation applied"},
        "quality_source_assets": {
            "LDEC": {"path": str(LDEC_PATH), "sha256": sha256(LDEC_PATH)},
            "total_Z_uncertainty": {"path": str(ZERR_PATH), "sha256": sha256(ZERR_PATH)},
            "slope_uncertainty": {"path": str(SLPERR_PATH), "sha256": sha256(SLPERR_PATH)},
            "provider_slope": {"path": str(ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_slp.tif"),
                               "sha256": sha256(ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_slp.tif")},
        },
        "roi_source": {"path": str(ROI_PATH), "feature_count": len(roi_frame),
                       "crs": roi_frame.crs.to_wkt(),
                       "pixel_lattice_max_vertex_residual_m": registration_residual,
                       "invalid_provider_feature_count": int((~roi_frame.geometry.is_valid).sum()),
                       "coordinate_frame": "unresolved; local raster-plane application only"},
        "aoi": props,
        "coverage_and_quality": coverage,
        "processing": {"target_crs_wkt": wkt, "target_scale_m": target_scale_m,
                       "resampling": "Rasterio average for continuous surface; no vertical transformation",
                       "mask": "source mask plus finite values; separate validity mask; outside AOI=255, invalid inside=0, valid=1",
                       "zero_elevation": "retained as valid data; no global zero recoding or ocean semantics applied",
                       "LDEC": "positive counts are direct spot support; zero counts indicate interpolated LDEM cells per product QA",
                       "settings": {"relief_window_m": RELIEF_WINDOW_M, "local_relief_min_valid_fraction": 1.0,
                                    "slope_class_thresholds_deg": [10.0, 25.0], "steep_threshold_deg": 25.0,
                                    "connectivity": 8, "status": "provisional demonstrator"}},
        "limitations": [
            "The AOI is a provisional operational circle around the envelope of provider ROI features, not an approved geological or illumination boundary.",
            "Provider shapefile CRS does not identify a MOON_ME/DE421 frame; exact pixel-lattice registration supports local placement only.",
            "Site04 local vertical reference is unresolved; no transformation was applied.",
            "Most Site04 cells are interpolated; 5 m posting is not effective resolution.",
            "31 m analysis grid, 124 m relief window, classes and matching tolerances are demonstrator parameters, not team-approved science settings.",
            "No uncertainty propagation or weighting is performed by the current matcher.",
        ],
    }
    (output_dir / "preparation_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {"manifest": manifest, "config_path": config_path, "coverage": coverage,
            "aoi": aoi, "center": center, "dem_out": dem_out}


def run_hiba_fingerprint(prepared: dict[str, Any], hiba_root: Path,
                         output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    hiba_root = hiba_root.resolve()
    hiba_script = hiba_root / "src/features/terrain_fingerprint.py"
    if not hiba_script.is_file():
        raise FileNotFoundError(f"Hiba implementation not found: {hiba_script}")
    output_csv = output_dir / "site04_fingerprint.csv"
    map_dir = output_dir / "fingerprint_maps"
    if output_csv.exists() or map_dir.exists():
        raise FileExistsError("Refusing to overwrite existing Hiba fingerprint outputs")
    subprocess.run([sys.executable, "-m", "src.features.terrain_fingerprint",
                    "--config", str(prepared["config_path"].resolve()),
                    "--output", str(output_csv.resolve()), "--maps-dir", str(map_dir.resolve())],
                   cwd=hiba_root, check=True)
    return {"fingerprint_csv": output_csv, "maps_dir": map_dir}


def integrate_matching(fingerprint_path: Path, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    from src.data.contracts import validate_fingerprints, validate_rankings, validate_ranking_references, validate_space_to_earth
    from src.matching.mission_profiles import get_mission_weights, ROVER_NAVIGATION_PROFILE
    from src.matching.pipeline import rank_terrain_fingerprints
    from src.matching.sensitivity import run_matching_robustness
    from src.reporting.ranking_export import export_rankings_csv

    for path in (CANONICAL_FINGERPRINTS, CANONICAL_RANKINGS):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing application data: {path}")
    earth = normalize_missing_values(pd.read_csv(EARTH_FINGERPRINTS))
    moon = normalize_missing_values(pd.read_csv(fingerprint_path))
    fingerprints = pd.concat([earth, moon], ignore_index=True, sort=False)
    errors = validate_fingerprints(fingerprints)
    if errors:
        raise ValueError("Combined fingerprint table failed integration validation: " + "; ".join(errors))
    target = moon.iloc[0].to_dict()
    candidates = {str(row["site_id"]): row.to_dict() for _, row in earth.iterrows()}
    weights = get_mission_weights()
    tolerances = {"slope_deg": 5.0, "tri_m": 2.0, "local_relief_m": 10.0,
                  "terrain_distribution_pp": 10.0, "spatial_pattern_pct": 10.0}
    profile = ROVER_NAVIGATION_PROFILE["name"]
    result = rank_terrain_fingerprints(target, candidates, weights, tolerances,
                                       mission_profile=profile,
                                       min_feature_group_completeness=0.60)
    if result.get("rejected_candidates"):
        raise ValueError("Matcher rejected one or more Earth candidates: " + json.dumps(result["rejected_candidates"]))
    robustness = run_matching_robustness(result, weights)
    output_dir.mkdir(parents=True, exist_ok=True)
    ranking_csv = output_dir / "site04_candidate_rankings.csv"
    export_rankings_csv(result, profile, ranking_csv,
                        ranking_stability_note="Provisional 20% one-at-a-time weight sensitivity; counts are descriptive, not probabilities.",
                        robustness_result=robustness)
    full_json = output_dir / "site04_matching_result.json"
    full_json.write_text(json.dumps({"status": "PROVISIONAL_EXPLORATORY_NOT_TEAM_APPROVED",
                                     "ranking_result": result, "robustness": robustness,
                                     "limitations": ["Tolerances are illustrative values documented in MATCHING_METHOD.md.",
                                                    "Scores are tolerance-scaled relative indices, not probabilities.",
                                                    "Earth AOIs and Site04 operational AOI are provisional.",
                                                    "Uncertainty and direct observation support are not matcher weights."]},
                                    indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    # Copy into app's canonical locations only after every validation succeeds.
    fingerprints.to_csv(CANONICAL_FINGERPRINTS, index=False)
    ranking = pd.read_csv(ranking_csv)
    ranking_errors = validate_rankings(ranking) + validate_ranking_references(fingerprints, ranking) + validate_space_to_earth(fingerprints, ranking)
    if ranking_errors:
        CANONICAL_FINGERPRINTS.unlink(missing_ok=True)
        raise ValueError("Ranking validation failed before application integration: " + "; ".join(ranking_errors))
    ranking.to_csv(CANONICAL_RANKINGS, index=False)
    finalize_manifest(output_dir)
    return {"ranking": result, "robustness": robustness, "fingerprints": CANONICAL_FINGERPRINTS,
            "rankings": CANONICAL_RANKINGS, "matching_json": full_json, "ranking_csv": ranking_csv}


def finalize_manifest(output_dir: Path) -> None:
    """Record checksums for derived files and the two canonical app tables."""
    manifest_path = output_dir / "preparation_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["quality_source_assets"] = {
        label: {"path": str(path), "sha256": sha256(path)}
        for label, path in (
            ("LDEC", LDEC_PATH),
            ("total_Z_uncertainty", ZERR_PATH),
            ("slope_uncertainty", SLPERR_PATH),
            ("provider_slope", ROOT / "data/raw/moon/site04/Site04_final_adj_5mpp_slp.tif"),
        )
    }
    archive_manifest_path = ROOT / "data/processed/site04_roi_archive_inspection_20261115/archive_inspection_manifest.json"
    if archive_manifest_path.is_file():
        archive_manifest = json.loads(archive_manifest_path.read_text(encoding="utf-8"))
        manifest["roi_source"]["archive_path"] = archive_manifest.get("archive")
        manifest["roi_source"]["archive_sha256"] = archive_manifest.get("archive_sha256")
        manifest["roi_source"]["archive_member_checksums"] = {
            item["name"]: item["sha256"] for item in archive_manifest.get("extracted", [])
        }
    manifest["derived_output_checksums"] = {
        path.relative_to(output_dir).as_posix(): {
            "size_bytes": path.stat().st_size, "sha256": sha256(path)
        }
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path != manifest_path
    }
    manifest["application_output_checksums"] = {
        path.name: {"size_bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in (CANONICAL_FINGERPRINTS, CANONICAL_RANKINGS)
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hiba-root", type=Path, default=ROOT.parent / "area-67-gis-publishing")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--resume-completed-run", action="store_true",
                        help="Write the report from completed outputs without rerunning or overwriting them")
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {args.report}")
    if args.resume_completed_run:
        fingerprint_csv = args.output_dir / "site04_fingerprint.csv"
        result_path = args.output_dir / "site04_matching_result.json"
        manifest_path = args.output_dir / "preparation_manifest.json"
        for required in (args.output_dir, fingerprint_csv, result_path, manifest_path,
                         CANONICAL_FINGERPRINTS, CANONICAL_RANKINGS):
            if not required.exists():
                raise FileNotFoundError(required)
        saved_result = json.loads(result_path.read_text(encoding="utf-8"))
        saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        prepared = {"manifest": saved_manifest,
                    "coverage": saved_manifest["coverage_and_quality"],
                    "center": [saved_manifest["aoi"]["center_x_m"], saved_manifest["aoi"]["center_y_m"]],
                    "dem_out": args.output_dir / "site04_operational_dem_31m_provisional.tif"}
        hiba = {"fingerprint_csv": fingerprint_csv}
        integrated = {"ranking": saved_result["ranking_result"],
                      "fingerprints": CANONICAL_FINGERPRINTS,
                      "rankings": CANONICAL_RANKINGS}
        finalize_manifest(args.output_dir)
    else:
        if args.output_dir.exists():
            raise FileExistsError(f"Refusing to overwrite existing output directory: {args.output_dir}")
        prepared = prepare_site04(output_dir=args.output_dir)
        hiba = run_hiba_fingerprint(prepared, args.hiba_root, args.output_dir)
        integrated = integrate_matching(hiba["fingerprint_csv"], args.output_dir)
    rel = lambda path: Path(path).resolve().relative_to(ROOT).as_posix()
    # Map products from Hiba supply slope, TRI (roughness), and local relief.
    ranking_rows = integrated["ranking"]["ranking"]
    lunar_row = pd.read_csv(hiba["fingerprint_csv"]).iloc[0]
    lines = [
        "# First provisional Earth–Moon terrain MVP execution", "",
        "**Status: executable demonstrator; all AOIs, the common analysis grid, and matching tolerances remain provisional and require team review.**", "",
        "## Lunar AOI and source", "",
        f"- Target: {SITE_ID}; NASA PGDA Site04, cataloged as the Shackleton rim.",
        f"- Operational AOI: circle radius {RADIUS_M:g} m centered at local DEM coordinates ({prepared['center'][0]:.2f}, {prepared['center'][1]:.2f}) m, derived from the envelope of all official ROI features.",
        "- This circle is not the provider illumination ROI, a geological rim boundary, or a team-approved site boundary.",
        "- Provider ROI feature vertices align exactly to DEM pixel centers (0 m max residual), supporting local-grid placement. The global lunar frame remains unresolved; no coordinate transformation was applied.",
        f"- Native ROI support: {prepared['coverage']['native_roi_cell_count']:,} pixel centers; positive LDEC {prepared['coverage']['direct_lola_support_pct_native_roi']:.3f}%; median source Z RMS {prepared['coverage']['z_rms_median_m']:.3f} m; slope RMS median {prepared['coverage']['slope_rms_median_deg']:.3f} degrees.",
        "- Site01 is not locally acquired. Site04 was used as the best available local lunar source; no other dataset was downloaded.", "",
        "## Prepared products", "",
        f"- `{rel(prepared['dem_out'])}`: average-resampled 31 m provisional elevation GeoTIFF; source unchanged.",
        f"- `{rel(args.output_dir / 'site04_validity_mask.tif')}`: separate source-validity/AOI mask.",
        f"- `{rel(args.output_dir / 'site04_aspect_degrees.tif')}` and `site04_hillshade_315_45.tif`.",
        f"- Hiba slope, Riley TRI roughness, and local-relief maps: `{rel(args.output_dir / 'fingerprint_maps')}`.",
        f"- AOI GeoJSON/GPKG, run config, and source/processing manifest: `{rel(args.output_dir)}`.", "",
        "## Fingerprint and comparison", "",
        f"- Real Hiba fingerprint: `{rel(hiba['fingerprint_csv'])}`; generated with Hiba implementation from the sibling checkout `../area-67-gis-publishing`.",
        f"- Five existing Earth fingerprint rows plus one lunar row passed current data-contract validation; Hiba quality status is `{lunar_row.get('quality_status')}`.",
        f"- Direct LOLA support is {float(lunar_row['direct_observation_coverage_pct']):.3f}% of valid native pixels in this AOI. The matcher reports this separately and does not include it or RMS uncertainty in the score.",
        "- Omar's current matcher ranked five Earth candidates under the existing Rover Navigation / Terrain Traversal profile.",
        "- `data_completeness=1.0` means all required feature groups are present and the raster masks have full valid coverage; it does not mean high measurement confidence or high direct LOLA support.",
        "- Matching used documented example tolerances (slope 5 degrees, TRI 2 m, relief 10 m, distributions and pattern 10 percentage points); these remain illustrative, not approved.",
        "- Score formula is 100/(1+weighted distance); scores are relative tolerance-scaled indices, not probabilities or certifications.", "",
        "| Rank | Earth candidate | Score | Distance | Data completeness |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in ranking_rows:
        lines.append(f"| {row['rank']} | {row.get('candidate_site_id', row.get('site_id'))} | {row['similarity_score']:.4f} | {row.get('similarity_distance', row.get('weighted_distance')):.6f} | {row['data_completeness']:.3f} |")
    top = ranking_rows[0]
    lines.extend(["", f"### Feature explanation for the lowest-distance candidate ({top.get('candidate_site_id', top.get('site_id'))})", "",
                  "Group distances are absolute feature differences divided by the illustrative tolerance; values are not probabilities.",
                  "| Feature group | Tolerance-scaled distance |", "|---|---:|"])
    for group, distance in top["group_distances"].items():
        lines.append(f"| {group} | {distance:.4f} |")
    largest_group = max(top["group_distances"], key=top["group_distances"].get)
    lines.append(f"The largest normalized difference for this candidate is **{largest_group}**. This describes the current comparison settings only and does not establish field suitability.")
    lines.extend(["", "## Application integration", "",
                  f"- Canonical files now exist: `{rel(integrated['fingerprints'])}` and `{rel(integrated['rankings'])}`.",
                  "- The existing app loads this complete real-data pair and exposes target selection, feature comparisons, scores, and site passports. No application code was changed.", "",
                  "## Limitations", "",
                  "- 31 m / 124 m settings, 10/25-degree terrain classes, 25-degree steep threshold, and 8-connectivity are demonstrator settings reused from the existing Earth run; they are not scientific approvals.",
                  "- Site04 nominal 5 m posting is not effective resolution. Most valid cells have zero LDEC and are interpolated.",
                  "- Site04 vertical reference and global lunar body-fixed ROI frame remain unresolved; the workflow compares local projected terrain without a global transformation.",
                  "- No uncertainty propagation, direct-observation scoring, effective-resolution correction, or geology-boundary claim is made.",
                  "- Rankings are provisional and depend on the illustrative tolerance set and existing operational mission weights.", "",
                  "## Reproducibility", "",
                  f"Run `python scripts/run_earth_moon_mvp.py --hiba-root ../area-67-gis-publishing --output-dir {rel(args.output_dir)} --report {rel(args.report)}` from the repository root. The command refuses to overwrite existing outputs.",
                  ""])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"fingerprint": str(hiba["fingerprint_csv"]),
                      "canonical_fingerprints": str(integrated["fingerprints"]),
                      "canonical_rankings": str(integrated["rankings"]),
                      "report": str(args.report), "rankings": ranking_rows},
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
