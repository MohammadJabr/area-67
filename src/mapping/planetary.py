"""Official NASA Trek WMTS map definitions for the Moon and Mars.

These are live visualization layers. They are not automatically ingested into
AREA 67 fingerprints or matching results.
"""
from __future__ import annotations

import folium


MOON_WAC_GLOBAL = (
    "https://trek.nasa.gov/tiles/Moon/EQ/"
    "LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)
MARS_MOLA_GLOBAL_HILLSHADE = (
    "https://trek.nasa.gov/tiles/Mars/EQ/"
    "Mars_MGS_MOLA_ClrShade_merge_global_463m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)
MARS_VIKING_GLOBAL = (
    "https://trek.nasa.gov/tiles/Mars/EQ/"
    "Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)


def build_planetary_map(body: str) -> folium.Map:
    """Build an equirectangular Folium map using live official NASA Trek tiles."""
    normalized = body.strip().casefold()
    if normalized not in {"moon", "mars"}:
        raise ValueError("body must be 'moon' or 'mars'")

    map_object = folium.Map(
        location=[0, 0],
        zoom_start=1,
        min_zoom=0,
        max_zoom=8,
        crs="EPSG4326",
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    if normalized == "moon":
        folium.TileLayer(
            tiles=MOON_WAC_GLOBAL,
            attr="NASA / JPL / LRO — LROC Wide Angle Camera global mosaic",
            name="LRO WAC global mosaic · 303 ppd",
            overlay=False,
            control=True,
            show=True,
            max_zoom=8,
            max_native_zoom=7,
            no_wrap=True,
        ).add_to(map_object)
        title = "Moon — LRO WAC global mosaic"
    else:
        folium.TileLayer(
            tiles=MARS_MOLA_GLOBAL_HILLSHADE,
            attr="NASA / JPL / MGS MOLA",
            name="MOLA global colour hillshade · 463 m/pixel",
            overlay=False,
            control=True,
            show=True,
            max_zoom=8,
            max_native_zoom=8,
            no_wrap=True,
        ).add_to(map_object)
        folium.TileLayer(
            tiles=MARS_VIKING_GLOBAL,
            attr="NASA / JPL / USGS — Viking MDIM 2.1",
            name="Viking global colour mosaic · 232 m/pixel",
            overlay=False,
            control=True,
            show=False,
            max_zoom=8,
            max_native_zoom=8,
            no_wrap=True,
        ).add_to(map_object)
        title = "Mars — MOLA / Viking global map layers"

    folium.LayerControl(collapsed=False, position="topright").add_to(map_object)
    folium.plugins.Fullscreen(position="topleft").add_to(map_object)
    folium.plugins.MousePosition(
        position="bottomleft",
        separator=" | ",
        empty_string="",
        num_digits=3,
        prefix="Lon / Lat",
    ).add_to(map_object)
    map_object.get_root().html.add_child(
        folium.Element(
            '<div style="position:absolute;z-index:999;left:12px;top:12px;'
            'background:rgba(5,13,24,.88);color:#edf5ff;padding:8px 12px;'
            'border:1px solid rgba(103,215,233,.45);border-radius:9px;'
            'font:600 12px Inter,Arial,sans-serif;pointer-events:none;">'
            + title
            + '</div>'
        )
    )
    return map_object
