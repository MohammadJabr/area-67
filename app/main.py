"""AREA 67 Streamlit MVP: streamlit run app/main.py."""
from __future__ import annotations
import html
import sys
from pathlib import Path
from typing import Any
import pandas as pd
import plotly.express as px
import pydeck as pdk
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
FP = ROOT / "data/processed/terrain_fingerprints.csv"
RANK = ROOT / "data/processed/candidate_rankings.csv"
DEMO_FP = ROOT / "data/sample/demo_terrain_fingerprints.csv"
DEMO_RANK = ROOT / "data/sample/demo_candidate_rankings.csv"


def apply_theme() -> None:
    """Load the repository-owned visual theme without external network assets."""
    theme_path = Path(__file__).with_name("theme.css")
    if theme_path.exists():
        st.markdown(f"<style>{theme_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_hero(status: str, site_count: int, candidate_count: int) -> None:
    """Render the product identity and a mission-console overview."""
    safe_status = html.escape(status)
    st.markdown(
        f"""
        <section class="a67-hero">
          <div class="a67-hero-top">
            <div>
              <div class="a67-brand-chip">AREA <span>67</span></div>
              <p class="a67-eyebrow">MISSION INTELLIGENCE / SPACE-TO-EARTH</p>
            </div>
            <div class="a67-status-pill">{safe_status}</div>
          </div>
          <div class="a67-hero-grid">
            <div class="a67-hero-copy">
              <h1>Find Earth's <span>terrain analogs</span><br>for other worlds.</h1>
              <p>Mission-specific terrain comparison with traceable measurements, transparent uncertainty, and evidence you can inspect — from the Moon to Earth.</p>
              <div class="a67-hero-foot">
                <span class="a67-hero-chip"><strong>{site_count}</strong> fingerprint records</span>
                <span class="a67-hero-chip"><strong>{candidate_count}</strong> ranked Earth references</span>
                <span class="a67-hero-chip"><strong>05</strong> terrain evidence groups</span>
              </div>
            </div>
            <div class="a67-hero-orbit" aria-hidden="true">
              <div class="a67-orbit orbit-one"></div>
              <div class="a67-orbit orbit-two"></div>
              <div class="a67-orbit orbit-three"></div>
              <div class="a67-orbit-core"><span>67</span><small>MISSION<br>INTELLIGENCE</small></div>
              <span class="a67-orbit-dot dot-one"></span>
              <span class="a67-orbit-dot dot-two"></span>
            </div>
          </div>
          <div class="a67-hero-bottom">
            <span>DISCOVER EARTH</span><i></i><span>EXPLORE OTHER WORLDS</span>
            <span class="a67-hero-bottom-right">EVIDENCE FIRST · NO FABRICATED SCORES</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def format_display_number(value: Any, digits: int = 2) -> str:
    clean = value_or_none(value)
    if clean is None:
        return "Not supplied"
    try:
        return f"{float(clean):,.{digits}f}"
    except (TypeError, ValueError, OverflowError):
        return html.escape(str(clean))


def render_candidate_cards(frame: pd.DataFrame) -> None:
    """Show matcher-supplied ranking rows as readable candidate cards."""
    if frame.empty:
        st.info("No candidate rows are available for this target and mission profile.")
        return
    for _, row in frame.sort_values("rank").iterrows():
        rank_value = value_or_none(row.get("rank"))
        try:
            rank = int(float(rank_value))
        except (TypeError, ValueError, OverflowError):
            rank = 0
        site_name = html.escape(str(value_or_none(row.get("site_name")) or row.get("candidate_site_id", "Unknown site")))
        site_id = html.escape(str(row.get("candidate_site_id", "Unknown ID")))
        planet = html.escape(str(value_or_none(row.get("planet")) or "Earth"))
        score = row.get("similarity_score", row.get("relative_similarity"))
        distance = row.get("weighted_distance", row.get("similarity_distance"))
        note_value = value_or_none(row.get("ranking_stability_note")) or value_or_none(row.get("ranking_note"))
        note = html.escape(str(note_value)) if note_value is not None else "Rank and index are reported by the current matcher output."
        distance_line = (
            f"<small>Weighted distance · {format_display_number(distance, 3)}</small>"
            if value_or_none(distance) is not None else ""
        )
        rank_label = "LEADING CANDIDATE" if rank == 1 else (f"RANK {rank:02d}" if rank > 0 else "RANK NOT SUPPLIED")
        card_class = "a67-candidate top" if rank == 1 else "a67-candidate"
        score_text = format_display_number(score, 2) if value_or_none(score) is not None else "—"
        st.markdown(
            f"""
            <article class="{card_class}">
              <div class="a67-rank">{("#" + str(rank)) if rank > 0 else "—"}</div>
              <div class="a67-candidate-main">
                <div class="a67-candidate-name">{site_name}</div>
                <div class="a67-candidate-sub">{planet} · {site_id} · {rank_label}</div>
                <div class="a67-candidate-note">{note}</div>
              </div>
              <div class="a67-candidate-score">
                <span>RELATIVE MATCH INDEX</span>
                <strong>{score_text}</strong>
                {distance_line}
              </div>
            </article>
            """,
            unsafe_allow_html=True,
        )


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
        with st.expander(group, expanded=(group == "Slope")):
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
    figure = px.bar(
        selected, x="site_name", y=metric, color="site_id",
        title=f"Single-parameter comparison · {metric}", template="plotly_dark",
    )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,18,31,.35)",
        font_color="#dce9f8", margin=dict(l=16, r=16, t=56, b=20),
        legend_title_text="Site",
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": True, "responsive": True})


def main() -> None:
    apply_theme()
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
            "EXPLORATORY REAL-DATA PILOT — these are provisional reference-centred windows, "
            "not an approved geomorphic AOI. Scores are relative indices, not site certification "
            "or rover-safety evidence."
        )
        with st.expander("Why this pilot is exploratory · scope and evidence limits", expanded=False):
            st.markdown(
                "- The tracked historical sample set is Haughton, Yungay and Mauna Kea; "
                "the frozen study shortlist is Haughton, Askja and Mauna Kea.\n"
                "- Yungay is held out from the canonical study. Askja's current test window "
                "was held as near-flat/equal-elevation; this is not a conclusion about all Askja terrain.\n"
                "- Site01 positive LOLA LDEC support is 9.235%, distinct from valid-raster coverage.\n"
                "- AOI boundaries, common analysis settings and scientific approvals remain outstanding."
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

    targets = sorted(rankings["target_site_id"].dropna().unique().tolist())
    if not targets:
        st.error("No target IDs are available in the ranking file.")
        st.stop()

    with st.sidebar:
        st.markdown('<div class="a67-sidebar-brand">AREA <span>67</span><small>PLANETARY ANALOG INTELLIGENCE</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="a67-sidebar-caption">Mission configuration</div>', unsafe_allow_html=True)
        target_id = st.selectbox("Target site", targets, key="area67_target")
        profiles = sorted(
            rankings.loc[rankings["target_site_id"] == target_id, "mission_profile"]
            .dropna().astype(str).unique().tolist()
        )
        if not profiles:
            st.error("No mission profile is supplied for this target.")
            st.stop()
        mission_profile = st.selectbox("Mission profile", profiles, key="area67_mission_profile")
        st.markdown(
            '<div class="a67-sidebar-status"><strong>SPACE-TO-EARTH ACTIVE</strong>'
            '<p>Target selection filters the supplied matcher output. Scores and rankings are not recalculated in the interface.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="a67-sidebar-caption">Evidence workspace</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="a67-sidebar-nav-hint">Navigate with the workspace tabs: Mission Control · Analog Radar · Terrain Lab · Analog Passport.</div>',
            unsafe_allow_html=True,
        )
        st.caption("Earth-to-Space discovery, Rover Gauntlet and ShadowTwin remain outside this MVP.")

    target_rows = fingerprints[fingerprints["site_id"] == target_id]
    target_row = target_rows.iloc[0] if not target_rows.empty else None
    target_body = str(target_row.get("planet", "Not supplied")) if target_row is not None else "Target row not found"
    target_name = str(target_row.get("site_name", target_id)) if target_row is not None else target_id

    status_label = (
        "SYNTHETIC DEMO · NOT MEASURED"
        if demo_mode else
        "EXPLORATORY REAL-DATA PILOT"
        if exploratory_rows else
        "CONNECTED DATASET"
    )
    render_hero(status_label, len(fingerprints), rankings["candidate_site_id"].nunique())

    tab_setup, tab_results, tab_terrain, tab_passport = st.tabs(["01 · Mission Control", "02 · Analog Radar", "03 · Terrain Lab", "04 · Analog Passport"])

    with tab_setup:
        st.markdown(
            '<div class="a67-section"><div class="a67-section-kicker">Mission workspace</div>'
            '<div class="a67-section-title">Your mission, configured.</div>'
            '<div class="a67-section-subtitle">Choose a supported target and mission profile from the controls in the left panel. The interface reads the matcher output; it does not invent or recompute rankings.</div></div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Target region", target_name)
        c2.metric("Target body", target_body)
        c3.metric("Mission profile", mission_profile)
        st.markdown(
            '<div class="a67-inline-note">Space-to-Earth is the active MVP workflow: start from a lunar or Martian target and inspect ranked Earth reference windows. Earth-to-Space remains a future search direction.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="a67-section"><div class="a67-section-kicker">Platform modules</div>'
            '<div class="a67-section-title">Evidence-first capability stack</div>'
            '<div class="a67-section-subtitle">Each module is labelled by what is implemented today, not by the long-term product vision.</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="a67-capability-grid">'
            '<article class="a67-capability"><span class="a67-cap-status">ACTIVE</span><h4>Analog Radar</h4><p>Mission-filtered candidate ranking from the supplied real-data pilot outputs.</p></article>'
            '<article class="a67-capability"><span class="a67-cap-status">ACTIVE</span><h4>Mission Matching</h4><p>Weighted five-group similarity and matcher-reported ranking explanations.</p></article>'
            '<article class="a67-capability"><span class="a67-cap-status">ACTIVE</span><h4>Terrain Lab</h4><p>Five terrain groups, source values and single-parameter exploration.</p></article>'
            '<article class="a67-capability"><span class="a67-cap-status">ACTIVE</span><h4>Analog Passport</h4><p>Site identity, evidence, provenance, data quality and portable report export.</p></article>'
            '<article class="a67-capability"><span class="a67-cap-status planned">PLANNED</span><h4>Rover Gauntlet</h4><p>Optional A* least-cost route prototype; not merged into this MVP and not a rover-safety planner.</p></article>'
            '<article class="a67-capability"><span class="a67-cap-status planned">PLANNED</span><h4>ShadowTwin</h4><p>Illumination and shadow analysis requires validated DEM and SPICE solar-position inputs.</p></article>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Thermal products (MODIS, Diviner, THEMIS) are supporting context only. They are not part of the core topographic score unless compatibility and an independent method are validated."
        )

    with tab_results:
        st.markdown(
            '<div class="a67-section"><div class="a67-section-kicker">Analog Radar</div>'
            '<div class="a67-section-title">Candidate intelligence</div>'
            '<div class="a67-section-subtitle">Explore the ranking and inspect the terrain evidence behind each candidate.</div></div>',
            unsafe_allow_html=True,
        )
        selected_rankings = rankings[
            (rankings["target_site_id"] == target_id)
            & (rankings["mission_profile"].astype(str) == mission_profile)
        ].copy()
        selected_rankings["rank"] = pd.to_numeric(selected_rankings["rank"], errors="coerce")
        selected_rankings["similarity_score"] = pd.to_numeric(selected_rankings["similarity_score"], errors="coerce")
        selected_rankings = selected_rankings.sort_values("rank")
        total_candidate_count = selected_rankings["candidate_site_id"].nunique()
        all_candidate_ids = selected_rankings["candidate_site_id"].tolist()
        candidate_name_map = fingerprints.set_index("site_id")["site_name"].to_dict()
        st.markdown("#### Refine the radar view")
        selected_candidate_ids = st.multiselect(
            "Compare Earth candidates",
            options=all_candidate_ids,
            default=all_candidate_ids,
            format_func=lambda site_id: f"{candidate_name_map.get(site_id, site_id)} · {site_id}",
            key="area67_candidate_filter",
            help="Filter the cards, ranking chart, map, and terrain comparison. This does not change the matcher ranking.",
        )
        selected_rankings = selected_rankings[
            selected_rankings["candidate_site_id"].isin(selected_candidate_ids)
        ].copy()
        candidate_count = selected_rankings["candidate_site_id"].nunique()
        metric_a, metric_b = st.columns(2)
        metric_a.metric("Candidates shown", f"{candidate_count} / {total_candidate_count}")
        metric_b.metric("Mission profile", mission_profile)
        if total_candidate_count < 3:
            st.warning(f"The supplied matcher output contains {total_candidate_count} candidate(s) for this target/profile; the current prototype goal is at least three.")
        elif candidate_count < total_candidate_count:
            st.caption(f"Filtered view: showing {candidate_count} of {total_candidate_count} available Earth candidates. Clear the candidate filter to restore the full comparison.")

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
                "data_completeness", "ranking_stability_note", "ranking_note",
                "source_id", "analysis_scale_m", "valid_coverage_pct",
                "nodata_pct",
            )
            if col in merged.columns
        ]
        view_mode = st.radio(
            "Ranking display",
            ["Candidate cards", "Detailed data table"],
            horizontal=True,
            key="area67_ranking_display",
        )
        if view_mode == "Candidate cards":
            render_candidate_cards(merged)
        else:
            st.dataframe(merged[display_cols], width="stretch", hide_index=True)

        if not selected_rankings.empty:
            spotlight_options = selected_rankings["candidate_site_id"].tolist()
            spotlight_id = st.selectbox(
                "Candidate spotlight",
                options=spotlight_options,
                format_func=lambda site_id: f"{candidate_name_map.get(site_id, site_id)} · {site_id}",
                key="area67_candidate_spotlight",
            )
            spotlight = selected_rankings[
                selected_rankings["candidate_site_id"] == spotlight_id
            ].iloc[0]
            spotlight_rank = value_or_none(spotlight.get("rank"))
            spotlight_score = value_or_none(spotlight.get("similarity_score", spotlight.get("relative_similarity")))
            spotlight_distance = value_or_none(spotlight.get("weighted_distance", spotlight.get("similarity_distance")))
            spotlight_completeness = value_or_none(spotlight.get("data_completeness"))
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Current rank", f"#{int(float(spotlight_rank))}" if spotlight_rank is not None else "Not supplied")
            s2.metric("Relative match index", format_display_number(spotlight_score, 2))
            s3.metric("Weighted distance", format_display_number(spotlight_distance, 3))
            s4.metric("Data completeness", f"{float(spotlight_completeness):.1%}" if spotlight_completeness is not None else "Not supplied")
            spotlight_note = value_or_none(spotlight.get("ranking_stability_note")) or value_or_none(spotlight.get("ranking_note"))
            if spotlight_note is not None:
                st.caption(str(spotlight_note))
        else:
            st.info("Select at least one candidate to populate the radar, map, and terrain comparison.")

        if selected_rankings["similarity_score"].notna().any():
            chart_data = selected_rankings.merge(
                fingerprints[["site_id", "site_name"]],
                left_on="candidate_site_id", right_on="site_id", how="left",
            )
            chart_data["rank_label"] = chart_data["rank"].apply(
                lambda value: f"Rank {int(value)}" if pd.notna(value) else "Unranked"
            )
            ranking_figure = px.bar(
                chart_data.sort_values("rank", ascending=True),
                x="similarity_score",
                y="site_name",
                color="rank_label",
                orientation="h",
                title="Candidate comparison · relative match index",
                template="plotly_dark",
                color_discrete_map={
                    "Rank 1": "#c7f36b", "Rank 2": "#67d7e9",
                    "Rank 3": "#9c8cff", "Unranked": "#ffad66",
                },
                hover_data={
                    "candidate_site_id": True, "rank": True,
                    "weighted_distance": ":.4f", "site_name": False,
                    "rank_label": False,
                },
            )
            ranking_figure.update_traces(
                texttemplate="%{x:.2f}", textposition="outside",
                cliponaxis=False, marker_line_width=0,
            )
            ranking_figure.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,18,31,.35)",
                font_color="#dce9f8", margin=dict(l=16, r=70, t=56, b=22),
                xaxis_title="Relative match index", yaxis_title="Earth candidate",
                legend_title_text="Candidate rank", height=max(300, 105 * len(chart_data)),
                bargap=0.42, showlegend=True,
            )
            ranking_figure.update_yaxes(autorange="reversed")
            st.plotly_chart(
                ranking_figure, width="stretch",
                config={"displayModeBar": True, "scrollZoom": True, "responsive": True},
            )

        candidate_ids = selected_rankings["candidate_site_id"].tolist()
        comparison_ids = [sid for sid in [target_id, *candidate_ids] if sid in known_ids]
        st.markdown("#### Geographic discovery map")
        st.caption("Explore Earth reference anchors. Pan and zoom the map, switch basemaps, focus one candidate, or show site labels.")
        map_controls = st.columns([1.05, 1.55, 1.0])
        basemap_choice = map_controls[0].selectbox(
            "Basemap", ["Dark Matter", "Light", "Voyager"], key="area67_map_basemap"
        )
        focus_options = ["All selected candidates", *candidate_ids]
        map_focus = map_controls[1].selectbox(
            "Map focus",
            options=focus_options,
            format_func=lambda value: "All selected candidates" if value == "All selected candidates"
            else candidate_name_map.get(value, value),
            key="area67_map_focus",
        )
        show_map_labels = map_controls[2].toggle(
            "Show labels", value=True, key="area67_map_labels"
        )
        if {"latitude", "longitude"}.issubset(fingerprints.columns):
            # Only Earth candidate anchors belong on this basemap; lunar coordinates
            # are intentionally kept out of the Earth geographic view.
            mapped = fingerprints[
                fingerprints["site_id"].isin(candidate_ids)
                & fingerprints["planet"].astype(str).str.casefold().eq("earth")
            ].copy()
            mapped["latitude"] = pd.to_numeric(mapped["latitude"], errors="coerce")
            mapped["longitude"] = pd.to_numeric(mapped["longitude"], errors="coerce")
            mapped = mapped.dropna(subset=["latitude", "longitude"])
            if not mapped.empty:
                map_rank_cols = ["candidate_site_id", "rank", "similarity_score"]
                if "weighted_distance" in selected_rankings.columns:
                    map_rank_cols.append("weighted_distance")
                map_ranks = selected_rankings[map_rank_cols].drop_duplicates("candidate_site_id")
                mapped = mapped.merge(
                    map_ranks, left_on="site_id", right_on="candidate_site_id", how="left",
                )
                mapped["rank"] = pd.to_numeric(mapped["rank"], errors="coerce")
                mapped["similarity_score"] = pd.to_numeric(mapped["similarity_score"], errors="coerce")
                rank_colors = {
                    1: [199, 243, 107, 230], 2: [103, 215, 233, 230],
                    3: [156, 140, 255, 230],
                }
                mapped["marker_color"] = mapped["rank"].apply(
                    lambda value: rank_colors.get(int(value), [255, 173, 102, 225])
                    if pd.notna(value) else [255, 173, 102, 225]
                )
                mapped["rank_label"] = mapped["rank"].apply(
                    lambda value: f"#{int(value)}" if pd.notna(value) else "Not ranked"
                )
                mapped["score_label"] = mapped["similarity_score"].apply(
                    lambda value: f"{value:.2f}" if pd.notna(value) else "Not supplied"
                )
                if "weighted_distance" in mapped.columns:
                    mapped["distance_label"] = pd.to_numeric(mapped["weighted_distance"], errors="coerce").apply(
                        lambda value: f"{value:.4f}" if pd.notna(value) else "Not supplied"
                    )
                else:
                    mapped["distance_label"] = "Not supplied"
                if map_focus != "All selected candidates":
                    focus_marker = mapped[mapped["site_id"] == map_focus]
                    if not focus_marker.empty:
                        center_lat = float(focus_marker.iloc[0]["latitude"])
                        center_lon = float(focus_marker.iloc[0]["longitude"])
                        map_zoom = 5.2
                    else:
                        center_lat = float(mapped["latitude"].mean())
                        center_lon = float(mapped["longitude"].mean())
                        map_zoom = 1.25
                else:
                    lat_span = float(mapped["latitude"].max() - mapped["latitude"].min())
                    lon_span = float(mapped["longitude"].max() - mapped["longitude"].min())
                    map_zoom = 1.25
                    if len(mapped) == 1:
                        map_zoom = 4.0
                    elif max(lat_span, lon_span) < 18:
                        map_zoom = 3.0
                    center_lat = float(mapped["latitude"].mean())
                    center_lon = float(mapped["longitude"].mean())
                view_state = pdk.ViewState(
                    latitude=center_lat,
                    longitude=center_lon,
                    zoom=map_zoom, pitch=0, bearing=0,
                )
                points_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=mapped,
                    get_position="[longitude, latitude]",
                    get_radius=24000,
                    get_fill_color="marker_color",
                    get_line_color=[242, 247, 252, 235],
                    line_width_min_pixels=1,
                    stroked=True, filled=True,
                    pickable=True, auto_highlight=True,
                    radius_min_pixels=7, radius_max_pixels=20,
                )
                map_layers = [points_layer]
                if show_map_labels:
                    map_layers.append(
                        pdk.Layer(
                            "TextLayer",
                            data=mapped,
                            get_position="[longitude, latitude]",
                            get_text="site_name",
                            get_size=13,
                            get_color=[242, 247, 252, 235],
                            get_angle=0,
                            billboard=True,
                            pickable=False,
                            get_pixel_offset=[0, -22],
                        )
                    )
                map_styles = {
                    "Dark Matter": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                    "Light": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                    "Voyager": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
                }
                deck = pdk.Deck(
                    layers=map_layers,
                    initial_view_state=view_state,
                    map_style=map_styles[basemap_choice],
                    tooltip={
                        "html": (
                            "<b>{site_name}</b><br/>Rank: {rank_label}<br/>"
                            "Relative match index: {score_label}<br/>"
                            "Weighted distance: {distance_label}<br/>"
                            "Reference: {latitude}, {longitude}"
                        ),
                        "style": {
                            "backgroundColor": "rgba(7,16,29,0.96)",
                            "color": "#ecf4ff",
                            "border": "1px solid rgba(103,215,233,.35)",
                        },
                    },
                )
                st.pydeck_chart(deck, width="stretch", height=470, key="area67_candidate_map")
                if map_focus != "All selected candidates":
                    st.caption(
                        "Focused on " + str(candidate_name_map.get(map_focus, map_focus))
                        + "; other filtered candidate anchors remain visible."
                    )
                st.caption(
                    "Pins are reference-window anchors only, not approved AOI polygons. "
                    "No terrain raster overlay is shown because validated, hosted AOI rasters are not yet available. "
                    "Lunar coordinates are deliberately not plotted on this Earth map."
                )
                st.markdown(
                    '<div class="a67-map-legend"><span><i class="rank-one"></i> Rank 1</span><span><i class="rank-two"></i> Rank 2</span><span><i class="rank-three"></i> Rank 3</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("No valid Earth reference coordinates are available for the selected candidates.")
        else:
            st.info("Map view is unavailable because candidate latitude/longitude were not supplied. The candidate table remains available.")

        st.caption("Similarity is a relative ranking under supplied features, scaling, and mission weights. It is not a probability of mission success or certification of site suitability.")

    with tab_terrain:
        st.markdown(
            '<div class="a67-section"><div class="a67-section-kicker">Analysis workspace</div>'
            '<div class="a67-section-title">Terrain Lab</div>'
            '<div class="a67-section-subtitle">Inspect the supplied terrain measurements side by side. The lab visualizes the current matcher inputs; it does not recalculate or fill missing scientific measurements.</div></div>',
            unsafe_allow_html=True,
        )
        terrain_sites = fingerprints[fingerprints["site_id"].isin(comparison_ids)].copy()
        terrain_site_labels = {
            row.site_id: f"{row.site_name} · {row.planet}"
            for row in terrain_sites[["site_id", "site_name", "planet"]].drop_duplicates().itertuples()
        }
        if terrain_sites.empty:
            st.info("No target or candidate fingerprint records are available for this terrain comparison.")
        else:
            focus_site = st.selectbox(
                "Focus site",
                options=comparison_ids,
                format_func=lambda site_id: terrain_site_labels.get(site_id, site_id),
                key="area67_terrain_focus",
                help="Choose a site to focus its measurements in the Terrain Lab. The comparison tables retain the selected target and candidate set.",
            )
            focus_row = terrain_sites[terrain_sites["site_id"] == focus_site]
            if not focus_row.empty:
                focus = focus_row.iloc[0]
                f1, f2, f3 = st.columns(3)
                f1.metric("Focus site", str(focus.get("site_name", focus_site)))
                f2.metric("Planetary body", str(focus.get("planet", "Not supplied")))
                scale_value = value_or_none(focus.get("analysis_scale_m"))
                f3.metric("Analysis scale", f"{float(scale_value):g} m" if scale_value is not None else "Not supplied")
            st.markdown("#### Five-group terrain fingerprint")
            show_feature_groups(fingerprints, comparison_ids)
            st.markdown("#### Single-parameter explorer")
            st.caption("Select a measurement to compare its supplied value across the target and currently selected Earth candidates.")
            show_single_parameter_explorer(fingerprints, comparison_ids)

            explanation_cols = [
                col for col in selected_rankings.columns
                if col.endswith("_contribution") or col.endswith("_difference")
            ]
            with st.expander("Matcher explanation · supplied feature contributions and differences", expanded=False):
                if explanation_cols:
                    explanation = selected_rankings[["candidate_site_id", *explanation_cols]].copy()
                    explanation = explanation.rename(columns={"candidate_site_id": "Earth candidate"})
                    st.dataframe(explanation, width="stretch", hide_index=True)
                else:
                    st.info("Per-feature differences/contributions have not been supplied by the matcher. AREA 67 does not estimate them.")

            quality_cols = [col for col in (
                "site_id", "site_name", "source_id", "analysis_scale_m",
                "valid_coverage_pct", "nodata_pct", "direct_observation_coverage_pct",
                "aoi_status", "aoi_approval", "source_checksum_sha256",
            ) if col in fingerprints.columns]
            with st.expander("Data quality & provenance comparison", expanded=False):
                if quality_cols:
                    quality = fingerprints[fingerprints["site_id"].isin(comparison_ids)][quality_cols].copy()
                    quality = quality.rename(columns={"site_id": "Site ID", "site_name": "Site", "source_id": "Source"})
                    st.dataframe(quality, width="stretch", hide_index=True)
                else:
                    st.info("No quality/provenance fields were supplied for this comparison.")

    with tab_passport:
        st.markdown(
            '<div class="a67-section"><div class="a67-section-kicker">Evidence dossier</div>'
            '<div class="a67-section-title">Analog Passport</div>'
            '<div class="a67-section-subtitle">A portable record of the selected site, its measured terrain descriptors, source lineage and known gaps.</div></div>',
            unsafe_allow_html=True,
        )
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
            with st.expander(group, expanded=(group == "Slope")):
                if values:
                    feature_rows = [
                        {
                            "Measurement": metric.replace("_", " ").title(),
                            "Value": value,
                            "Unit": value_or_none(site_row.get(f"{metric}_unit")) or "Not supplied",
                        }
                        for metric, value in values.items()
                    ]
                    st.dataframe(pd.DataFrame(feature_rows), width="stretch", hide_index=True)
                else:
                    st.write("No measurements supplied for this feature group.")
                if absent:
                    st.caption("Not measured or not supplied: " + ", ".join(absent))
        if missing_features:
            st.warning("Analog gap: some Terrain Fingerprint measurements are missing for this site. They are not replaced with zero.")
        else:
            st.success("All five feature groups have at least one supplied value. This does not by itself establish full scientific validation.")

        st.markdown("#### Source provenance and quality")
        provenance_rows = [
            {"Field": key.replace("_", " ").title(), "Value": value}
            for key, value in provenance.items()
        ]
        if provenance_rows:
            st.dataframe(pd.DataFrame(provenance_rows), width="stretch", hide_index=True)
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
            quality_rows = [
                {"Field": key.replace("_", " ").title(), "Value": value}
                for key, value in extra_quality.items()
            ]
            st.dataframe(pd.DataFrame(quality_rows), width="stretch", hide_index=True)
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
                difference_rows = [
                    {"Measurement": key.replace("_", " ").title(), "Difference": value}
                    for key, value in comparison["reported_differences"].items()
                    if value is not None
                ]
                st.dataframe(pd.DataFrame(difference_rows), width="stretch", hide_index=True)
            else:
                st.caption("The matcher has not supplied per-feature differences. The app shows original values and does not invent differences.")

        st.markdown("#### Matching, assumptions, and limitations")
        if passport["ranking"]:
            ranking_rows = [
                {"Field": key.replace("_", " ").title(), "Value": value}
                for key, value in passport["ranking"].items()
                if value is not None and not (isinstance(value, float) and pd.isna(value))
            ]
            st.dataframe(pd.DataFrame(ranking_rows), width="stretch", hide_index=True)
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
    st.markdown(
        '<div class="a67-section-subtitle">AREA 67 · Discover Earth. Explore Other Worlds. '
        'Verify sources, units, vertical references, analysis scale and data quality before interpreting cross-body comparisons.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
