"""Shared data contracts, validation, and quality audits for AREA 67."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

FINGERPRINT_REQUIRED_COLUMNS = (
    "site_id",
    "planet",
    "source_id",
    "analysis_scale_m",
    "slope_median",
    "slope_p90",
    "tri_median",
    "local_relief_p95_p5",
    "terrain_flat_pct",
    "terrain_moderate_pct",
    "terrain_steep_pct",
    "spatial_pattern_metric",
    "nodata_pct",
)

RANKING_REQUIRED_COLUMNS = (
    "target_site_id",
    "candidate_site_id",
    "rank",
    "similarity_score",
    "mission_profile",
)

FEATURE_GROUPS = {
    "Slope distribution": ["slope_median", "slope_p90"],
    "Terrain Ruggedness Index (TRI)": ["tri_median"],
    "Local relief": ["local_relief_p95_p5"],
    "Terrain distribution": [
        "terrain_flat_pct",
        "terrain_moderate_pct",
        "terrain_steep_pct",
    ],
    "Spatial pattern": ["spatial_pattern_metric"],
}

FINGERPRINT_NUMERIC_COLUMNS = (
    "analysis_scale_m",
    "slope_median",
    "slope_p90",
    "tri_median",
    "local_relief_p95_p5",
    "terrain_flat_pct",
    "terrain_moderate_pct",
    "terrain_steep_pct",
    "spatial_pattern_metric",
    "nodata_pct",
)

PERCENTAGE_COLUMNS = (
    "terrain_flat_pct",
    "terrain_moderate_pct",
    "terrain_steep_pct",
    "nodata_pct",
)

# These are recommended provenance/method fields. Their absence is a quality
# warning, not a reason to hide otherwise usable measurements.
RECOMMENDED_METADATA_COLUMNS = (
    "source_name",
    "product_version",
    "access_date",
    "crs",
    "vertical_reference",
    "slope_unit",
    "tri_definition",
    "tri_window_cells",
    "relief_window_m",
    "terrain_class_thresholds",
    "spatial_pattern_definition",
)


def missing_columns(frame: pd.DataFrame, required: Iterable[str]) -> list[str]:
    """Return required column names that are absent from a frame."""
    return [column for column in required if column not in frame.columns]


def read_csv(path: str | Path) -> pd.DataFrame:
    """Read a non-empty CSV, raising a useful error for missing/empty files."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"Data file contains no rows: {path}")
    return frame


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
        numeric = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & numeric.isna()
        if invalid.any():
            errors.append(
                f"{column} contains {int(invalid.sum())} non-numeric value(s)"
            )
        finite = numeric.dropna().map(np.isfinite)
        if not finite.all():
            errors.append(f"{column} contains infinite value(s)")
        if not allow_null and numeric.isna().any():
            errors.append(f"{column} contains missing values")
    return errors


def validate_fingerprints(frame: pd.DataFrame) -> list[str]:
    """Validate structural and numeric requirements for the site fingerprint table."""
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

    # Scale and NoData are required quality metadata. Individual terrain
    # metrics may be null as long as each fingerprint group remains represented.
    errors.extend(
        _numeric_errors(
            frame,
            (
                "analysis_scale_m",
                "nodata_pct",
                "terrain_flat_pct",
                "terrain_moderate_pct",
                "terrain_steep_pct",
            ),
            allow_null=False,
        )
    )
    errors.extend(
        _numeric_errors(
            frame,
            (
                "slope_median",
                "slope_p90",
                "tri_median",
                "local_relief_p95_p5",
                "terrain_flat_pct",
                "terrain_moderate_pct",
                "terrain_steep_pct",
                "spatial_pattern_metric",
            ),
            allow_null=True,
        )
    )

    numeric = frame[list(FINGERPRINT_NUMERIC_COLUMNS)].apply(
        pd.to_numeric,
        errors="coerce",
    )
    if (numeric["analysis_scale_m"] <= 0).any():
        errors.append("analysis_scale_m must be greater than zero")
    if (numeric["local_relief_p95_p5"] < 0).any():
        errors.append("local_relief_p95_p5 cannot be negative")
    for column in PERCENTAGE_COLUMNS:
        outside = (numeric[column] < 0) | (numeric[column] > 100)
        if outside.any():
            errors.append(f"{column} must be between 0 and 100")

    if (numeric["slope_median"] < 0).any() or (numeric["slope_p90"] < 0).any():
        errors.append("Slope statistics cannot be negative")
    if (numeric["slope_p90"] < numeric["slope_median"]).any():
        errors.append("slope_p90 must be greater than or equal to slope_median")

    return errors


def validate_rankings(frame: pd.DataFrame) -> list[str]:
    """Validate candidate rankings without assuming a score range or direction."""
    errors = [
        f"Missing required column: {name}"
        for name in missing_columns(frame, RANKING_REQUIRED_COLUMNS)
    ]
    if errors:
        return errors

    for column in ("target_site_id", "candidate_site_id", "mission_profile"):
        values = frame[column].astype("string").str.strip()
        if values.isna().any() or values.eq("").any():
            errors.append(f"{column} contains empty values")

    errors.extend(
        _numeric_errors(
            frame,
            ("rank", "similarity_score"),
            allow_null=False,
        )
    )

    rank_values = pd.to_numeric(frame["rank"], errors="coerce")
    if (rank_values <= 0).any():
        errors.append("rank must contain positive integers")
    if ((rank_values % 1) != 0).any():
        errors.append("rank must contain integer values")

    duplicate_pair = frame.duplicated(
        ["target_site_id", "candidate_site_id", "mission_profile"],
        keep=False,
    )
    if duplicate_pair.any():
        errors.append(
            "Each target/candidate/mission_profile combination must be unique"
        )

    duplicate_rank = frame.duplicated(
        ["target_site_id", "mission_profile", "rank"],
        keep=False,
    )
    if duplicate_rank.any():
        errors.append("Ranks must be unique within each target and mission profile")

    if (frame["target_site_id"].astype(str) == frame["candidate_site_id"].astype(str)).any():
        errors.append("A target site cannot be ranked as its own Earth candidate")

    return errors


def validate_ranking_references(
    fingerprints: pd.DataFrame,
    rankings: pd.DataFrame,
) -> list[str]:
    """Ensure every target and candidate in the ranking table has a fingerprint row."""
    if "site_id" not in fingerprints or not {
        "target_site_id",
        "candidate_site_id",
    }.issubset(rankings.columns):
        return ["Cannot validate ranking references because required ID columns are absent"]

    known_sites = set(fingerprints["site_id"].astype(str))
    target_ids = set(rankings["target_site_id"].astype(str))
    candidate_ids = set(rankings["candidate_site_id"].astype(str))
    missing_targets = sorted(target_ids - known_sites)
    missing_candidates = sorted(candidate_ids - known_sites)
    errors: list[str] = []
    if missing_targets:
        errors.append(
            "Ranking references target site_id values absent from fingerprints: "
            + ", ".join(missing_targets)
        )
    if missing_candidates:
        errors.append(
            "Ranking references candidate site_id values absent from fingerprints: "
            + ", ".join(missing_candidates)
        )
    return errors


def validate_space_to_earth(
    fingerprints: pd.DataFrame,
    rankings: pd.DataFrame,
) -> list[str]:
    """Check the active MVP direction: lunar/Martian targets to Earth candidates."""
    if not {"site_id", "planet"}.issubset(fingerprints.columns):
        return ["Cannot validate Space-to-Earth direction without site_id and planet"]
    if not {"target_site_id", "candidate_site_id"}.issubset(rankings.columns):
        return ["Cannot validate Space-to-Earth direction without ranking site IDs"]

    planets = (
        fingerprints.assign(site_id=fingerprints["site_id"].astype(str))
        .set_index("site_id")["planet"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .to_dict()
    )

    errors: list[str] = []
    for target_id in rankings["target_site_id"].astype(str).unique():
        body = planets.get(target_id)
        if body not in {"moon", "mars"}:
            errors.append(
                f"Space-to-Earth target {target_id} must be a Moon or Mars site; got {body!r}"
            )
    for candidate_id in rankings["candidate_site_id"].astype(str).unique():
        body = planets.get(candidate_id)
        if body != "earth":
            errors.append(
                f"Space-to-Earth candidate {candidate_id} must be an Earth site; got {body!r}"
            )
    return errors


def fingerprint_quality_warnings(frame: pd.DataFrame) -> list[str]:
    """Return explainable data-quality warnings without silently changing data."""
    warnings: list[str] = []
    absent_metadata = [
        column for column in RECOMMENDED_METADATA_COLUMNS
        if column not in frame.columns
    ]
    if absent_metadata:
        warnings.append(
            "Recommended provenance/method metadata columns are absent: "
            + ", ".join(absent_metadata)
        )

    for group, metrics in FEATURE_GROUPS.items():
        available = [column for column in metrics if column in frame.columns]
        if not available:
            warnings.append(f"{group}: no metric columns supplied")
            continue
        numeric = frame[available].apply(pd.to_numeric, errors="coerce")
        missing_rows = numeric.isna().all(axis=1)
        if missing_rows.any():
            ids = (
                frame.loc[missing_rows, "site_id"].astype(str).tolist()
                if "site_id" in frame
                else [str(index) for index in frame.index[missing_rows]]
            )
            warnings.append(
                f"{group}: no usable metric supplied for site(s): " + ", ".join(ids)
            )

    terrain_classes = [
        "terrain_flat_pct",
        "terrain_moderate_pct",
        "terrain_steep_pct",
    ]
    if all(column in frame.columns for column in terrain_classes):
        class_values = frame[terrain_classes].apply(pd.to_numeric, errors="coerce")
        sums = class_values.sum(axis=1, min_count=3)
        off_total = (sums - 100).abs() > 1.0
        if off_total.any():
            ids = (
                frame.loc[off_total, "site_id"].astype(str).tolist()
                if "site_id" in frame
                else [str(index) for index in frame.index[off_total]]
            )
            warnings.append(
                "Terrain-class percentages do not sum to approximately 100% "
                "for: " + ", ".join(ids)
            )

    return warnings
