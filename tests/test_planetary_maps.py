import pytest

from src.mapping.planetary import (
    MARS_MOLA_GLOBAL_HILLSHADE,
    MOON_WAC_GLOBAL,
    build_planetary_map,
)


def test_moon_map_uses_documented_nasa_lro_wac_wmts():
    map_object = build_planetary_map("moon")
    markup = map_object.get_root().render()
    assert "LRO_WAC_Mosaic_Global_303ppd_v02" in markup
    assert "moontrek.jpl.nasa.gov/trektiles" in markup
    assert "NASA / JPL" in markup


def test_mars_map_has_mola_and_viking_layers():
    map_object = build_planetary_map("mars")
    markup = map_object.get_root().render()
    assert "Mars_MGS_MOLA_ClrShade_merge_global_463m" in markup
    assert "Mars_Viking_MDIM21_ClrMosaic_global_232m" in markup


def test_unknown_planet_is_rejected():
    with pytest.raises(ValueError, match="body must be"):
        build_planetary_map("venus")


def test_wmts_definitions_keep_https_and_tile_placeholders():
    assert MOON_WAC_GLOBAL.startswith("https://")
    assert MARS_MOLA_GLOBAL_HILLSHADE.startswith("https://")
    for template in (MOON_WAC_GLOBAL, MARS_MOLA_GLOBAL_HILLSHADE):
        assert all(token in template for token in ("{z}", "{y}", "{x}"))
