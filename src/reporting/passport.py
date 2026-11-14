"""Evidence-based Analog Passport assembly and Markdown export."""
from __future__ import annotations
import math
from typing import Any, Mapping
from src.data.contracts import FEATURE_GROUPS


def _clean(value: Any) -> Any:
    if value is None:
        return None
    try:
        if value != value:
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def build_passport(fingerprint: Mapping[str, Any], ranking: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a passport only from supplied source rows; absent values remain absent."""
    row = {str(key): _clean(value) for key, value in fingerprint.items()}
    rank = {str(key): _clean(value) for key, value in (ranking or {}).items()}
    standard_keys = {"site_id", "planet", "site_name", "latitude", "longitude", "area_km2", "source_id", "source_name", "product_version", "access_date", "crs", "vertical_reference", "analysis_scale_m", "nodata_pct", "license"}
    feature_keys = {metric for metrics in FEATURE_GROUPS.values() for metric in metrics}
    return {
        "identity": {key: row[key] for key in ("site_id", "planet", "site_name", "latitude", "longitude", "area_km2") if row.get(key) is not None},
        "provenance": {key: row[key] for key in ("source_id", "source_name", "product_version", "access_date", "crs", "vertical_reference", "analysis_scale_m", "nodata_pct", "license") if row.get(key) is not None},
        "fingerprint": {group: {metric: row[metric] for metric in metrics if row.get(metric) is not None} for group, metrics in FEATURE_GROUPS.items()},
        "ranking": rank,
        "other_metadata": {key: value for key, value in row.items() if key not in standard_keys | feature_keys and value is not None},
    }


def passport_to_markdown(passport: Mapping[str, Any], demo_mode: bool = False) -> str:
    identity, provenance, ranking = passport.get("identity", {}), passport.get("provenance", {}), passport.get("ranking", {})
    lines = ["# AREA 67 — Analog Passport", ""]
    lines.append("> DEMONSTRATION DATA — synthetic example, not a measured scientific result." if demo_mode else "> Generated from supplied project data files. Verify source metadata before scientific use.")
    lines += ["", "## Site identity"]
    for key, label in (("site_id", "Site ID"), ("site_name", "Site name"), ("planet", "Planet/body"), ("latitude", "Latitude"), ("longitude", "Longitude"), ("area_km2", "Area (km²)")):
        lines.append(f"- **{label}:** {identity.get(key, 'Not provided')}")
    lines += ["", "## Data provenance and quality"]
    for key, label in (("source_id", "Source/product ID"), ("source_name", "Source"), ("product_version", "Product version"), ("access_date", "Access date"), ("crs", "Horizontal CRS"), ("vertical_reference", "Vertical reference"), ("analysis_scale_m", "Analysis scale (m)"), ("nodata_pct", "NoData (%)"), ("license", "License/usage terms")):
        lines.append(f"- **{label}:** {provenance.get(key, 'Not provided')}")
    lines += ["", "## Terrain fingerprint"]
    for group, metrics in passport.get("fingerprint", {}).items():
        lines.append(f"### {group}")
        if metrics:
            lines.extend(f"- **{metric}:** {value}" for metric, value in metrics.items())
        else:
            lines.append("- Measurement not supplied.")
    lines += ["", "## Candidate matching"]
    if ranking:
        lines.extend(f"- **{key.replace('_', ' ').title()}:** {value}" for key, value in ranking.items())
    else:
        lines.append("- No matching result supplied for this site.")
    lines += ["", "## Differences, assumptions, and limitations", "- A terrain similarity score is a relative comparison under selected features and mission profile; it is not a probability of mission success.", "- Missing measurements are not estimated or treated as zero.", "- A DEM alone does not establish soil strength, rock size, mineralogy, temperature, radiation, atmospheric conditions, or subsurface properties.", "- Confirm compatible CRS, units, vertical references, spatial scale, and data quality before interpreting cross-body comparisons.", "", "## Suggested use", "Use this site only for the terrain characteristics represented by supplied measurements. Any proposed experiment is a hypothesis to evaluate, not a site-validity certification.", ""]
    return "\n".join(lines)
