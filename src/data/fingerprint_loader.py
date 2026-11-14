"""Load and validate the AREA 67 terrain_fingerprints.csv contract."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


NUMERIC_FIELDS = {
    "analysis_scale_m",
    "slope_median",
    "slope_p90",
    "slope_p95",
    "tri_median",
    "tri_p90",
    "local_relief_p95_p5",
    "relief_window_m",
    "tri_window_cells",
    "terrain_low_pct",
    "terrain_mid_pct",
    "terrain_high_pct",
    "terrain_flat_pct",
    "terrain_moderate_pct",
    "terrain_steep_pct",
    "largest_steep_patch_pct",
    "spatial_pattern_metric",
    "nodata_pct",
    "valid_coverage_pct",
    "direct_observation_coverage_pct",
    "latitude",
    "longitude",
    "area_km2",
    "valid_cell_count",
}

INTEGER_FIELDS = {"tri_window_cells", "valid_cell_count"}

JSON_FIELDS = {
    "terrain_class_thresholds",
    "spatial_pattern_definition",
    "tri_definition",
}


def _parse_cell(value: str | None, field: str, row_number: int) -> Any:
    """Convert CSV cells without silently turning missing measurements into zero."""
    if value is None:
        return None

    stripped = value.strip()
    if stripped == "" or stripped.lower() in {"null", "none", "n/a", "na", "nan"}:
        return None

    if field in NUMERIC_FIELDS:
        try:
            number = float(stripped)
        except ValueError as exc:
            raise ValueError(
                f"Row {row_number}: field {field!r} must be numeric; got {value!r}."
            ) from exc

        if not math.isfinite(number):
            raise ValueError(
                f"Row {row_number}: field {field!r} must be finite; got {value!r}."
            )

        if field in INTEGER_FIELDS:
            if not number.is_integer():
                raise ValueError(
                    f"Row {row_number}: field {field!r} must be an integer."
                )
            return int(number)
        return number

    if field in JSON_FIELDS and stripped[:1] in {"{", "["}:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            # Some producers may use a human-readable threshold description.
            # Preserve it exactly rather than inventing a parsed interpretation.
            return stripped

    return stripped


def load_terrain_fingerprints_csv(path: str | Path) -> list[dict[str, Any]]:
    """Read fingerprints while preserving explicit missing values as None.

    The loader validates required identity columns and duplicate site IDs.
    Feature-specific completeness and method comparability are checked later
    by the matching engine.
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Terrain fingerprint CSV not found: {source}")

    with source.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError("Terrain fingerprint CSV is empty or has no header.")

        required_columns = {"site_id", "planet"}
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise ValueError(
                "Terrain fingerprint CSV is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        records = []
        seen_site_ids = set()

        for row_number, raw_row in enumerate(reader, start=2):
            if raw_row is None or all(
                value is None or value.strip() == ""
                for value in raw_row.values()
            ):
                continue

            record = {
                field: _parse_cell(value, field, row_number)
                for field, value in raw_row.items()
                if field is not None
            }

            site_id = record.get("site_id")
            planet = record.get("planet")
            if not isinstance(site_id, str) or not site_id:
                raise ValueError(f"Row {row_number}: site_id is required.")
            if not isinstance(planet, str) or not planet:
                raise ValueError(f"Row {row_number}: planet is required.")

            if site_id in seen_site_ids:
                raise ValueError(f"Duplicate site_id {site_id!r} in row {row_number}.")
            seen_site_ids.add(site_id)
            records.append(record)

    if not records:
        raise ValueError("Terrain fingerprint CSV contains no data rows.")

    return records


def select_space_to_earth_fingerprints(
    records: list[dict[str, Any]],
    target_site_id: str,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Select one Moon/Mars target and all Earth candidate rows."""
    if not isinstance(target_site_id, str) or not target_site_id.strip():
        raise ValueError("target_site_id must be a non-empty string.")

    matches = [
        row for row in records
        if row.get("site_id") == target_site_id.strip()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one target row for {target_site_id!r}; found {len(matches)}."
        )

    target = matches[0]
    target_planet = str(target.get("planet", "")).strip().lower()
    if target_planet not in {"moon", "mars"}:
        raise ValueError(
            f"Target {target_site_id!r} must have planet Moon or Mars, not {target.get('planet')!r}."
        )

    candidates = {
        row["site_id"]: row
        for row in records
        if str(row.get("planet", "")).strip().lower() == "earth"
    }
    if not candidates:
        raise ValueError("No Earth candidate fingerprints were found in the CSV.")

    return target, candidates
