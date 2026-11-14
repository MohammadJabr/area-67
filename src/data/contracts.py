"""Shared file contracts and safe CSV loading for AREA 67."""
from __future__ import annotations
from typing import Iterable
from pathlib import Path
import pandas as pd

FINGERPRINT_REQUIRED_COLUMNS = ("site_id", "planet", "source_id", "analysis_scale_m", "slope_median", "slope_p90", "tri_median", "local_relief_p95_p5", "terrain_flat_pct", "terrain_moderate_pct", "terrain_steep_pct", "spatial_pattern_metric", "nodata_pct")
RANKING_REQUIRED_COLUMNS = ("target_site_id", "candidate_site_id", "rank", "similarity_score", "mission_profile")
FEATURE_GROUPS = {
    "Slope distribution": ["slope_median", "slope_p90"],
    "Terrain Ruggedness Index (TRI)": ["tri_median"],
    "Local relief": ["local_relief_p95_p5"],
    "Terrain distribution": ["terrain_flat_pct", "terrain_moderate_pct", "terrain_steep_pct"],
    "Spatial pattern": ["spatial_pattern_metric"],
}

def missing_columns(frame: pd.DataFrame, required: Iterable[str]) -> list[str]:
    return [column for column in required if column not in frame.columns]

def read_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"Data file contains no rows: {path}")
    return frame

def validate_fingerprints(frame: pd.DataFrame) -> list[str]:
    errors = [f"Missing required column: {name}" for name in missing_columns(frame, FINGERPRINT_REQUIRED_COLUMNS)]
    if "site_id" in frame.columns and frame["site_id"].isna().any():
        errors.append("site_id contains empty values")
    if "site_id" in frame.columns and frame["site_id"].duplicated().any():
        errors.append("site_id must be unique (one row per analyzed site)")
    return errors

def validate_rankings(frame: pd.DataFrame) -> list[str]:
    errors = [f"Missing required column: {name}" for name in missing_columns(frame, RANKING_REQUIRED_COLUMNS)]
    if "rank" in frame.columns and pd.to_numeric(frame["rank"], errors="coerce").isna().any():
        errors.append("rank must contain numeric values")
    if "similarity_score" in frame.columns and pd.to_numeric(frame["similarity_score"], errors="coerce").isna().any():
        errors.append("similarity_score must contain numeric values")
    return errors
