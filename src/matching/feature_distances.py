"""Calculate comparable group distances from AREA 67 terrain fingerprints.

The metric tolerances are explicit configuration inputs. Resulting group
distances are RMS differences measured in tolerance units; they are not
probabilities or universal measures of planetary equivalence.
"""

from collections.abc import Mapping
import json
from math import isclose, isfinite

from src.matching.normalization import standardized_rms_distance


DISTRIBUTION_FIELDS = {
    "low_mid_high": (
        "terrain_low_pct",
        "terrain_mid_pct",
        "terrain_high_pct",
    ),
    "flat_moderate_steep": (
        "terrain_flat_pct",
        "terrain_moderate_pct",
        "terrain_steep_pct",
    ),
}

BASE_TOLERANCE_KEYS = (
    "slope_deg",
    "tri_m",
    "local_relief_m",
    "terrain_distribution_pp",
)


def _finite_number(record: Mapping, key: str, *, required: bool = True):
    value = record.get(key)
    if value is None:
        if required:
            raise ValueError(f"Missing required numeric field: {key}")
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
    ):
        raise ValueError(f"{key} must be a finite numeric value.")
    return float(value)


def _unit_key(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be explicitly declared.")
    return value.strip().lower().replace(" ", "_")


def _slope_to_degrees(value: float, unit: str) -> float:
    unit_key = _unit_key(unit, "slope_unit")
    if unit_key in {"degree", "degrees", "deg", "°"}:
        return value
    if unit_key in {"radian", "radians", "rad"}:
        return value * 180.0 / 3.141592653589793
    raise ValueError(f"Unsupported slope_unit {unit!r}; use degrees or radians.")


def _elevation_to_meters(value: float, unit: str) -> float:
    unit_key = _unit_key(unit, "elevation_unit")
    factors = {
        "m": 1.0,
        "meter": 1.0,
        "meters": 1.0,
        "metre": 1.0,
        "metres": 1.0,
        "cm": 0.01,
        "centimeter": 0.01,
        "centimeters": 0.01,
        "mm": 0.001,
        "millimeter": 0.001,
        "millimeters": 0.001,
        "ft": 0.3048,
        "foot": 0.3048,
        "feet": 0.3048,
    }
    if unit_key not in factors:
        raise ValueError(
            f"Unsupported elevation_unit {unit!r}; convert values to a supported unit first."
        )
    return value * factors[unit_key]


def _validate_percent(value: float, field: str) -> float:
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{field} must be between 0 and 100.")
    return value


def _canonical_metadata(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value).strip().lower()


def _compare_method_field(
    target: Mapping,
    candidate: Mapping,
    field: str,
    warnings: list[str],
    *,
    required_for_comparison: bool = False,
):
    target_value = target.get(field)
    candidate_value = candidate.get(field)

    if target_value is None or candidate_value is None:
        warnings.append(
            f"Method metadata '{field}' is missing on "
            f"{'target' if target_value is None else 'candidate'}; comparability is not fully confirmed."
        )
        if required_for_comparison:
            raise ValueError(f"Both sites must provide {field}.")
        return

    if _canonical_metadata(target_value) != _canonical_metadata(candidate_value):
        raise ValueError(
            f"Incompatible {field}: target={target_value!r}, candidate={candidate_value!r}."
        )


def validate_feature_tolerances(tolerances: Mapping) -> dict:
    """Validate declared feature tolerances and return a normalized copy."""
    if not isinstance(tolerances, Mapping):
        raise TypeError("tolerances must be a mapping.")

    missing = [key for key in BASE_TOLERANCE_KEYS if key not in tolerances]
    if missing:
        raise ValueError(f"Missing feature tolerances: {', '.join(missing)}")

    result = {}
    for key, value in tolerances.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value <= 0
        ):
            raise ValueError(f"Tolerance '{key}' must be finite and greater than zero.")
        result[key] = float(value)

    if "spatial_pattern_pct" not in result and "spatial_pattern_metric" not in result:
        raise ValueError(
            "Provide spatial_pattern_pct for largest_steep_patch_pct or "
            "spatial_pattern_metric for spatial_pattern_metric."
        )
    return result


def compare_terrain_fingerprints(
    target: Mapping,
    candidate: Mapping,
    tolerances: Mapping,
    *,
    scale_relative_tolerance: float = 0.01,
    distribution_sum_tolerance_pp: float = 0.5,
) -> dict:
    """Compare one Moon/Mars target with one Earth candidate.

    Required matching safeguards:
    - Both sites declare analysis scale, slope units, elevation units and NoData.
    - Analysis scales agree within the configured relative tolerance.
    - Known method metadata conflicts are rejected.
    - Missing feature groups remain missing; they are never filled with zero.
    - Scalar and percentage differences are standardized by explicit tolerances.

    TRI is assumed to use the site's declared elevation unit, as expected for
    elevation-difference-based TRI. Confirm this with the feature producer.
    """
    if not isinstance(target, Mapping) or not isinstance(candidate, Mapping):
        raise TypeError("target and candidate fingerprints must be mappings.")

    target_id = target.get("site_id")
    candidate_id = candidate.get("site_id")
    if not isinstance(target_id, str) or not target_id.strip():
        raise ValueError("Target fingerprint must have a non-empty site_id.")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("Candidate fingerprint must have a non-empty site_id.")

    target_planet = str(target.get("planet", "")).strip().lower()
    candidate_planet = str(candidate.get("planet", "")).strip().lower()
    if target_planet not in {"moon", "mars"}:
        raise ValueError("Space-to-Earth matching requires target planet Moon or Mars.")
    if candidate_planet != "earth":
        raise ValueError("Space-to-Earth matching requires an Earth candidate.")

    if (
        isinstance(scale_relative_tolerance, bool)
        or not isinstance(scale_relative_tolerance, (int, float))
        or not isfinite(scale_relative_tolerance)
        or scale_relative_tolerance < 0
    ):
        raise ValueError("scale_relative_tolerance must be finite and non-negative.")

    if (
        isinstance(distribution_sum_tolerance_pp, bool)
        or not isinstance(distribution_sum_tolerance_pp, (int, float))
        or not isfinite(distribution_sum_tolerance_pp)
        or distribution_sum_tolerance_pp < 0
    ):
        raise ValueError("distribution_sum_tolerance_pp must be finite and non-negative.")

    tolerance_values = validate_feature_tolerances(tolerances)

    target_scale = _finite_number(target, "analysis_scale_m")
    candidate_scale = _finite_number(candidate, "analysis_scale_m")
    if target_scale <= 0 or candidate_scale <= 0:
        raise ValueError("analysis_scale_m must be greater than zero.")
    if not isclose(
        target_scale,
        candidate_scale,
        rel_tol=float(scale_relative_tolerance),
        abs_tol=0.0,
    ):
        raise ValueError(
            "Incompatible analysis scales: "
            f"target={target_scale} m, candidate={candidate_scale} m."
        )

    target_nodata = _validate_percent(_finite_number(target, "nodata_pct"), "target nodata_pct")
    candidate_nodata = _validate_percent(
        _finite_number(candidate, "nodata_pct"), "candidate nodata_pct"
    )
    target_valid = 1.0 - target_nodata / 100.0
    candidate_valid = 1.0 - candidate_nodata / 100.0
    if target_valid <= 0 or candidate_valid <= 0:
        raise ValueError("A site has no valid raster coverage after NoData masking.")

    # Where supplied, valid_coverage_pct must agree with 100 - nodata_pct.
    for record, nodata, label in (
        (target, target_nodata, "target"),
        (candidate, candidate_nodata, "candidate"),
    ):
        valid_coverage = record.get("valid_coverage_pct")
        if valid_coverage is not None:
            valid_coverage = _validate_percent(
                _finite_number(record, "valid_coverage_pct"),
                f"{label} valid_coverage_pct",
            )
            if abs(valid_coverage - (100.0 - nodata)) > 1.0:
                raise ValueError(
                    f"{label} valid_coverage_pct conflicts with nodata_pct."
                )

    warnings = []
    for field in (
        "tri_definition",
        "tri_window_cells",
        "relief_window_m",
        "terrain_class_thresholds",
        "spatial_pattern_definition",
    ):
        _compare_method_field(target, candidate, field, warnings)

    if not target.get("source_id") or not candidate.get("source_id"):
        warnings.append("One or both sites are missing source_id provenance.")

    if target_planet == "moon" and target.get("direct_observation_coverage_pct") is None:
        warnings.append(
            "Moon target has no direct_observation_coverage_pct; an instrument-support "
            "layer such as LOLA LDEC must be reviewed separately from NoData coverage."
        )

    target_slope_unit = _unit_key(target.get("slope_unit"), "target slope_unit")
    candidate_slope_unit = _unit_key(candidate.get("slope_unit"), "candidate slope_unit")
    target_elevation_unit = _unit_key(target.get("elevation_unit"), "target elevation_unit")
    candidate_elevation_unit = _unit_key(
        candidate.get("elevation_unit"), "candidate elevation_unit"
    )

    # Validate units before any groups are calculated, even when a group is missing.
    _slope_to_degrees(0.0, target_slope_unit)
    _slope_to_degrees(0.0, candidate_slope_unit)
    _elevation_to_meters(0.0, target_elevation_unit)
    _elevation_to_meters(0.0, candidate_elevation_unit)

    group_distances = {}
    missing_groups = []

    # Slope group: median and P90, standardized in degrees.
    slope_target = [
        _finite_number(target, "slope_median", required=False),
        _finite_number(target, "slope_p90", required=False),
    ]
    slope_candidate = [
        _finite_number(candidate, "slope_median", required=False),
        _finite_number(candidate, "slope_p90", required=False),
    ]
    if any(value is None for value in slope_target + slope_candidate):
        group_distances["slope"] = None
        missing_groups.append("slope")
    else:
        target_slope_deg = [
            _slope_to_degrees(value, target_slope_unit) for value in slope_target
        ]
        candidate_slope_deg = [
            _slope_to_degrees(value, candidate_slope_unit) for value in slope_candidate
        ]
        if any(value < 0 or value > 90 for value in target_slope_deg + candidate_slope_deg):
            raise ValueError("Slope statistics in degrees must be between 0 and 90.")
        group_distances["slope"] = standardized_rms_distance(
            target_slope_deg, candidate_slope_deg, tolerance_values["slope_deg"]
        )

    # TRI group: median and P90, assuming elevation units.
    tri_target = [
        _finite_number(target, "tri_median", required=False),
        _finite_number(target, "tri_p90", required=False),
    ]
    tri_candidate = [
        _finite_number(candidate, "tri_median", required=False),
        _finite_number(candidate, "tri_p90", required=False),
    ]
    if any(value is None for value in tri_target + tri_candidate):
        group_distances["tri"] = None
        missing_groups.append("tri")
    else:
        tri_target_m = [
            _elevation_to_meters(value, target_elevation_unit) for value in tri_target
        ]
        tri_candidate_m = [
            _elevation_to_meters(value, candidate_elevation_unit) for value in tri_candidate
        ]
        if any(value < 0 for value in tri_target_m + tri_candidate_m):
            raise ValueError("TRI statistics must be non-negative.")
        group_distances["tri"] = standardized_rms_distance(
            tri_target_m, tri_candidate_m, tolerance_values["tri_m"]
        )

    # Local relief: P95-P5, converted to metres.
    target_relief = _finite_number(target, "local_relief_p95_p5", required=False)
    candidate_relief = _finite_number(candidate, "local_relief_p95_p5", required=False)
    if target_relief is None or candidate_relief is None:
        group_distances["local_relief"] = None
        missing_groups.append("local_relief")
    else:
        target_relief_m = _elevation_to_meters(target_relief, target_elevation_unit)
        candidate_relief_m = _elevation_to_meters(candidate_relief, candidate_elevation_unit)
        if target_relief_m < 0 or candidate_relief_m < 0:
            raise ValueError("Local relief must be non-negative.")
        group_distances["local_relief"] = standardized_rms_distance(
            [target_relief_m], [candidate_relief_m], tolerance_values["local_relief_m"]
        )

    # Terrain distribution: compare the same explicitly named class set.
    target_distribution_variant = next(
        (name for name, fields in DISTRIBUTION_FIELDS.items()
         if all(field in target for field in fields)),
        None,
    )
    candidate_distribution_variant = next(
        (name for name, fields in DISTRIBUTION_FIELDS.items()
         if all(field in candidate for field in fields)),
        None,
    )
    if (
        target_distribution_variant is None
        or candidate_distribution_variant is None
        or target_distribution_variant != candidate_distribution_variant
    ):
        group_distances["terrain_distribution"] = None
        missing_groups.append("terrain_distribution")
        if (
            target_distribution_variant is not None
            and candidate_distribution_variant is not None
            and target_distribution_variant != candidate_distribution_variant
        ):
            raise ValueError(
                "Terrain distribution class labels differ; do not reinterpret "
                "low/mid/high as flat/moderate/steep."
            )
    else:
        distribution_fields = DISTRIBUTION_FIELDS[target_distribution_variant]
        target_distribution = [
            _finite_number(target, field, required=False) for field in distribution_fields
        ]
        candidate_distribution = [
            _finite_number(candidate, field, required=False) for field in distribution_fields
        ]
        if any(value is None for value in target_distribution + candidate_distribution):
            group_distances["terrain_distribution"] = None
            missing_groups.append("terrain_distribution")
        else:
            target_distribution = [
                _validate_percent(value, field)
                for value, field in zip(target_distribution, distribution_fields)
            ]
            candidate_distribution = [
                _validate_percent(value, field)
                for value, field in zip(candidate_distribution, distribution_fields)
            ]
            for values, label in (
                (target_distribution, "target"),
                (candidate_distribution, "candidate"),
            ):
                if abs(sum(values) - 100.0) > distribution_sum_tolerance_pp:
                    raise ValueError(
                        f"{label} terrain distribution percentages must sum to 100 "
                        f"within {distribution_sum_tolerance_pp} percentage points."
                    )
            group_distances["terrain_distribution"] = standardized_rms_distance(
                target_distribution,
                candidate_distribution,
                tolerance_values["terrain_distribution_pp"],
            )

    # Spatial pattern: the same documented statistic must exist on both sites.
    spatial_field = None
    if "largest_steep_patch_pct" in target or "largest_steep_patch_pct" in candidate:
        spatial_field = "largest_steep_patch_pct"
        spatial_tolerance_key = "spatial_pattern_pct"
    elif "spatial_pattern_metric" in target or "spatial_pattern_metric" in candidate:
        spatial_field = "spatial_pattern_metric"
        spatial_tolerance_key = "spatial_pattern_metric"

    if spatial_field is None:
        group_distances["spatial_pattern"] = None
        missing_groups.append("spatial_pattern")
    else:
        target_spatial = _finite_number(target, spatial_field, required=False)
        candidate_spatial = _finite_number(candidate, spatial_field, required=False)
        if target_spatial is None or candidate_spatial is None:
            group_distances["spatial_pattern"] = None
            missing_groups.append("spatial_pattern")
        else:
            if spatial_field == "largest_steep_patch_pct":
                target_spatial = _validate_percent(target_spatial, spatial_field)
                candidate_spatial = _validate_percent(candidate_spatial, spatial_field)
            if spatial_tolerance_key not in tolerance_values:
                raise ValueError(
                    f"Missing tolerance '{spatial_tolerance_key}' for {spatial_field}."
                )
            group_distances["spatial_pattern"] = standardized_rms_distance(
                [target_spatial],
                [candidate_spatial],
                tolerance_values[spatial_tolerance_key],
            )

    return {
        "target_site_id": target_id.strip(),
        "candidate_site_id": candidate_id.strip(),
        "group_distances": group_distances,
        "missing_groups": missing_groups,
        "method_warnings": warnings,
        "target_analysis_scale_m": target_scale,
        "candidate_analysis_scale_m": candidate_scale,
        "target_valid_coverage_pct": 100.0 * target_valid,
        "candidate_valid_coverage_pct": 100.0 * candidate_valid,
        "valid_raster_coverage_completeness": min(target_valid, candidate_valid),
        "target_direct_observation_coverage_pct": target.get("direct_observation_coverage_pct"),
        "candidate_direct_observation_coverage_pct": candidate.get("direct_observation_coverage_pct"),
        "normalization_method": "RMS of metric differences divided by explicit metric tolerances",
        "normalization_tolerances": tolerance_values,
    }
