"""Conservative STAC and remote COG inspection using HTTP byte ranges only."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

import rasterio
from pyproj import Transformer
from rasterio.windows import Window, from_bounds


class RemoteInspectionError(RuntimeError):
    """A remote asset could not be inspected safely."""


class RangeUnsupportedError(RemoteInspectionError):
    """The server ignored or rejected a byte-range request."""


class AssetNotFoundError(RemoteInspectionError):
    """The STAC item does not contain the requested asset."""


class RemoteMetadataError(RemoteInspectionError):
    """The remote raster metadata is missing or invalid."""


@dataclass
class RemoteWindow:
    metadata: dict[str, Any]
    window: tuple[int, int, int, int]
    values: Any


def _request(url: str, *, method: str, headers: dict[str, str] | None = None,
             timeout: float, open_url: Callable[..., Any]) -> Any:
    request = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        return open_url(request, timeout=timeout)
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        raise RemoteInspectionError(f"Network error for {url}: {exc}") from exc


def read_stac_item(item_url: str, *, timeout: float = 20,
                   open_url: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    with _request(item_url, method="GET", timeout=timeout, open_url=open_url) as response:
        status = getattr(response, "status", 200)
        if status in (401, 403):
            raise RemoteInspectionError(f"STAC request requires authorization (HTTP {status}): {item_url}")
        if status >= 400:
            raise RemoteInspectionError(f"STAC request failed (HTTP {status}): {item_url}")
        try:
            item = json.loads(response.read())
        except (ValueError, TypeError) as exc:
            raise RemoteInspectionError(f"STAC response is not valid JSON: {item_url}") from exc
    if not isinstance(item, dict) or not isinstance(item.get("assets"), dict):
        raise RemoteInspectionError("STAC item has no assets object")
    return item


def get_asset_href(item: dict[str, Any], asset_key: str) -> str:
    asset = item.get("assets", {}).get(asset_key)
    if not isinstance(asset, dict) or not asset.get("href"):
        raise AssetNotFoundError(f"STAC asset is missing: {asset_key}")
    return str(asset["href"])


def probe_http_range(asset_url: str, *, probe_bytes: int = 16_384, timeout: float = 20,
                     open_url: Callable[..., Any] = urllib.request.urlopen) -> dict[str, int]:
    """Confirm a bounded range works before GDAL sees the URL; never consume a full 200 body."""
    if probe_bytes < 1:
        raise ValueError("probe_bytes must be positive")
    with _request(asset_url, method="HEAD", timeout=timeout, open_url=open_url) as response:
        status = getattr(response, "status", 200)
        if status in (401, 403):
            raise RemoteInspectionError(f"Asset requires authorization (HTTP {status}): {asset_url}")
        if status >= 400:
            raise RemoteInspectionError(f"Asset HEAD failed (HTTP {status}): {asset_url}")
        try:
            total = int(response.headers["Content-Length"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RemoteInspectionError("Asset HEAD did not provide a valid Content-Length") from exc
        if total <= 0:
            raise RemoteInspectionError(f"Asset has invalid Content-Length: {total}")

    requested = min(probe_bytes, total)
    end = requested - 1
    with _request(asset_url, method="GET", headers={"Range": f"bytes=0-{end}"},
                  timeout=timeout, open_url=open_url) as response:
        status = getattr(response, "status", 200)
        if status in (401, 403):
            raise RemoteInspectionError(f"Asset range requires authorization (HTTP {status}): {asset_url}")
        if status != 206:
            raise RangeUnsupportedError(
                f"Server did not honor the bounded byte range (HTTP {status}); GDAL read was not attempted"
            )
        content_range = response.headers.get("Content-Range", "")
        match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range)
        if not match or tuple(map(int, match.groups())) != (0, end, total):
            raise RemoteInspectionError(f"Incorrect Content-Range response: {content_range!r}")
        declared_length = response.headers.get("Content-Length")
        if declared_length is not None and declared_length != str(requested):
            raise RemoteInspectionError(
                f"Incorrect range Content-Length {declared_length}; expected {requested}"
            )
        body = response.read(requested + 1)
        if len(body) != requested:
            raise RemoteInspectionError(
                f"Incorrect range response body length {len(body)}; expected {requested}"
            )
    return {"asset_size_bytes": total, "range_probe_bytes": requested}


def validate_remote_metadata(metadata: dict[str, Any]) -> None:
    """Reject incomplete georeferencing or nonsensical dimensions before reading pixels."""
    if not metadata.get("crs"):
        raise RemoteMetadataError("Remote raster has no CRS")
    width, height = metadata.get("width", 0), metadata.get("height", 0)
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise RemoteMetadataError("Remote raster dimensions are invalid")
    if not isinstance(metadata.get("count"), int) or metadata["count"] <= 0:
        raise RemoteMetadataError("Remote raster band count is invalid")
    if len(metadata.get("transform", ())) != 6:
        raise RemoteMetadataError("Remote raster affine transform is missing or incomplete")


def read_remote_window(
    item_url: str,
    asset_key: str,
    bounds: tuple[float, float, float, float],
    bounds_crs: str,
    *,
    max_pixels: int = 262_144,
    timeout: float = 20,
    open_url: Callable[..., Any] = urllib.request.urlopen,
) -> RemoteWindow:
    """Read a small window from a STAC COG, after proving byte-range support.

    The window is defined by an input bbox and CRS. This function never writes a
    raster, and refuses windows over ``max_pixels`` to keep previews bounded.
    """
    if len(bounds) != 4 or not all(map(lambda value: isinstance(value, (int, float)), bounds)):
        raise ValueError("bounds must be four numeric coordinates")
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValueError("bounds must have positive width and height")
    item = read_stac_item(item_url, timeout=timeout, open_url=open_url)
    asset_url = get_asset_href(item, asset_key)
    result = read_remote_cog_window(
        asset_url, bounds, bounds_crs, max_pixels=max_pixels, timeout=timeout,
        open_url=open_url,
    )
    result.metadata["stac_item_id"] = item.get("id")
    result.metadata["stac_asset_key"] = asset_key
    return result


def read_remote_cog_window(
    asset_url: str,
    bounds: tuple[float, float, float, float],
    bounds_crs: str,
    *,
    max_pixels: int = 262_144,
    timeout: float = 20,
    open_url: Callable[..., Any] = urllib.request.urlopen,
) -> RemoteWindow:
    """Read a bounded window from a direct COG URL after an HTTP range preflight."""
    if len(bounds) != 4 or not all(
        isinstance(value, (int, float)) and value == value and abs(value) != float("inf")
        for value in bounds
    ):
        raise ValueError("bounds must be four finite numeric coordinates")
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValueError("bounds must have positive width and height")
    if max_pixels <= 0:
        raise ValueError("max_pixels must be positive")
    probe = probe_http_range(asset_url, timeout=timeout, open_url=open_url)
    try:
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_USE_HEAD="YES",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff",
            VSI_CACHE="FALSE",
            GDAL_HTTP_TIMEOUT=str(max(1, int(timeout))),
        ):
            with rasterio.open("/vsicurl/" + asset_url) as dataset:
                metadata = {
                    "crs": dataset.crs.to_string() if dataset.crs else None,
                    "width": dataset.width,
                    "height": dataset.height,
                    "count": dataset.count,
                    "dtype": list(dataset.dtypes),
                    "bounds": tuple(dataset.bounds),
                    "transform": tuple(dataset.transform)[:6],
                    "nodata": dataset.nodata,
                    "block_shapes": dataset.block_shapes,
                    "overviews": dataset.overviews(1) if dataset.count else [],
                }
                validate_remote_metadata(metadata)
                transformer = Transformer.from_crs(bounds_crs, dataset.crs, always_xy=True)
                left, bottom, right, top = transformer.transform_bounds(*bounds, densify_pts=21)
                requested_window = from_bounds(left, bottom, right, top, dataset.transform)
                requested_window = requested_window.round_offsets().round_lengths()
                window = requested_window.intersection(Window(0, 0, dataset.width, dataset.height))
                if window.width <= 0 or window.height <= 0:
                    raise RemoteMetadataError("Requested window does not intersect the remote raster")
                pixels = int(window.width) * int(window.height)
                if pixels > max_pixels:
                    raise ValueError(f"Requested window contains {pixels} pixels; limit is {max_pixels}")
                values = dataset.read(1, window=window, masked=True)
                metadata.update(probe)
                win = (int(window.col_off), int(window.row_off), int(window.width), int(window.height))
    except RemoteInspectionError:
        raise
    except (rasterio.errors.RasterioError, OSError, ValueError) as exc:
        raise RemoteInspectionError(f"Remote COG read failed for {asset_url}: {exc}") from exc
    return RemoteWindow(metadata=metadata, window=win, values=values)
