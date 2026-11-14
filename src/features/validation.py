"""Scientific diagnostics for AREA 67 terrain fingerprints."""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd


CORRELATION_METRICS = {
    "Slope": "slope_median",
    "TRI": "tri_median",
    "Local Relief": "local_relief_p95_p5",
    "Terrain Distribution": "terrain_high_pct",
    "Spatial Pattern": "largest_steep_patch_pct",
}


def validate_fingerprint_rows(frame: pd.DataFrame, percentage_tolerance: float = 0.5) -> list[str]:
    """Return integration/scientific-contract errors without replacing nulls."""
    errors: list[str] = []
    required = {
        "site_id", "planet", "source_id", "analysis_scale_m", "nodata_pct",
        "valid_coverage_pct", "slope_unit", "slope_median", "slope_p90",
        "tri_definition", "tri_window_cells", "tri_median", "relief_window_m",
        "local_relief_p95_p5", "terrain_class_thresholds", "terrain_low_pct",
        "terrain_mid_pct", "terrain_high_pct", "spatial_pattern_definition",
        "largest_steep_patch_pct",
    }
    for column in sorted(required - set(frame.columns)):
        errors.append(f"Missing required terrain fingerprint column: {column}")
    if errors:
        return errors
    for column in ("site_id", "source_id", "planet"):
        values = frame[column].astype("string").str.strip()
        if values.isna().any() or values.eq("").any():
            errors.append(f"{column} must be non-empty for every row")
    if frame["site_id"].duplicated().any():
        errors.append("site_id must be unique (one row per site per analysis run)")
    if not frame["planet"].astype(str).str.title().isin({"Earth", "Moon", "Mars"}).all():
        errors.append("planet must be Earth, Moon, or Mars")

    required_numeric = [
        "analysis_scale_m", "nodata_pct", "valid_coverage_pct", "slope_median",
        "slope_p90", "tri_window_cells", "tri_median", "relief_window_m",
        "local_relief_p95_p5", "terrain_low_pct", "terrain_mid_pct",
        "terrain_high_pct", "largest_steep_patch_pct",
    ]
    numeric = frame[required_numeric].apply(pd.to_numeric, errors="coerce")
    for column in required_numeric:
        values = numeric[column]
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
            errors.append(f"{column} must contain finite, non-missing numeric values")
    if (numeric["analysis_scale_m"] <= 0).any() or (numeric["relief_window_m"] <= 0).any():
        errors.append("analysis_scale_m and relief_window_m must be positive")
    if (numeric["tri_window_cells"] <= 0).any():
        errors.append("tri_window_cells must be positive")
    if numeric["analysis_scale_m"].nunique(dropna=True) > 1:
        errors.append("All compared sites must use the same analysis_scale_m")
    if (numeric["slope_median"] < 0).any() or (numeric["slope_p90"] < numeric["slope_median"]).any():
        errors.append("Slope summaries must be non-negative and P90 >= median")
    if (numeric["tri_median"] < 0).any() or (numeric["local_relief_p95_p5"] < 0).any():
        errors.append("TRI and local relief summaries cannot be negative")
    for col in ("nodata_pct", "valid_coverage_pct", "terrain_low_pct", "terrain_mid_pct", "terrain_high_pct", "largest_steep_patch_pct"):
        values = numeric[col]
        if ((values < -percentage_tolerance) | (values > 100 + percentage_tolerance)).any():
            errors.append(f"{col} must be between 0 and 100")
    valid_pair = numeric["nodata_pct"] + numeric["valid_coverage_pct"]
    if (valid_pair.sub(100).abs() > percentage_tolerance).any():
        errors.append("nodata_pct + valid_coverage_pct must sum to approximately 100")
    class_sum = numeric[["terrain_low_pct", "terrain_mid_pct", "terrain_high_pct"]].sum(axis=1)
    if (class_sum.sub(100).abs() > percentage_tolerance).any():
        errors.append("Terrain class percentages must sum to approximately 100")
    return errors


def feature_correlation_audit(frame: pd.DataFrame, threshold: float = 0.8) -> dict[str, Any]:
    """Compute pairwise Spearman correlations when enough measured sites exist.

    Correlation is descriptive and does not replace a scientific decision about
    group weights. Terrain Distribution is explicitly derived from Slope.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    available = {group: metric for group, metric in CORRELATION_METRICS.items() if metric in frame.columns}
    matrix = pd.DataFrame({group: pd.to_numeric(frame[metric], errors="coerce") for group, metric in available.items()})
    if len(matrix) < 3:
        return {
            "status": "insufficient_sites",
            "site_count": int(len(matrix)),
            "minimum_sites_required": 3,
            "correlation_matrix": {},
            "high_correlations": [],
            "notes": ["At least three measured site fingerprints are needed for a basic correlation audit."],
        }
    correlation = matrix.corr(method="spearman", min_periods=3)
    high: list[dict[str, Any]] = []
    for row_index, first in enumerate(correlation.columns):
        for second in correlation.columns[row_index + 1 :]:
            value = correlation.loc[first, second]
            n = int(matrix[[first, second]].dropna().shape[0])
            if pd.notna(value) and abs(float(value)) >= threshold:
                high.append({"feature_a": first, "feature_b": second, "spearman_rho": float(value), "pair_count": n})
    notes = ["Terrain Distribution is derived from Slope; do not give both independent full weight without a deliberate redundancy strategy."]
    notes.append("TRI and Slope may correlate but describe different local terrain properties; inspect measured data before weighting.")
    return {
        "status": "computed",
        "site_count": int(len(matrix)),
        "correlation_matrix": correlation.round(4).astype(object).where(pd.notna(correlation), None).to_dict(),
        "high_correlations": high,
        "notes": notes,
    }


def compare_scale_runs(
    fine_run: dict[str, Any],
    coarse_run: dict[str, Any],
    metrics: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Compare two fingerprints for the same site calculated at different scales."""
    if fine_run.get("site_id") != coarse_run.get("site_id"):
        raise ValueError("Resolution sensitivity requires the same site_id in both runs")
    fine_scale = float(fine_run["analysis_scale_m"])
    coarse_scale = float(coarse_run["analysis_scale_m"])
    if fine_scale == coarse_scale:
        raise ValueError("Resolution sensitivity requires two different analysis scales")
    selected = list(metrics or [
        "slope_median", "slope_p90", "tri_median", "tri_p90",
        "local_relief_p95_p5", "terrain_low_pct", "terrain_mid_pct",
        "terrain_high_pct", "largest_steep_patch_pct",
    ])
    rows = []
    for metric in selected:
        fine_value = fine_run.get(metric)
        coarse_value = coarse_run.get(metric)
        if fine_value is None or coarse_value is None or pd.isna(fine_value) or pd.isna(coarse_value):
            absolute = relative = np.nan
        else:
            absolute = float(coarse_value) - float(fine_value)
            relative = np.nan if float(fine_value) == 0 else 100.0 * absolute / abs(float(fine_value))
        rows.append({
            "site_id": fine_run["site_id"],
            "metric": metric,
            "fine_analysis_scale_m": fine_scale,
            "coarse_analysis_scale_m": coarse_scale,
            "fine_value": fine_value,
            "coarse_value": coarse_value,
            "absolute_change_coarse_minus_fine": absolute,
            "relative_change_pct_vs_fine": relative,
        })
    return pd.DataFrame(rows)
