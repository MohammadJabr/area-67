"""NASA/JPL Trek WMTS map layers for Moon and Mars.

These maps are for visual exploration only. They are not automatically ingested
into AREA 67 fingerprints, AOIs, or matching results.
"""
from __future__ import annotations

import folium
from folium.plugins import Fullscreen, MousePosition


# NASA's Open APIs documentation gives this exact Moon global-tile path.
MOON_WAC_GLOBAL = (
    "https://moontrek.jpl.nasa.gov/trektiles/Moon/EQ/"
    "LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)

# NASA Trek's Mars WMTS documentation lists this MOLA global colour hillshade
# layer and the default/default028mm matrix set.
MARS_MOLA_GLOBAL_HILLSHADE = (
    "https://trek.nasa.gov/tiles/Mars/EQ/"
    "Mars_MGS_MOLA_ClrShade_merge_global_463m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)

MARS_VIKING_GLOBAL = (
    "https://trek.nasa.gov/tiles/Mars/EQ/"
    "Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)


def build_planetary_map(body: str) -> folium.Map:
    """Build a global equirectangular Folium map using NASA/JPL Trek WMTS tiles."""
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
            attr="NASA / JPL — Lunar Reconnaissance Orbiter (LROC WAC)",
            name="LRO WAC global mosaic · 303 ppd",
            overlay=False,
            control=True,
            show=True,
            max_zoom=8,
            max_native_zoom=7,
            no_wrap=True,
            tms=False,
        ).add_to(map_object)
        title = "MOON · LRO WAC GLOBAL MOSAIC"
        attribution = (
            "Global lunar visual reference from LRO WAC. This equirectangular "
            "map is not the project's Site01 LOLA raster grid."
        )
    else:
        folium.TileLayer(
            tiles=MARS_MOLA_GLOBAL_HILLSHADE,
            attr="NASA / JPL — Mars Global Surveyor MOLA",
            name="MOLA global colour hillshade · 463 m/pixel",
            overlay=False,
            control=True,
            show=True,
            max_zoom=8,
            max_native_zoom=8,
            no_wrap=True,
            tms=False,
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
            tms=False,
        ).add_to(map_object)
        title = "MARS · MOLA / VIKING GLOBAL MAPS"
        attribution = (
            "Global Mars visual reference. These map tiles are not yet inputs "
            "to an AREA 67 Mars fingerprint or ranking."
        )

    folium.LayerControl(collapsed=False, position="topright").add_to(map_object)
    Fullscreen(position="topleft").add_to(map_object)
    MousePosition(
        position="bottomleft",
        separator=" | ",
        empty_string="",
        num_digits=3,
        prefix="Lon / Lat",
    ).add_to(map_object)
    map_object.get_root().html.add_child(
        folium.Element(
            '<div style="position:absolute;z-index:999;left:12px;top:12px;'
            'background:rgba(5,13,24,.9);color:#edf5ff;padding:8px 12px;'
            'border:1px solid rgba(103,215,233,.45);border-radius:9px;'
            'font:600 12px Inter,Arial,sans-serif;pointer-events:none;">'
            + title
            + '</div>'
        )
    )
    map_object.get_root().html.add_child(
        folium.Element(
            '<div style="position:absolute;z-index:999;left:12px;bottom:34px;'
            'max-width:440px;background:rgba(5,13,24,.86);color:#d9e5f4;'
            'padding:7px 10px;border-radius:8px;font:11px Inter,Arial,sans-serif;'
            'pointer-events:none;">'
            + attribution
            + '</div>'
        )
    )
    return map_object
