"""AREA 67 Streamlit MVP: streamlit run app/main.py."""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.data.contracts import (
    FEATURE_GROUPS,
    fingerprint_quality_warnings,
    normalize_rankings,
    validate_fingerprints,
    validate_ranking_references,
    validate_rankings,
    validate_space_to_earth,
)
from src.reporting.passport import build_passport, passport_to_markdown

st.set_page_config(page_title="AREA 67 | Planetary Analog Discovery", page_icon="🪐", layout="wide")
MVP_DATA = Path(os.environ.get("AREA67_MVP_DATA_DIR", "data/processed/exploratory_mvp_2026-11-15_v2"))
if not MVP_DATA.is_absolute():
    MVP_DATA = ROOT / MVP_DATA
FP = MVP_DATA / "terrain_fingerprints.csv"
RANK = MVP_DATA / "candidate_rankings.csv"
DEMO_FP = ROOT / "data/sample/demo_terrain_fingerprints.csv"
DEMO_RANK = ROOT / "data/sample/demo_candidate_rankings.csv"


def load_data():
    """Load one complete real pair, or a complete labelled demo pair; never mix them."""
    real_fp, real_rank = FP.exists(), RANK.exists()
    if real_fp and real_rank:
        return pd.read_csv(FP), pd.read_csv(RANK), False, []
    if not real_fp and not real_rank and DEMO_FP.exists() and DEMO_RANK.exists():
        return pd.read_csv(DEMO_FP), pd.read_csv(DEMO_RANK), True, []
    if real_fp != real_rank:
        missing = RANK if not real_rank else FP
        message = f"One real output is missing: {missing.relative_to(ROOT)}. The app will not mix real and synthetic results."
    else:
        message = "No complete data pair found. Add the agreed CSV files under data/processed/. No scientific results will be shown."
    return None, None, False, [message]


def feature_metrics() -> list[str]:
    return [metric for metrics in FEATURE_GROUPS.values() for metric in metrics]


def value_or_none(value: Any) -> Any:
    """Preserve missing values rather than converting them to zero."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def site_feature_values(row: pd.Series) -> dict[str, Any]:
    return {metric: value_or_none(row.get(metric)) for metric in feature_metrics() if metric in row.index}


def show_feature_groups(frame: pd.DataFrame, site_ids: list[str]) -> None:
    selected = frame[frame["site_id"].astype(str).isin(site_ids)].copy()
    if selected.empty:
        st.info("No matching target/candidate feature rows are available.")
        return
    if "site_name" not in selected:
        selected["site_name"] = selected["site_id"]
    for group, metrics in FEATURE_GROUPS.items():
        available = [
            metric for metric in metrics
            if metric in selected.columns
            and pd.to_numeric(selected[metric], errors="coerce").notna().any()
        ]
        with st.expander(group, expanded=True):
            if available:
                st.dataframe(selected[["site_id", "site_name", *available]], width="stretch", hide_index=True)
            else:
                st.write("No measurements supplied for this feature group.")


def show_single_parameter_explorer(frame: pd.DataFrame, site_ids: list[str]) -> None:
    options = {
        f"{group} · {metric}": metric
        for group, metrics in FEATURE_GROUPS.items()
        for metric in metrics
        if metric in frame.columns and pd.to_numeric(frame[metric], errors="coerce").notna().any()
    }
    if not options:
        st.info("No numeric terrain parameters are available to explore.")
        return
    label = st.selectbox("Parameter", list(options), key="single_parameter_choice")
    metric = options[label]
    selected = frame[frame["site_id"].astype(str).isin(site_ids)][["site_id", "site_name", metric]].copy()
    selected[metric] = pd.to_numeric(selected[metric], errors="coerce")
    selected = selected.dropna(subset=[metric])
    if selected.empty:
        st.info("No valid observations are available for this parameter.")
        return
    unit_col = f"{metric}_unit"
    if unit_col in frame.columns:
        units = frame[unit_col].dropna().astype(str).unique().tolist()
        if len(units) == 1:
            st.caption(f"Reported unit: {units[0]}")
        elif len(units) > 1:
            st.warning("Unit labels vary across sites; interpret values cautiously.")
    st.plotly_chart(px.bar(selected, x="site_name", y=metric, color="site_id", title=f"Single-parameter comparison · {metric}"), width="stretch")


def main() -> None:
    st.title("AREA 67")
    st.caption("Planetary Analog Discovery & Mission Planning · Discover Earth. Explore Other Worlds.")
    st.write("An evidence-based platform for finding useful terrestrial analogs for selected lunar or Martian exploration tasks.")

    fingerprints, rankings, demo_mode, messages = load_data()
    if demo_mode:
        st.warning("DEMO MODE — displayed measurements and rankings are synthetic interface fixtures. They are NOT NASA observations or validated scientific results.")
    for message in messages:
        st.info(message)

    if fingerprints is None or rankings is None:
        st.subheader("Data integration status")
        st.write("The app is ready for the GIS, terrain-analysis, and matching outputs. It does not create substitute measurements when those files are absent.")
        st.code("data/processed/terrain_fingerprints.csv\ndata/processed/candidate_rankings.csv", language="text")
        st.markdown("See docs/INTEGRATION_CONTRACT.md for the agreed field names and units.")
        st.info("Active MVP workflow: Space-to-Earth. Earth-to-Space remains in the product architecture but is not implemented in this MVP.")
        st.stop()

    if fingerprints.empty or rankings.empty:
        st.error("The supplied CSV pair contains no rows; no results can be shown.")
        st.stop()

    rankings = normalize_rankings(rankings)
    errors = (
        validate_fingerprints(fingerprints)
        + validate_rankings(rankings)
        + validate_ranking_references(fingerprints, rankings)
        + validate_space_to_earth(fingerprints, rankings)
    )
    if errors:
        st.error("Input files do not satisfy the shared integration contract.")
        for error in errors:
            st.write(f"- {error}")
        st.stop()

    exploratory_rows = False
    if "scientific_status" in fingerprints.columns:
        exploratory_rows = fingerprints["scientific_status"].astype(str).str.upper().str.contains("EXPLORATORY").any()
    if "aoi_approval" in fingerprints.columns:
        exploratory_rows = exploratory_rows or (~fingerprints["aoi_approval"].astype(str).str.upper().eq("APPROVED")).any()
    if exploratory_rows:
        st.warning(
            "EXPLORATORY REAL-DATA PILOT — these measurements come from real NASA LOLA and Copernicus rasters, "
            "but every footprint is a provisional reference-centred sampling window, not an approved geomorphic AOI. "
            "Scores are exploratory relative rankings only; do not present them as site certification or rover safety evidence."
        )

    fingerprints = fingerprints.copy()
    rankings = rankings.copy()
    fingerprints["site_id"] = fingerprints["site_id"].astype(str)
    rankings["candidate_site_id"] = rankings["candidate_site_id"].astype(str)
    rankings["target_site_id"] = rankings["target_site_id"].astype(str)
    if "site_name" not in fingerprints.columns:
        fingerprints["site_name"] = fingerprints["site_id"]

    known_ids = set(fingerprints["site_id"])
    unknown_targets = sorted(set(rankings["target_site_id"]) - known_ids)
    unknown_candidates = sorted(set(rankings["candidate_site_id"]) - known_ids)
    if unknown_targets or unknown_candidates:
        st.error("Ranking rows reference site IDs with no fingerprint record. Fix the upstream data contract before interpreting results.")
        if unknown_targets:
            st.write("Unknown target IDs: " + ", ".join(unknown_targets))
        if unknown_candidates:
            st.write("Unknown candidate IDs: " + ", ".join(unknown_candidates))
        st.stop()

    quality_warnings = fingerprint_quality_warnings(fingerprints)
    if quality_warnings:
        with st.expander("Data-quality audit · review before interpreting scores", expanded=True):
            for warning in quality_warnings:
                st.warning(warning)

    tab_setup, tab_results, tab_passport = st.tabs(["1 · Mission Setup", "2 · Results & Comparison", "3 · Site Passport"])

    with tab_setup:
        st.subheader("Mission setup")
        st.info("Space-to-Earth is the active MVP workflow: select a lunar or Martian target and inspect ranked Earth candidates. Earth-to-Space is retained as a future search direction.")
        targets = sorted(rankings["target_site_id"].dropna().unique().tolist())
        if not targets:
            st.error("No target IDs are available in the ranking file.")
            st.stop()
        target_id = st.selectbox("Target site", targets, key="area67_target")
        profiles = sorted(rankings.loc[rankings["target_site_id"] == target_id, "mission_profile"].dropna().astype(str).unique().tolist())
        if not profiles:
            st.error("No mission profile is supplied for this target.")
            st.stop()
        mission_profile = st.selectbox("Mission profile", profiles, key="area67_mission_profile")
        target_rows = fingerprints[fingerprints["site_id"] == target_id]
        target_row = target_rows.iloc[0] if not target_rows.empty else None
        target_body = str(target_row.get("planet", "Not supplied")) if target_row is not None else "Target row not found"
        target_name = str(target_row.get("site_name", target_id)) if target_row is not None else target_id
        c1, c2 = st.columns(2)
        c1.metric("Target", target_name)
        c2.metric("Target body", target_body)
        st.caption("Mission-profile selection filters the ranking produced by the matching module. The app does not recalculate weights or rankings.")
        st.markdown("#### AREA 67 product capabilities")
        st.markdown(
            "| Capability | Scope / current status |\n"
            "|---|---|\n"
            "| Analog Radar | Candidate discovery and ranking from the selected target |\n"
            "| Mission Matching | MVP profile: Rover Navigation / Terrain Traversal; actual weights come from Omar's ranking output |\n"
            "| Single-Parameter Explorer | Available in Results & Comparison |\n"
            "| Rover Gauntlet | A* least-cost route planned after the core data-to-ranking workflow is validated |\n"
            "| ShadowTwin | DEM + SPICE Sun-position illumination analysis; planned until implemented and tested |\n"
            "| Analog Passport | Evidence, provenance, candidate explanation, gaps, and analogy limits |"
        )
        st.caption(
            "Thermal products (MODIS, Diviner, THEMIS) are separate supporting context in the project report. "
            "They are not part of the core topographic similarity score unless source compatibility and an independent method are validated."
        )

    with tab_results:
        st.subheader("Candidate results")
        selected_rankings = rankings[
            (rankings["target_site_id"] == target_id)
            & (rankings["mission_profile"].astype(str) == mission_profile)
        ].copy()
        selected_rankings["rank"] = pd.to_numeric(selected_rankings["rank"], errors="coerce")
        selected_rankings["similarity_score"] = pd.to_numeric(selected_rankings["similarity_score"], errors="coerce")
        selected_rankings = selected_rankings.sort_values("rank")
        candidate_count = selected_rankings["candidate_site_id"].nunique()
        ranking_bases = (
            selected_rankings["ranking_basis"].dropna().astype(str).unique().tolist()
            if "ranking_basis" in selected_rankings.columns else []
        )
        if ranking_bases:
            st.info(
                "Reduced MVP ranking basis: " + "; ".join(ranking_bases)
                + ". Other stored fingerprint groups are context and do not contribute to this score."
            )
        metric_a, metric_b = st.columns(2)
        metric_a.metric("Earth candidates ranked", candidate_count)
        metric_b.metric("Mission profile", mission_profile)
        if candidate_count < 3:
            st.warning(f"Only {candidate_count} candidate(s) are present for this target/profile. The prototype target is at least three.")

        merged = selected_rankings.merge(
            fingerprints,
            left_on="candidate_site_id",
            right_on="site_id",
            how="left",
            suffixes=("", "_fingerprint"),
        )
        display_cols = [
            col for col in (
                "rank", "candidate_site_id", "site_name", "planet",
                "similarity_score", "relative_similarity",
                "weighted_distance", "similarity_distance",
                "slope_group_distance", "ranking_basis",
                "data_completeness", "ranking_stability_note", "ranking_note",
                "source_id", "analysis_scale_m", "valid_coverage_pct",
                "nodata_pct",
            )
            if col in merged.columns
        ]
        st.dataframe(merged[display_cols], width="stretch", hide_index=True)
        if selected_rankings["similarity_score"].notna().any():
            st.plotly_chart(
                px.bar(selected_rankings, x="candidate_site_id", y="similarity_score", color="rank", title="Relative similarity score (as supplied by the matcher)"),
                width="stretch",
            )

        candidate_ids = selected_rankings["candidate_site_id"].tolist()
        comparison_ids = [sid for sid in [target_id, *candidate_ids] if sid in known_ids]
        st.markdown("#### Fingerprint measurements and provenance")
        show_feature_groups(fingerprints, comparison_ids)
        st.markdown("#### Single-Parameter Explorer")
        show_single_parameter_explorer(fingerprints, comparison_ids)

        if {"latitude", "longitude"}.issubset(fingerprints.columns):
            # Planetary latitude/longitude must not be plotted on an Earth basemap.
            # This view intentionally displays Earth candidate locations only.
            mapped = fingerprints[
                fingerprints["site_id"].isin(candidate_ids)
                & fingerprints["planet"].astype(str).str.casefold().eq("earth")
            ].copy()
            mapped["latitude"] = pd.to_numeric(mapped["latitude"], errors="coerce")
            mapped["longitude"] = pd.to_numeric(mapped["longitude"], errors="coerce")
            mapped = mapped.dropna(subset=["latitude", "longitude"])
            if not mapped.empty:
                st.plotly_chart(
                    px.scatter_geo(mapped, lat="latitude", lon="longitude", color="planet", hover_name="site_name", hover_data=["site_id"], title="Earth candidate locations (target coordinates are not plotted on an Earth basemap)"),
                    width="stretch",
                )
                st.caption("Map markers are reference-window anchors only; they are not approved AOI polygons.")
            else:
                st.info("No valid coordinates are available for this target/profile.")
        else:
            st.info("Map view is unavailable because latitude/longitude were not supplied. The candidate table remains available.")

        explanation_cols = [
            col for col in selected_rankings.columns
            if col.endswith("_contribution") or col.endswith("_difference") or col.endswith("_group_distance")
        ]
        if explanation_cols:
            st.markdown("#### Matcher-supplied explanation")
            st.dataframe(selected_rankings[["candidate_site_id", *explanation_cols]], width="stretch", hide_index=True)
        else:
            st.info("Per-feature differences/contributions have not been supplied by the matcher. The app does not estimate them.")

        quality_cols = [col for col in (
            "site_id", "site_name", "source_id", "analysis_scale_m",
            "valid_coverage_pct", "nodata_pct", "direct_observation_coverage_pct",
            "aoi_status", "aoi_approval", "source_checksum_sha256",
        ) if col in fingerprints.columns]
        if quality_cols:
            st.markdown("#### Data quality and provenance")
            st.dataframe(fingerprints[fingerprints["site_id"].isin(comparison_ids)][quality_cols], width="stretch", hide_index=True)

        st.caption("Similarity is a relative ranking under supplied features, scaling, and mission weights. It is not a probability of mission success or certification of site suitability.")

    with tab_passport:
        st.subheader("Analog Passport")
        passport_sites = fingerprints[fingerprints["site_id"].isin(comparison_ids)][["site_id", "site_name"]].drop_duplicates()
        if passport_sites.empty:
            st.info("No target or candidate site rows are available for a Passport.")
            return
        labels = {row.site_id: f"{row.site_name} · {row.site_id}" for row in passport_sites.itertuples()}
        selected_site = st.selectbox("Choose a target/candidate site", passport_sites["site_id"].tolist(), format_func=lambda value: labels.get(value, value), key="passport_site")
        site_row = fingerprints[fingerprints["site_id"] == selected_site].iloc[0]
        matched_rows = selected_rankings[selected_rankings["candidate_site_id"] == selected_site]
        matched_row = matched_rows.iloc[0].to_dict() if not matched_rows.empty else None

        comparison = None
        if selected_site != target_id:
            target_match = fingerprints[fingerprints["site_id"] == target_id]
            if not target_match.empty:
                matcher_differences = {
                    key: value_or_none(value)
                    for key, value in (matched_row or {}).items()
                    if key.endswith("_difference")
                }
                comparison = {
                    "target_site_id": target_id,
                    "candidate_site_id": selected_site,
                    "mission_profile": mission_profile,
                    "target_features": site_feature_values(target_match.iloc[0]),
                    "candidate_features": site_feature_values(site_row),
                    "reported_differences": matcher_differences,
                }

        passport = build_passport(site_row.to_dict(), matched_row, comparison=comparison)
        identity = passport["identity"]
        provenance = passport["provenance"]
        st.markdown(f"### {identity.get('site_name', selected_site)}")
        st.write(f"**{identity.get('planet', 'Body not specified')}** · {selected_site}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Analysis scale", f"{provenance.get('analysis_scale_m')} m" if provenance.get("analysis_scale_m") is not None else "Not supplied")
        c2.metric("NoData", f"{provenance.get('nodata_pct')}%" if provenance.get("nodata_pct") is not None else "Not supplied")
        c3.metric("Source ID", str(provenance.get("source_id", "Not supplied")))
        direct_support = pd.to_numeric(
            pd.Series([site_row.get("direct_observation_coverage_pct")]), errors="coerce"
        ).iloc[0]
        if pd.notna(direct_support):
            st.metric("Direct LOLA shot support", f"{direct_support:.3f}%")
        elif str(site_row.get("planet", "")).casefold() == "earth":
            st.caption("Direct instrument-shot support was not supplied for this Earth DSM; this is separate from raster NoData.")

        st.markdown("#### Terrain Fingerprint evidence")
        missing_features = []
        for group, metrics in FEATURE_GROUPS.items():
            values = passport["fingerprint"].get(group, {})
            present_metrics = [metric for metric in metrics if metric in fingerprints.columns]
            absent = [metric for metric in present_metrics if metric not in values]
            missing_features.extend(absent)
            with st.expander(group, expanded=True):
                if values:
                    st.json(values)
                else:
                    st.write("No measurements supplied for this feature group.")
                if absent:
                    st.caption("Not measured or not supplied: " + ", ".join(absent))
        if missing_features:
            st.warning("Analog gap: some Terrain Fingerprint measurements are missing for this site. They are not replaced with zero.")
        else:
            st.success("All five feature groups have at least one supplied value. This does not by itself establish full scientific validation.")

        st.markdown("#### Source provenance and quality")
        st.json(provenance)
        extra_quality = {
            key: site_row.get(key)
            for key in (
                "scientific_status", "aoi_status", "aoi_approval",
                "aoi_note", "source_quality_note", "effective_resolution_note",
                "source_checksum_sha256", "ldec_checksum_sha256",
                "z_uncertainty_checksum_sha256",
            )
            if key in site_row.index and pd.notna(site_row.get(key))
        }
        if extra_quality:
            st.json(extra_quality)
        if comparison:
            st.markdown("#### Target-to-candidate comparison")
            st.write(f"Target: {target_id} · Mission: {mission_profile}")
            rows = [
                {
                    "Feature": metric,
                    "Target value": comparison["target_features"].get(metric),
                    "Candidate value": comparison["candidate_features"].get(metric),
                }
                for metric in feature_metrics()
                if metric in fingerprints.columns
            ]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            if comparison["reported_differences"]:
                st.write("Differences reported by the matching module")
                st.json(comparison["reported_differences"])
            else:
                st.caption("The matcher has not supplied per-feature differences. The app shows original values and does not invent differences.")

        st.markdown("#### Matching, assumptions, and limitations")
        if passport["ranking"]:
            st.json(passport["ranking"])
        else:
            st.info("No candidate-ranking row applies to the selected target/site.")
        suggested_test = passport["other_metadata"].get("suggested_test")
        st.markdown("**Suggested mission experiment**")
        st.write(
            suggested_test
            if suggested_test
            else "No site-specific experiment proposal has been supplied. Any future proposal must be labelled as a hypothesis, not a suitability certification."
        )
        report = passport_to_markdown(passport, demo_mode=demo_mode)
        st.download_button(
            "Download Analog Passport (Markdown)",
            data=report,
            file_name=f"analog_passport_{selected_site}.md",
            mime="text/markdown",
        )

    st.divider()
    st.caption("AREA 67 · Verify sources, units, vertical references, analysis scale, and data quality before interpreting cross-body comparisons.")


if __name__ == "__main__":
    main()
