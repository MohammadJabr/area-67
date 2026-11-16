"""Bounded, read-only terrain previews from the project's public elevation products.

Every preview is a visual inspection of an unapproved reference window. It is
not an AOI, a canonical fingerprint, or a matching input.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import rasterio
from matplotlib.colors import LightSource
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.windows import Window, from_bounds
from rasterio.warp import reproject, transform_bounds


EARTH_COG_SOURCES: dict[str, dict[str, Any]] = {
    "haughton": {
        "site_name": "Haughton Crater — reference window",
        "latitude": 75.3772222,
        "longitude": -89.68,
        "analysis_crs": "EPSG:32616",
        "source_id": "Copernicus_DSM_COG_10_N75_00_W090_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N75_00_W090_00_DEM/Copernicus_DSM_COG_10_N75_00_W090_00_DEM.tif",
        "product": "Copernicus DEM GLO-30 DSM",
        "vertical_reference": "EGM2008 (product documentation)",
        "status": "EXPLORATORY · NOT APPROVED AOI",
        "note": "Patterson & Ernst (2020) crater-centre reference. Does not delineate the central basin, final rim or apparent rim.",
    },
    "askja": {
        "site_name": "Askja — held reference window",
        "latitude": 65.033,
        "longitude": -16.783,
        "analysis_crs": "EPSG:32628",
        "source_id": "Copernicus_DSM_COG_10_N65_00_W017_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N65_00_W017_00_DEM/Copernicus_DSM_COG_10_N65_00_W017_00_DEM.tif",
        "product": "Copernicus DEM GLO-30 DSM",
        "vertical_reference": "EGM2008 (product documentation)",
        "status": "HELD · NOT APPROVED AOI",
        "note": "Existing 990 m pilot sample was near-flat/equal-elevation dominated. This display does not assess the full caldera or lava fields.",
    },
    "mauna_kea": {
        "site_name": "Mauna Kea — reference window",
        "latitude": 19.82,
        "longitude": -155.47,
        "analysis_crs": "EPSG:32605",
        "source_id": "Copernicus_DSM_COG_10_N19_00_W156_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N19_00_W156_00_DEM/Copernicus_DSM_COG_10_N19_00_W156_00_DEM.tif",
        "product": "Copernicus DEM GLO-30 DSM",
        "vertical_reference": "EGM2008 (product documentation)",
        "status": "EXPLORATORY · NOT APPROVED AOI",
        "note": "USGS summit reference. Does not select the summit cone field, a lava surface or a flank sector.",
    },
    "yungay": {
        "site_name": "Yungay — published hyper-arid-core reference",
        "latitude": -24.0637778,
        "longitude": -69.8805,
        "analysis_crs": "EPSG:32719",
        "source_id": "Copernicus_DSM_COG_10_S25_00_W070_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_S25_00_W070_00_DEM/Copernicus_DSM_COG_10_S25_00_W070_00_DEM.tif",
        "product": "Copernicus DEM GLO-30 DSM",
        "vertical_reference": "EGM2008 (product documentation)",
        "status": "HELD · FIELD-PLOT IDENTITY NOT CONFIRMED",
        "note": "Published hyper-arid-core study reference; not confirmed as the team's intended Yungay plot.",
    },
}

EARTH_PREVIEW_SIDE_M = 990.0
EARTH_PREVIEW_PIXEL_M = 30.0
MOON_SITE01_BOUNDS_NATIVE_M = (-11825.0, -12742.5, -10835.0, -11752.5)
MOON_SITE01_LAYERS: dict[str, dict[str, str]] = {
    "ldem": {
        "label": "LOLA elevation (LDEM)",
        "unit": "m",
        "url": "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif",
        "interpretation": "Surface-interpolated elevation. Many 5 m-posted cells are interpolated between direct laser shots.",
    },
    "slope": {
        "label": "LOLA slope",
        "unit": "degrees",
        "url": "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_slp.tif",
        "interpretation": "Provider-derived slope map in degrees.",
    },
    "ldec": {
        "label": "LOLA direct-shot count (LDEC)",
        "unit": "returns per pixel",
        "url": "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_ldec.tif",
        "interpretation": "Number of LOLA spots per pixel. Zero is no direct return in that cell, not NoData.",
    },
    "z_error": {
        "label": "LOLA total Z uncertainty",
        "unit": "m RMS",
        "url": "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_toterr.tif",
        "interpretation": "Provider total elevation uncertainty, reported as RMS error.",
    },
    "slope_error": {
        "label": "LOLA slope uncertainty",
        "unit": "degrees RMS",
        "url": "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_slperr.tif",
        "interpretation": "Provider slope uncertainty, reported as RMS error.",
    },
}


@dataclass(frozen=True)
class TerrainPreview:
    site_id: str
    site_name: str
    source_id: str
    source_url: str
    product: str
    vertical_reference: str
    analysis_crs: str
    display_side_m: float
    display_pixel_m: float
    elevation_m: np.ndarray
    valid_mask: np.ndarray
    slope_degrees: np.ndarray
    hillshade: np.ndarray
    bounds_latlon: list[list[float]]
    valid_coverage_pct: float
    source_status: str
    note: str


def derive_display_layers(
    elevation: np.ndarray,
    pixel_size_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate display-only slope and hillshade from an elevation array."""
    values = np.asarray(elevation, dtype=np.float64)
    valid = np.isfinite(values)
    if values.ndim != 2 or min(values.shape) < 3:
        raise ValueError("elevation must be a 2D array with at least 3 rows and columns")
    if not np.isfinite(pixel_size_m) or pixel_size_m <= 0:
        raise ValueError("pixel_size_m must be a positive finite value")
    if int(valid.sum()) < 9:
        raise ValueError("elevation array contains too few valid cells")

    if not valid.all():
        # Nearest-neighbour fill is used only to stabilize display derivatives.
        # The original invalid cells are masked again in the returned layers.
        from scipy.ndimage import distance_transform_edt

        nearest = distance_transform_edt(~valid, return_distances=False, return_indices=True)
        filled = values[tuple(nearest)]
    else:
        filled = values

    dy, dx = np.gradient(filled, pixel_size_m, pixel_size_m)
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    light = LightSource(azdeg=315, altdeg=45)
    hillshade = light.hillshade(filled, vert_exag=1.0, dx=pixel_size_m, dy=pixel_size_m)
    slope[~valid] = np.nan
    hillshade[~valid] = np.nan
    return slope.astype(np.float32), hillshade.astype(np.float32)


def read_earth_reference_window(
    site_id: str,
    *,
    side_m: float = EARTH_PREVIEW_SIDE_M,
    pixel_m: float = EARTH_PREVIEW_PIXEL_M,
) -> TerrainPreview:
    """Read one bounded range from a public Copernicus COG and derive visual layers.

    This is a visual reference-window preview. It does not modify the canonical
    fingerprints/rankings and must not be treated as a geomorphic AOI.
    """
    if site_id not in EARTH_COG_SOURCES:
        raise ValueError(f"Unsupported Earth preview site: {site_id}")
    if side_m <= 0 or pixel_m <= 0:
        raise ValueError("side_m and pixel_m must be positive")
    site = EARTH_COG_SOURCES[site_id]
    target_crs = site["analysis_crs"]
    width = int(round(side_m / pixel_m))
    if width < 3 or not np.isclose(width * pixel_m, side_m, atol=1e-6):
        raise ValueError("side_m must be an integer multiple of pixel_m and provide at least 3 cells")

    transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    center_x, center_y = transformer.transform(site["longitude"], site["latitude"])
    half = side_m / 2.0
    left, bottom, right, top = center_x - half, center_y - half, center_x + half, center_y + half
    target_transform = from_origin(left, top, pixel_m, pixel_m)

    src_url = site["source_url"]
    vsi_url = src_url if src_url.startswith("/vsi") else f"/vsicurl/{src_url}"
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        CPL_VSIL_CURL_CACHE_SIZE=str(32 * 1024 * 1024),
    ):
        with rasterio.open(vsi_url) as dataset:
            if dataset.crs is None:
                raise ValueError("Source COG does not declare a horizontal CRS")
            source_bounds = transform_bounds(
                target_crs, dataset.crs, left, bottom, right, top, densify_pts=21
            )
            requested_window = from_bounds(*source_bounds, transform=dataset.transform).round_offsets().round_lengths()
            full_window = Window(0, 0, dataset.width, dataset.height)
            clipped_window = requested_window.intersection(full_window)
            if (
                clipped_window.width != requested_window.width
                or clipped_window.height != requested_window.height
                or clipped_window.width <= 0
                or clipped_window.height <= 0
            ):
                raise ValueError(
                    "The full reference window is not covered by the selected Copernicus tile. "
                    "Adjacent-tile coverage must be checked before extending the study area."
                )
            source = dataset.read(1, window=clipped_window, masked=True)
            source_transform = dataset.window_transform(clipped_window)
            source_values = np.asarray(source.filled(np.nan), dtype=np.float32)
            source_valid = (
                ~np.ma.getmaskarray(source)
                & np.isfinite(source_values)
            ).astype(np.uint8)
            source_crs = dataset.crs.to_string()
            source_dtype = dataset.dtypes[0]
            source_bounds_meta = [float(v) for v in dataset.bounds]

    if source_values.size == 0 or source_valid.sum() == 0:
        raise ValueError("The bounded source read returned no valid DEM cells")

    destination = np.full((width, width), np.nan, dtype=np.float32)
    reproject(
        source=source_values,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        src_nodata=np.nan,
        dst_transform=target_transform,
        dst_crs=target_crs,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
        init_dest_nodata=True,
        num_threads=2,
    )
    valid_destination = np.zeros((width, width), dtype=np.uint8)
    reproject(
        source=source_valid,
        destination=valid_destination,
        src_transform=source_transform,
        src_crs=source_crs,
        src_nodata=0,
        dst_transform=target_transform,
        dst_crs=target_crs,
        dst_nodata=0,
        resampling=Resampling.nearest,
        init_dest_nodata=True,
        num_threads=2,
    )
    valid_mask = (valid_destination > 0) & np.isfinite(destination)
    destination[~valid_mask] = np.nan
    if valid_mask.sum() < 9:
        raise ValueError("The reprojected preview contains too few valid cells")

    slope, hillshade = derive_display_layers(destination, pixel_m)
    to_wgs84 = Transformer.from_crs(target_crs, "EPSG:4326", always_xy=True)
    corners = [
        to_wgs84.transform(left, bottom),
        to_wgs84.transform(left, top),
        to_wgs84.transform(right, bottom),
        to_wgs84.transform(right, top),
    ]
    longitudes = [point[0] for point in corners]
    latitudes = [point[1] for point in corners]
    bounds_latlon = [
        [float(min(latitudes)), float(min(longitudes))],
        [float(max(latitudes)), float(max(longitudes))],
    ]

    return TerrainPreview(
        site_id=site_id,
        site_name=site["site_name"],
        source_id=site["source_id"],
        source_url=src_url,
        product=site["product"],
        vertical_reference=site["vertical_reference"],
        analysis_crs=target_crs,
        display_side_m=side_m,
        display_pixel_m=pixel_m,
        elevation_m=destination,
        valid_mask=valid_mask,
        slope_degrees=slope,
        hillshade=hillshade,
        bounds_latlon=bounds_latlon,
        valid_coverage_pct=100.0 * float(valid_mask.mean()),
        source_status=site["status"],
        note=site["note"],
    )


def rgba_for_terrain_layer(
    array: np.ndarray,
    *,
    palette: str = "terrain",
    hillshade: bool = False,
) -> np.ndarray:
    """Convert a numeric preview array to an RGBA image for Leaflet ImageOverlay."""
    import matplotlib

    values = np.asarray(array, dtype=np.float32)
    valid = np.isfinite(values)
    if values.ndim != 2:
        raise ValueError("array must be 2D")
    if not valid.any():
        raise ValueError("array has no finite values")
    if hillshade:
        grey = np.clip(np.nan_to_num(values, nan=0.0), 0.0, 1.0)
        rgba = np.stack([grey, grey, grey, np.ones_like(grey)], axis=-1)
    else:
        low, high = np.nanpercentile(values[valid], [2, 98])
        if not np.isfinite(low) or not np.isfinite(high) or high <= low:
            low = float(np.nanmin(values[valid]))
            high = float(np.nanmax(values[valid]))
        scaled = np.zeros_like(values, dtype=np.float32)
        scaled[valid] = (values[valid] - low) / max(high - low, 1e-9)
        rgba = matplotlib.colormaps[palette](np.clip(scaled, 0, 1))
    rgba[~valid, 3] = 0.0
    return np.asarray(np.round(rgba * 255), dtype=np.uint8)


def read_lola_site01_window(
    layer_key: str,
    *,
    bounds_native_m: tuple[float, float, float, float] = (-11825.0, -12742.5, -10835.0, -11752.5),
    output_cells: int = 160,
) -> dict[str, Any]:
    """Read a bounded native-coordinate window from a NASA PGDA Site01 GeoTIFF."""
    if layer_key not in MOON_SITE01_LAYERS:
        raise ValueError(f"Unknown LOLA layer: {layer_key}")
    if output_cells < 3:
        raise ValueError("output_cells must be at least 3")
    item = MOON_SITE01_LAYERS[layer_key]
    url = item["url"]
    vsi_url = f"/vsicurl/{url}"
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        CPL_VSIL_CURL_CACHE_SIZE=str(32 * 1024 * 1024),
    ):
        with rasterio.open(vsi_url) as dataset:
            if dataset.crs is None:
                raise ValueError("NASA source GeoTIFF has no CRS metadata")
            requested = from_bounds(*bounds_native_m, transform=dataset.transform).round_offsets().round_lengths()
            full = Window(0, 0, dataset.width, dataset.height)
            window = requested.intersection(full)
            if (
                window.width != requested.width
                or window.height != requested.height
                or window.width <= 0
                or window.height <= 0
            ):
                raise ValueError("The native-coordinate screening window is outside the NASA Site01 raster.")
            data = dataset.read(
                1,
                window=window,
                out_shape=(output_cells, output_cells),
                masked=True,
                resampling=Resampling.average if layer_key == "ldec" else Resampling.bilinear,
            )
            meta = {
                "crs_wkt": dataset.crs.to_wkt(),
                "transform": [float(value) for value in dataset.transform[:6]],
                "source_width": dataset.width,
                "source_height": dataset.height,
                "posting_m": [abs(float(dataset.transform.a)), abs(float(dataset.transform.e))],
                "source_url": url,
                "layer_label": item["label"],
                "unit": item["unit"],
                "interpretation": item["interpretation"],
            }
            source_transform = dataset.window_transform(window)
            out_transform = source_transform * source_transform.scale(
                window.width / output_cells,
                window.height / output_cells,
            )
    values = np.asarray(data.filled(np.nan), dtype=np.float32)
    valid = np.isfinite(values)
    return {
        "layer_key": layer_key,
        "label": item["label"],
        "unit": item["unit"],
        "interpretation": item["interpretation"],
        "values": values,
        "valid_mask": valid,
        "bounds_native_m": list(bounds_native_m),
        "x_centres_m": (
            out_transform.c + (np.arange(output_cells) + 0.5) * out_transform.a
        ).tolist(),
        "y_centres_m": (
            out_transform.f + (np.arange(output_cells) + 0.5) * out_transform.e
        ).tolist(),
        "valid_coverage_pct": 100.0 * float(valid.mean()),
        "metadata": meta,
    }
