"""AREA 67 Streamlit application. Run: streamlit run app/main.py"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.data.contracts import FEATURE_GROUPS, validate_fingerprints, validate_rankings
from src.reporting.passport import build_passport, passport_to_markdown
st.set_page_config(page_title="AREA 67 | Planetary Analog Explorer", page_icon="🪐", layout="wide")
FP = ROOT / "data/processed/terrain_fingerprints.csv"
RANK = ROOT / "data/processed/candidate_rankings.csv"
DEMO_FP = ROOT / "data/sample/demo_terrain_fingerprints.csv"
DEMO_RANK = ROOT / "data/sample/demo_candidate_rankings.csv"

def load_data():
    """Load only a complete real pair, or a complete labelled demo pair; never mix them."""
    if FP.exists() and RANK.exists():
        return pd.read_csv(FP), pd.read_csv(RANK), False, []
    if not FP.exists() and not RANK.exists() and DEMO_FP.exists() and DEMO_RANK.exists():
        return pd.read_csv(DEMO_FP), pd.read_csv(DEMO_RANK), True, []
    if FP.exists() != RANK.exists():
        missing = RANK if not RANK.exists() else FP
        return None, None, False, [f"One real output is missing: {missing.relative_to(ROOT)}. Demo data will not be mixed with real results."]
    return None, None, False, ["No processed outputs found. Add the agreed CSV pair under data/processed/."]

def show_comparison(frame: pd.DataFrame, site_ids: list[str]):
    selected = frame[frame.site_id.astype(str).isin(site_ids)].copy()
    metrics = [m for m in ["slope_median", "slope_p90", "tri_median", "local_relief_p95_p5", "spatial_pattern_metric"] if m in selected and selected[m].notna().any()]
    if metrics:
        long = selected.melt(id_vars=["site_id", "site_name"], value_vars=metrics, var_name="metric", value_name="value")
        fig = px.bar(long, x="site_name", y="value", color="site_id", facet_col="metric", facet_col_wrap=2, title="Terrain indicators (separate scales by metric)", height=560)
        fig.update_yaxes(matches=None)
        st.plotly_chart(fig, use_container_width=True)
    distribution = [m for m in FEATURE_GROUPS["Terrain distribution"] if m in selected]
    if distribution:
        long = selected[["site_name", *distribution]].melt(id_vars="site_name", var_name="terrain_class", value_name="area_percent")
        st.plotly_chart(px.bar(long, x="site_name", y="area_percent", color="terrain_class", barmode="stack", title="Terrain class distribution (%)"), use_container_width=True)

def main():
    st.title("AREA 67")
    st.caption("Planetary Analog Discovery & Mission Planning · NASA Space Apps Challenge 2026")
    st.write("Compare selected Earth terrain environments with a lunar or Martian target using documented topographic evidence.")
    fingerprints, rankings, demo, messages = load_data()
    if demo:
        st.warning("DEMO MODE — all displayed site measurements and rankings are synthetic placeholders for interface testing. They are NOT NASA measurements or validated findings.")
    for msg in messages:
        st.info(msg)
    if fingerprints is None or rankings is None:
        st.subheader("Data integration status")
        st.write("The app is ready for the shared outputs. It will not substitute invented scientific results when files are missing.")
        st.code("data/processed/terrain_fingerprints.csv\ndata/processed/candidate_rankings.csv")
        st.markdown("See `docs/INTEGRATION_CONTRACT.md` for the expected schemas.")
        st.stop()
    errors = validate_fingerprints(fingerprints) + validate_rankings(rankings)
    if errors:
        st.error("Input data do not satisfy the integration contract.")
        for error in errors:
            st.write(f"- {error}")
        st.stop()
    fingerprints["site_id"] = fingerprints.site_id.astype(str)
    rankings["candidate_site_id"] = rankings.candidate_site_id.astype(str)
    rankings["target_site_id"] = rankings.target_site_id.astype(str)
    if "site_name" not in fingerprints:
        fingerprints["site_name"] = fingerprints.site_id
    setup, results, passport_tab = st.tabs(["1 · Mission Setup", "2 · Results & Comparison", "3 · Site Passport"])
    with setup:
        st.subheader("Mission setup")
        targets = sorted(rankings.target_site_id.dropna().unique().tolist())
        target = st.selectbox("Target site", targets)
        profiles = sorted(rankings.loc[rankings.target_site_id == target, "mission_profile"].dropna().unique().tolist())
        profile = st.selectbox("Mission profile", profiles) if profiles else "Not supplied"
        target_row = fingerprints[fingerprints.site_id == target]
        st.write(f"**Target body:** {target_row.iloc[0]['planet'] if not target_row.empty else 'Not found'}")
        st.write(f"**Mission profile:** {profile}")
        st.caption("The app filters the ranking delivered by the matching module; changing this selection does not recalculate mission weights.")
    with results:
        st.subheader("Candidate results")
        targets = sorted(rankings.target_site_id.dropna().unique().tolist())
        target = st.selectbox("Target", targets, key="result_target")
        profiles = sorted(rankings.loc[rankings.target_site_id == target, "mission_profile"].dropna().unique().tolist())
        profile = st.selectbox("Mission profile", profiles, key="result_profile") if profiles else None
        ranked = rankings[(rankings.target_site_id == target) & (rankings.mission_profile == profile)].copy()
        ranked["rank"] = pd.to_numeric(ranked["rank"], errors="coerce")
        ranked["similarity_score"] = pd.to_numeric(ranked["similarity_score"], errors="coerce")
        ranked = ranked.sort_values("rank")
        merged = ranked.merge(fingerprints, left_on="candidate_site_id", right_on="site_id", how="left", suffixes=("", "_fingerprint"))
        columns = [c for c in ["rank", "candidate_site_id", "site_name", "planet", "similarity_score", "weighted_distance", "source_id", "analysis_scale_m", "nodata_pct"] if c in merged]
        st.dataframe(merged[columns], use_container_width=True, hide_index=True)
        if ranked.similarity_score.notna().any():
            st.plotly_chart(px.bar(ranked, x="candidate_site_id", y="similarity_score", color="rank", title="Relative similarity score"), use_container_width=True)
        selected_ids = [target] + ranked.candidate_site_id.tolist()
        selected_ids = [sid for sid in selected_ids if sid in set(fingerprints.site_id)]
        show_comparison(fingerprints, selected_ids)
        if {"latitude", "longitude"}.issubset(fingerprints.columns):
            mapped = fingerprints[fingerprints.site_id.isin(selected_ids)].copy()
            mapped["latitude"] = pd.to_numeric(mapped.latitude, errors="coerce")
            mapped["longitude"] = pd.to_numeric(mapped.longitude, errors="coerce")
            mapped = mapped.dropna(subset=["latitude", "longitude"])
            if not mapped.empty:
                st.plotly_chart(px.scatter_geo(mapped, lat="latitude", lon="longitude", color="planet", hover_name="site_name", hover_data=["site_id"], title="Target and candidate locations"), use_container_width=True)
        else:
            st.info("Coordinates are not included in the fingerprint file; map view is unavailable.")
        contributions = [c for c in ranked if c.endswith("_contribution")]
        if contributions:
            st.write("Per-feature ranking contributions supplied by the matching module")
            st.dataframe(ranked[["candidate_site_id", *contributions]], use_container_width=True, hide_index=True)
        st.caption("Similarity is a relative score under supplied features and weights, not a probability of mission success or site certification.")
    with passport_tab:
        st.subheader("Analog Passport")
        sites = fingerprints[["site_id", "site_name"]].drop_duplicates()
        labels = {row.site_id: f"{row.site_name} · {row.site_id}" for row in sites.itertuples()}
        selected = st.selectbox("Choose a site", sites.site_id.tolist(), format_func=lambda value: labels.get(value, value))
        site_rows = fingerprints[fingerprints.site_id == selected]
        match_rows = rankings[rankings.candidate_site_id == selected]
        match = match_rows.sort_values("rank").iloc[0].to_dict() if not match_rows.empty else None
        card = build_passport(site_rows.iloc[0].to_dict(), match)
        st.markdown(f"### {card['identity'].get('site_name', selected)}")
        st.write(f"**{card['identity'].get('planet', 'Body not specified')}** · `{selected}`")
        provenance = card["provenance"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Analysis scale", f"{provenance.get('analysis_scale_m')} m" if provenance.get("analysis_scale_m") is not None else "Not supplied")
        c2.metric("NoData", f"{provenance.get('nodata_pct')}%" if provenance.get("nodata_pct") is not None else "Not supplied")
        c3.metric("Data source", str(provenance.get("source_id", "Not supplied")))
        for group, values in card["fingerprint"].items():
            with st.expander(group, expanded=True):
                st.json(values) if values else st.write("No measurements supplied for this feature group.")
        st.write("**Provenance and limitations**")
        st.json(provenance)
        report = passport_to_markdown(card, demo_mode=demo)
        st.download_button("Download Passport (Markdown)", report, file_name=f"analog_passport_{selected}.md", mime="text/markdown")
    st.divider()
    st.caption("AREA 67 prototype · Verify source metadata, analysis scale, units, and data quality before interpreting cross-body comparisons.")

if __name__ == "__main__":
    main()
