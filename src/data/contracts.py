"""AREA 67 shared data contracts and validation."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

FINGERPRINT_REQUIRED_COLUMNS = (
    "site_id", "planet", "source_id", "analysis_scale_m",
    "slope_median", "slope_p90", "tri_median",
    "local_relief_p95_p5", "nodata_pct",
)
RANKING_REQUIRED_COLUMNS = (
    "target_site_id", "candidate_site_id", "rank", "mission_profile",
)

# Two documented names for terrain-class proportions are supported. Keep the
# original labels in output so their threshold meaning is never silently changed.
TERRAIN_DISTRIBUTION_VARIANTS = (
    ("terrain_low_pct", "terrain_mid_pct", "terrain_high_pct"),
    ("terrain_flat_pct", "terrain_moderate_pct", "terrain_steep_pct"),
)
SPATIAL_PATTERN_VARIANTS = (
    ("largest_steep_patch_pct",),
    ("spatial_pattern_metric",),
)
FEATURE_GROUPS = {
    "Slope distribution": ["slope_median", "slope_p90", "slope_p95"],
    "Terrain Ruggedness Index (TRI)": ["tri_median", "tri_p90"],
    "Local relief": ["local_relief_p95_p5", "local_relief_median"],
    "Terrain distribution": [
        "terrain_low_pct", "terrain_mid_pct", "terrain_high_pct",
        "terrain_flat_pct", "terrain_moderate_pct", "terrain_steep_pct",
    ],
    "Spatial pattern": ["largest_steep_patch_pct", "spatial_pattern_metric"],
}
OPTIONAL_NUMERIC_COLUMNS = (
    "slope_p95", "tri_p90", "local_relief_median",
    "terrain_low_pct", "terrain_mid_pct", "terrain_high_pct",
    "terrain_flat_pct", "terrain_moderate_pct", "terrain_steep_pct",
    "largest_steep_patch_pct", "spatial_pattern_metric",
    "valid_coverage_pct",
)
PERCENTAGE_COLUMNS = (
    "terrain_low_pct", "terrain_mid_pct", "terrain_high_pct",
    "terrain_flat_pct", "terrain_moderate_pct", "terrain_steep_pct",
    "largest_steep_patch_pct", "valid_coverage_pct", "nodata_pct",
)
RECOMMENDED_METADATA_COLUMNS = (
    "source_name", "product_version", "access_date", "crs",
    "vertical_reference", "slope_unit", "tri_definition",
    "tri_window_cells", "relief_window_m", "terrain_class_thresholds",
    "spatial_pattern_definition",
)
RANKING_SCORE_COLUMNS = ("similarity_score", "relative_similarity")
RANKING_DISTANCE_COLUMNS = ("weighted_distance", "similarity_distance")


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


def normalize_rankings(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize Omar's and Mohammed's documented result-field variants."""
    result = frame.copy()
    if "candidate_site_id" not in result.columns and "site_id" in result.columns:
        result["candidate_site_id"] = result["site_id"]
    if "similarity_score" not in result.columns and "relative_similarity" in result.columns:
        result["similarity_score"] = result["relative_similarity"]
    if "weighted_distance" not in result.columns and "similarity_distance" in result.columns:
        result["weighted_distance"] = result["similarity_distance"]
    return result


def _numeric_errors(
    frame: pd.DataFrame,
    columns: Iterable[str],
    *,
    allow_null: bool = True,
) -> list[str]:
    errors: list[str] = []
    for column in columns:
        if column not in frame.columns:
            continue
        original = frame[column]
        boolean_values = original.map(
            lambda value: isinstance(value, (bool, np.bool_))
        ).fillna(False)
        if boolean_values.any():
            errors.append(
                f"{column} contains {int(boolean_values.sum())} boolean value(s); "
                "expected numeric measurements"
            )
        numeric = pd.to_numeric(original.mask(boolean_values), errors="coerce")
        invalid = original.notna() & ~boolean_values & numeric.isna()
        if invalid.any():
            errors.append(f"{column} contains {int(invalid.sum())} non-numeric value(s)")
        if not numeric.dropna().map(np.isfinite).all():
            errors.append(f"{column} contains infinite value(s)")
        if not allow_null and numeric.isna().any():
            errors.append(f"{column} contains missing values")
    return errors


def _has_complete_variant(
    frame: pd.DataFrame,
    variants: tuple[tuple[str, ...], ...],
) -> tuple[str, ...] | None:
    for variant in variants:
        if all(column in frame.columns for column in variant):
            return variant
    return None


def validate_fingerprints(frame: pd.DataFrame) -> list[str]:
    errors = [
        f"Missing required column: {name}"
        for name in missing_columns(frame, FINGERPRINT_REQUIRED_COLUMNS)
    ]
    if errors:
        return errors

    for column in ("site_id", "planet", "source_id"):
        values = frame[column].astype("string").str.strip()
        if values.isna().any() or values.eq("").any():
            errors.append(f"{column} contains empty values")
    if frame["site_id"].duplicated().any():
        errors.append("site_id must be unique (one row per analyzed site)")

    distribution = _has_complete_variant(frame, TERRAIN_DISTRIBUTION_VARIANTS)
    if distribution is None:
        errors.append(
            "Terrain distribution requires a complete low/mid/high or "
            "flat/moderate/steep percentage set"
        )
    spatial = _has_complete_variant(frame, SPATIAL_PATTERN_VARIANTS)
    if spatial is None:
        errors.append(
            "Spatial pattern requires largest_steep_patch_pct or spatial_pattern_metric"
        )

    required_numeric = [
        "analysis_scale_m", "slope_median", "slope_p90", "tri_median",
        "local_relief_p95_p5", "nodata_pct",
    ]
    if distribution:
        required_numeric.extend(distribution)
    if spatial:
        required_numeric.extend(spatial)
    if "valid_coverage_pct" in frame.columns:
        required_numeric.append("valid_coverage_pct")

    errors.extend(_numeric_errors(frame, required_numeric, allow_null=False))
    optional_numeric = [
        column for column in OPTIONAL_NUMERIC_COLUMNS
        if column in frame.columns and column not in required_numeric
    ]
    errors.extend(_numeric_errors(frame, optional_numeric, allow_null=True))

    present_numeric = [
        column for column in (*required_numeric, *optional_numeric)
        if column in frame.columns
    ]
    numeric = frame[present_numeric].apply(pd.to_numeric, errors="coerce")

    if (numeric["analysis_scale_m"] <= 0).any():
        errors.append("analysis_scale_m must be greater than zero")
    if (numeric["slope_median"] < 0).any() or (numeric["slope_p90"] < 0).any():
        errors.append("Slope statistics cannot be negative")
    if (numeric["slope_p90"] < numeric["slope_median"]).any():
        errors.append("slope_p90 must be greater than or equal to slope_median")
    if "slope_p95" in numeric and (numeric["slope_p95"] < numeric["slope_p90"]).any():
        errors.append("slope_p95 must be greater than or equal to slope_p90")
    if "tri_p90" in numeric and (numeric["tri_p90"] < numeric["tri_median"]).any():
        errors.append("tri_p90 must be greater than or equal to tri_median")
    if (numeric["local_relief_p95_p5"] < 0).any():
        errors.append("local_relief_p95_p5 cannot be negative")

    for column in PERCENTAGE_COLUMNS:
        if column in numeric:
            outside = (numeric[column] < 0) | (numeric[column] > 100)
            if outside.any():
                errors.append(f"{column} must be between 0 and 100")

    for variant in TERRAIN_DISTRIBUTION_VARIANTS:
        if all(column in numeric for column in variant):
            total = numeric[list(variant)].sum(axis=1, min_count=len(variant))
            if ((total - 100).abs() > 1.0).any():
                errors.append("Terrain distribution percentages must sum to approximately 100%")

    if "valid_coverage_pct" in numeric:
        total = numeric["valid_coverage_pct"] + numeric["nodata_pct"]
        if ((total - 100).abs() > 1.0).any():
            errors.append("valid_coverage_pct + nodata_pct must sum to approximately 100%")
    return errors


def validate_rankings(frame: pd.DataFrame) -> list[str]:
    errors = [
        f"Missing required column: {name}"
        for name in missing_columns(frame, RANKING_REQUIRED_COLUMNS)
    ]
    if errors:
        return errors
    if not any(column in frame.columns for column in RANKING_SCORE_COLUMNS):
        errors.append("Rankings must provide similarity_score or relative_similarity")

    for column in ("target_site_id", "candidate_site_id", "mission_profile"):
        values = frame[column].astype("string").str.strip()
        if values.isna().any() or values.eq("").any():
            errors.append(f"{column} contains empty values")

    numeric_columns = ["rank"]
    numeric_columns.extend(
        column for column in RANKING_SCORE_COLUMNS + RANKING_DISTANCE_COLUMNS
        if column in frame.columns
    )
    errors.extend(_numeric_errors(frame, numeric_columns, allow_null=False))
    rank_values = pd.to_numeric(frame["rank"], errors="coerce")
    for distance_column in RANKING_DISTANCE_COLUMNS:
        if distance_column in frame.columns:
            distance_values = pd.to_numeric(frame[distance_column], errors="coerce")
            if (distance_values < 0).any():
                errors.append(f"{distance_column} must be non-negative")
    if (rank_values <= 0).any():
        errors.append("rank must contain positive integers")
    if ((rank_values % 1) != 0).any():
        errors.append("rank must contain integer values")

    if frame.duplicated(
        ["target_site_id", "candidate_site_id", "mission_profile"], keep=False
    ).any():
        errors.append("Each target/candidate/mission_profile combination must be unique")
    if frame.duplicated(
        ["target_site_id", "mission_profile", "rank"], keep=False
    ).any():
        errors.append("Ranks must be unique within each target and mission profile")
    if (
        frame["target_site_id"].astype(str)
        == frame["candidate_site_id"].astype(str)
    ).any():
        errors.append("A target site cannot be ranked as its own Earth candidate")
    return errors


def validate_ranking_references(
    fingerprints: pd.DataFrame,
    rankings: pd.DataFrame,
) -> list[str]:
    if "site_id" not in fingerprints or not {
        "target_site_id", "candidate_site_id"
    }.issubset(rankings.columns):
        return ["Cannot validate ranking references because required ID columns are absent"]
    known = set(fingerprints["site_id"].astype(str))
    missing_targets = sorted(set(rankings["target_site_id"].astype(str)) - known)
    missing_candidates = sorted(set(rankings["candidate_site_id"].astype(str)) - known)
    errors: list[str] = []
    if missing_targets:
        errors.append("Ranking references target site_id values absent from fingerprints: " + ", ".join(missing_targets))
    if missing_candidates:
        errors.append("Ranking references candidate site_id values absent from fingerprints: " + ", ".join(missing_candidates))
    return errors


def validate_space_to_earth(
    fingerprints: pd.DataFrame,
    rankings: pd.DataFrame,
) -> list[str]:
    if not {"site_id", "planet"}.issubset(fingerprints.columns):
        return ["Cannot validate Space-to-Earth direction without site_id and planet"]
    if not {"target_site_id", "candidate_site_id"}.issubset(rankings.columns):
        return ["Cannot validate Space-to-Earth direction without ranking site IDs"]
    planets = (
        fingerprints.assign(site_id=fingerprints["site_id"].astype(str))
        .set_index("site_id")["planet"].astype(str).str.strip().str.casefold().to_dict()
    )
    errors: list[str] = []
    for site_id in rankings["target_site_id"].astype(str).unique():
        body = planets.get(site_id)
        if body not in {"moon", "mars"}:
            errors.append(f"Space-to-Earth target {site_id} must be a Moon or Mars site; got {body!r}")
    for site_id in rankings["candidate_site_id"].astype(str).unique():
        body = planets.get(site_id)
        if body != "earth":
            errors.append(f"Space-to-Earth candidate {site_id} must be an Earth site; got {body!r}")
    return errors


def fingerprint_quality_warnings(frame: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    absent = [column for column in RECOMMENDED_METADATA_COLUMNS if column not in frame.columns]
    if absent:
        warnings.append("Recommended provenance/method metadata columns are absent: " + ", ".join(absent))

    for group, metrics in FEATURE_GROUPS.items():
        available = [column for column in metrics if column in frame.columns]
        if not available:
            warnings.append(f"{group}: no metric columns supplied")
            continue
        values = frame[available].apply(pd.to_numeric, errors="coerce")
        missing = values.isna().all(axis=1)
        if missing.any():
            ids = frame.loc[missing, "site_id"].astype(str).tolist()
            warnings.append(f"{group}: no usable metric supplied for site(s): " + ", ".join(ids))

    return warnings
