"""Streamlit UI workspaces for AREA 67's evidence-backed GIS previews."""
from __future__ import annotations

import json
from typing import Any

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

from src.mapping.aoi_workbench import (
    EARTH_SITE_CATALOG,
    build_draft_aoi_feature_collection,
)
from src.mapping.planetary import build_planetary_map
from src.mapping.terrain_preview import (
    MOON_SITE01_LAYERS,
    read_earth_reference_window,
    read_lola_site01_window,
    rgba_for_terrain_layer,
)


@st.cache_data(ttl=3600, max_entries=8, show_spinner=False)
def _cached_earth_preview(site_id: str, side_m: float):
    """Cache bounded public COG previews for an hour; never write them to disk."""
    return read_earth_reference_window(site_id, side_m=side_m, pixel_m=30.0)


@st.cache_data(ttl=3600, max_entries=8, show_spinner=False)
def _cached_lola_preview(layer_key: str):
    """Cache the bounded NASA LOLA Site01 preview for an hour."""
    return read_lola_site01_window(layer_key, output_cells=160)


def _earth_map(
    site_id: str,
    *,
    side_m: float,
    preview_layer: str | None,
    opacity: float,
    drawings: Any,
) -> folium.Map:
    site = EARTH_SITE_CATALOG[site_id]
    map_object = folium.Map(
        location=[site["latitude"], site["longitude"]],
        zoom_start=12 if side_m >= 3000 else 13,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        name="CARTO Dark",
        attr="© OpenStreetMap contributors · © CARTO",
        subdomains="abcd",
        overlay=False,
        control=True,
        show=True,
        max_zoom=20,
    ).add_to(map_object)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="OpenStreetMap",
        attr="© OpenStreetMap contributors",
        subdomains="abc",
        overlay=False,
        control=True,
        show=False,
        max_zoom=19,
    ).add_to(map_object)
    folium.Marker(
        [site["latitude"], site["longitude"]],
        tooltip=site["site_name"] + " — provisional reference anchor",
        popup=folium.Popup(
            f"<b>{site['site_name']}</b><br/>"
            f"Reference: {site['reference_source']}<br/>"
            f"<a href='{site['reference_url']}' target='_blank'>Open reference</a><br/>"
            "This point is not an AOI centre or approval.",
            max_width=320,
        ),
        icon=folium.Icon(color="lightblue", icon="info-sign"),
    ).add_to(map_object)

    if preview_layer:
        preview = _cached_earth_preview(site_id, side_m)
        if preview_layer == "Elevation":
            rgba = rgba_for_terrain_layer(preview.elevation_m, palette="terrain")
            units = "metres (EGM2008 product reference)"
        elif preview_layer == "Slope":
            rgba = rgba_for_terrain_layer(preview.slope_degrees, palette="magma")
            units = "degrees · derived for visual inspection only"
        else:
            rgba = rgba_for_terrain_layer(preview.hillshade, hillshade=True)
            units = "relative illumination · display derivative"
        folium.raster_layers.ImageOverlay(
            image=rgba,
            bounds=preview.bounds_latlon,
            opacity=opacity,
            name=f"{preview_layer} · {side_m:,.0f} m reference window",
            interactive=True,
            cross_origin=False,
            zindex=2,
        ).add_to(map_object)
        folium.Marker(
            [site["latitude"], site["longitude"]],
            icon=folium.DivIcon(
                html=(
                    '<div style="font:700 11px Inter,Arial,sans-serif;'
                    'background:rgba(8,18,31,.86);color:#eaf5ff;'
                    'border:1px solid #69d9e8;border-radius:6px;'
                    'padding:3px 6px;white-space:nowrap;">'
                    f"{preview_layer} · {units}"
                    "</div>"
                )
            ),
            interactive=False,
        ).add_to(map_object)

    current_features = []
    if isinstance(drawings, dict) and drawings.get("type") == "FeatureCollection":
        current_features = drawings.get("features", [])
    elif isinstance(drawings, list):
        current_features = drawings
    elif isinstance(drawings, dict) and drawings.get("type") == "Feature":
        current_features = [drawings]
    if current_features:
        folium.GeoJson(
            {"type": "FeatureCollection", "features": current_features},
            name="Your AOI draft drawings",
            style_function=lambda _: {
                "color": "#b9f36b",
                "weight": 3,
                "fillColor": "#b9f36b",
                "fillOpacity": 0.13,
            },
        ).add_to(map_object)

    Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "marker": False,
            "circle": False,
            "circlemarker": False,
            "polygon": True,
            "rectangle": True,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(map_object)
    folium.LayerControl(collapsed=False, position="topright").add_to(map_object)
    return map_object


def render_earth_aoi_workbench() -> None:
    st.markdown(
        "#### Earth terrain explorer & AOI workbench",
    )
    st.caption(
        "Inspect a bounded Copernicus GLO-30 reference window, then draw a candidate polygon or rectangle. "
        "Every export is marked DRAFT_NOT_APPROVED and is excluded from matching."
    )
    site_id = st.selectbox(
        "Earth candidate / reference location",
        options=list(EARTH_SITE_CATALOG),
        format_func=lambda key: EARTH_SITE_CATALOG[key]["site_name"],
        key="area67_aoi_site",
    )
    site = EARTH_SITE_CATALOG[site_id]
    status_col, source_col = st.columns(2)
    status_col.info(site["candidate_status"])
    source_col.markdown(
        f"**Source:** {site['source_id']}  \n"
        f"**Reference:** [{site['reference_source']}]({site['reference_url']})"
    )
    st.write(site["landform_guidance"])

    controls = st.columns([1.0, 1.1, 1.0, 1.0])
    side_m = controls[0].selectbox(
        "Preview width",
        options=[990.0, 1980.0, 2970.0, 4950.0],
        format_func=lambda value: f"{value:,.0f} m",
        index=0,
        key=f"area67_preview_width_{site_id}",
    )
    preview_choice = controls[1].selectbox(
        "Terrain overlay",
        options=["Off", "Elevation", "Slope", "Hillshade"],
        key=f"area67_preview_layer_{site_id}",
        help="Slope and hillshade are calculated only for visualization. They do not update the scored fingerprints.",
    )
    opacity = controls[2].slider(
        "Overlay opacity", min_value=0.15, max_value=1.0, value=0.78, step=0.05,
        key=f"area67_preview_opacity_{site_id}",
    )
    controls[3].markdown(
        f"**Grid:** 30 m nominal  \n**Coverage:** one source tile",
    )

    preview_layer = None if preview_choice == "Off" else preview_choice
    drawings_by_site = st.session_state.setdefault("area67_aoi_drawings", {})
    drawings = drawings_by_site.get(site_id, [])

    try:
        map_object = _earth_map(
            site_id,
            side_m=side_m,
            preview_layer=preview_layer,
            opacity=opacity,
            drawings=drawings,
        )
    except Exception as exc:
        st.error(
            "The bounded Copernicus reference-window preview could not be loaded. "
            "You can still use the base map and prepare a draft AOI."
        )
        st.caption(f"Preview detail: {type(exc).__name__}: {exc}")
        map_object = _earth_map(
            site_id, side_m=side_m, preview_layer=None, opacity=opacity, drawings=drawings
        )

    map_state = st_folium(
        map_object,
        width=1320,
        height=610,
        returned_objects=["all_drawings"],
        key=f"area67_earth_aoi_map_{site_id}",
    )
    returned_drawings = map_state.get("all_drawings")
    if returned_drawings is not None:
        drawings_by_site[site_id] = returned_drawings
    drawings = drawings_by_site.get(site_id, [])
    if isinstance(drawings, dict):
        if drawings.get("type") == "FeatureCollection":
            drawing_count = len(drawings.get("features", []))
        elif drawings.get("type") == "Feature":
            drawing_count = 1
        else:
            drawing_count = 0
    elif isinstance(drawings, list):
        drawing_count = len(drawings)
    else:
        drawing_count = 0

    if preview_layer:
        try:
            preview = _cached_earth_preview(site_id, side_m)
            st.caption(
                f"Preview source: {preview.product}; source window: {preview.display_side_m:,.0f} × "
                f"{preview.display_side_m:,.0f} m; display grid: {preview.display_pixel_m:g} m; "
                f"valid preview coverage: {preview.valid_coverage_pct:.2f}%. "
                "The map uses a geographic bounding envelope for display; it is not an analysis raster."
            )
            with st.expander("Preview provenance and limitations", expanded=False):
                st.write(f"Source ID: {preview.source_id}")
                st.write(f"Vertical reference: {preview.vertical_reference}")
                st.write(f"Source: {preview.source_url}")
                st.write(preview.note)
                st.warning(
                    "Display-only resampling and derivatives do not establish effective resolution, "
                    "AOI approval, or cross-site comparability."
                )
        except Exception:
            pass

    st.markdown(f"**Drawn geometries:** {drawing_count}")
    with st.form(f"area67_aoi_metadata_{site_id}"):
        landform_label = st.text_input(
            "Named landform / geomorphic unit",
            placeholder="e.g., selected crater-floor unit or lava-flow field",
        )
        mission_question = st.text_area(
            "Mission or science question",
            value="Which terrain characteristics of this Earth landform should be inspected for rover terrain-traversal testing?",
            height=90,
        )
        source_reference = st.text_input(
            "Boundary source / map reference",
            placeholder="Citation, geological map sheet, figure, or field boundary source",
        )
        author = st.text_input("Prepared by", placeholder="Team member")
        prepare = st.form_submit_button(
            "Validate geometry & prepare draft GeoJSON",
            type="primary",
            use_container_width=True,
        )

    if prepare:
        try:
            draft = build_draft_aoi_feature_collection(
                drawings,
                site_id=site_id,
                landform_label=landform_label,
                mission_question=mission_question,
                source_reference=source_reference,
                author=author,
            )
            st.session_state["area67_validated_aoi_draft"] = {
                "site_id": site_id,
                "feature_collection": draft,
            }
            total_area = sum(
                item["properties"]["geometry_area_km2_geodesic"]
                for item in draft["features"]
            )
            st.success(
                f"Geometry checks passed. {len(draft['features'])} draft feature(s), "
                f"{total_area:,.4f} km² total geodesic area."
            )
        except Exception as exc:
            st.session_state.pop("area67_validated_aoi_draft", None)
            st.error(f"Draft AOI validation failed: {exc}")

    saved = st.session_state.get("area67_validated_aoi_draft")
    if saved and saved.get("site_id") == site_id:
        draft = saved["feature_collection"]
        st.warning(
            "DRAFT_NOT_APPROVED — this geometry is not an approved study AOI and cannot enter the matching engine."
        )
        area_rows = [
            {
                "AOI ID": feature["properties"]["aoi_id"],
                "Landform": feature["properties"]["landform_label"],
                "Area (km²)": feature["properties"]["geometry_area_km2_geodesic"],
                "Review status": feature["properties"]["review_status"],
                "Ranking eligible": feature["properties"]["ranking_eligible"],
            }
            for feature in draft["features"]
        ]
        st.dataframe(pd.DataFrame(area_rows), width="stretch", hide_index=True)
        st.download_button(
            "Download draft AOI GeoJSON",
            data=json.dumps(draft, ensure_ascii=False, indent=2),
            file_name=f"AREA67_DRAFT_AOI_{site_id.upper()}.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )
        st.caption(
            "The export records the source tile extent and proposed projected CRS, but does not transform, "
            "clip, fingerprint, or approve the geometry."
        )

    with st.expander("Candidate reference catalogue", expanded=False):
        catalogue = [
            {
                "Site": key,
                "Status": value["candidate_status"],
                "Reference anchor": f"{value['latitude']:.6f}, {value['longitude']:.6f}",
                "Source": value["reference_source"],
            }
            for key, value in EARTH_SITE_CATALOG.items()
        ]
        st.dataframe(pd.DataFrame(catalogue), width="stretch", hide_index=True)


def render_moon_surface_lab() -> None:
    st.markdown("#### Moon — NASA LOLA Site01 surface lab")
    st.write(
        "Load a bounded preview from the current Site01 Connecting Ridge screening window. "
        "The raster is shown in its stored local grid coordinates, not on a geographic basemap."
    )
    layer_labels = {
        key: value["label"] for key, value in MOON_SITE01_LAYERS.items()
    }
    selected_layer = st.selectbox(
        "NASA LOLA source layer",
        options=list(MOON_SITE01_LAYERS),
        format_func=lambda key: layer_labels[key],
        key="area67_moon_lola_layer",
    )
    load_layer = st.toggle(
        "Load bounded NASA source raster preview",
        value=False,
        key="area67_moon_lola_load",
        help="Loads a small bounded window by HTTP range requests. The source raster is not downloaded in full.",
    )
    st.caption(
        "Source: [NASA PGDA LOLA Product 78](https://pgda.gsfc.nasa.gov/products/78). "
        "Stored Site01 native raster grid; local physical-frame caveats remain. Preview is downsampled to 160 × 160."
    )
    if not load_layer:
        st.info("Turn on the preview switch to request the bounded NASA GeoTIFF window.")
        return

    try:
        with st.spinner("Reading the bounded NASA LOLA window..."):
            result = _cached_lola_preview(selected_layer)
        values = np.asarray(result["values"], dtype=np.float32)
        if not np.isfinite(values).any():
            st.warning("The selected LOLA window contains no valid display cells.")
            return
        scales = {
            "ldem": "Viridis",
            "slope": "Magma",
            "ldec": "Cividis",
            "z_error": "Inferno",
            "slope_error": "Plasma",
        }
        figure = px.imshow(
            values,
            x=result["x_centres_m"],
            y=result["y_centres_m"],
            origin="upper",
            aspect="equal",
            color_continuous_scale=scales[selected_layer],
            labels={"x": "Stored native grid X (m)", "y": "Stored native grid Y (m)", "color": result["unit"]},
            title=f"{result['label']} · Site01 bounded display",
        )
        figure.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,18,31,.35)",
            margin=dict(l=20, r=20, t=60, b=30),
            height=590,
        )
        figure.update_xaxes(showgrid=False)
        figure.update_yaxes(showgrid=False, scaleanchor="x", scaleratio=1)
        st.plotly_chart(
            figure,
            width="stretch",
            config={"displayModeBar": True, "scrollZoom": True, "responsive": True},
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Valid display cells", f"{int(result['valid_mask'].sum()):,} / {values.size:,}")
        c2.metric("Valid preview coverage", f"{result['valid_coverage_pct']:.2f}%")
        c3.metric("Nominal source posting", "5 m")
        st.info(result["interpretation"])
        if selected_layer == "ldec":
            st.caption(
                "LOLA count values are averaged during downsampling. This image shows a mean count per display cell, "
                "not individual laser shots or raw 5 m cells."
            )
        st.link_button(
            "Open original NASA PGDA product",
            "https://pgda.gsfc.nasa.gov/products/78",
        )
        with st.expander("Raster grid metadata", expanded=False):
            st.json(result["metadata"])
    except Exception as exc:
        st.error(
            "NASA's remote raster preview could not be loaded. This does not change the committed "
            "pilot outputs or imply that a new measurement was created."
        )
        st.caption(f"{type(exc).__name__}: {exc}")



def render_moon_surface_map() -> None:
    st.markdown("#### Moon — NASA LRO WAC global mosaic")
    st.caption(
        "Explore the global LRO Wide Angle Camera mosaic. The project-native Site01 LOLA raster preview "
        "is shown separately below because its stored local coordinate frame is not treated as geographic latitude/longitude."
    )
    map_object = build_planetary_map("moon")
    st_folium(
        map_object,
        width=1320,
        height=620,
        returned_objects=[],
        key="area67_moon_wac_wmts_map",
    )
    st.link_button("Open NASA Moon Trek", "https://trek.nasa.gov/moon/")
    st.caption(
        "Map source: NASA / JPL LRO WAC global mosaic via the official Moon Trek WMTS service."
    )

def render_mars_surface_map() -> None:
    st.markdown("#### Mars — NASA global map layers")
    st.caption(
        "Switch between the global MOLA colour hillshade and Viking visual mosaic using the map layer control. "
        "No Mars target fingerprint or Mars-to-Earth ranking is currently connected."
    )
    map_object = build_planetary_map("mars")
    st_folium(
        map_object,
        width=1320,
        height=620,
        returned_objects=[],
        key="area67_mars_wmts_map",
    )
    st.link_button("Open NASA Mars Trek", "https://trek.nasa.gov/mars/")
    st.caption(
        "Map sources: NASA / JPL Mars Trek WMTS. These visual layers are separate from the AREA 67 scored dataset."
    )
