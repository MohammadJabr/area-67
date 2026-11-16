import numpy as np
import pytest

from src.mapping.terrain_preview import (
    EARTH_COG_SOURCES,
    derive_display_layers,
    rgba_for_terrain_layer,
)


def test_flat_surface_has_zero_slope_and_finite_hillshade():
    elevation = np.full((12, 12), 123.0, dtype=np.float32)
    slope, hillshade = derive_display_layers(elevation, pixel_size_m=30.0)
    assert np.allclose(slope, 0.0)
    assert np.isfinite(hillshade).all()
    assert hillshade.shape == elevation.shape


def test_sloped_plane_has_expected_slope():
    y, x = np.mgrid[0:12, 0:12]
    elevation = 0.1 * x * 30.0
    slope, _ = derive_display_layers(elevation, pixel_size_m=30.0)
    expected = np.degrees(np.arctan(0.1))
    assert np.allclose(slope[1:-1, 1:-1], expected, atol=1e-5)


def test_masked_cells_remain_nan_in_display_derivatives():
    elevation = np.full((12, 12), 10.0, dtype=np.float32)
    elevation[0, 0] = np.nan
    slope, hillshade = derive_display_layers(elevation, pixel_size_m=30.0)
    assert np.isnan(slope[0, 0])
    assert np.isnan(hillshade[0, 0])
    assert np.isfinite(slope[1:, 1:]).all()


def test_rgba_overlay_preserves_transparency_for_invalid_pixels():
    values = np.array([[1.0, 2.0], [np.nan, 4.0]], dtype=np.float32)
    rgba = rgba_for_terrain_layer(values, palette="terrain")
    assert rgba.shape == (2, 2, 4)
    assert rgba.dtype == np.uint8
    assert rgba[1, 0, 3] == 0
    assert rgba[0, 0, 3] == 255


def test_known_earth_preview_sources_are_explicit_and_distinct():
    assert {"haughton", "askja", "mauna_kea", "yungay"} == set(EARTH_COG_SOURCES)
    assert all(item["source_url"].startswith("https://") for item in EARTH_COG_SOURCES.values())


def test_derive_display_layers_rejects_invalid_grid():
    with pytest.raises(ValueError, match="at least 3 rows"):
        derive_display_layers(np.ones((2, 2)), pixel_size_m=30)
    with pytest.raises(ValueError, match="positive finite"):
        derive_display_layers(np.ones((5, 5)), pixel_size_m=0)
