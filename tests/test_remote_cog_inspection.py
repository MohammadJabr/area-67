from io import BytesIO

import pytest

from src.data.remote_cog_inspection import (
    AssetNotFoundError,
    RemoteInspectionError,
    RemoteMetadataError,
    RangeUnsupportedError,
    get_asset_href,
    probe_http_range,
    read_remote_cog_window,
    validate_remote_metadata,
)


class Response(BytesIO):
    def __init__(self, body=b"", *, status=200, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}
        self.bytes_read = 0

    def read(self, size=-1):
        chunk = super().read(size)
        self.bytes_read += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_range_supported_response_is_bounded_and_validated():
    calls = []

    def opener(request, timeout):
        calls.append((request.get_method(), request.header_items()))
        if request.get_method() == "HEAD":
            return Response(status=200, headers={"Content-Length": "1000000"})
        return Response(b"x" * 16384, status=206, headers={
            "Content-Range": "bytes 0-16383/1000000", "Content-Length": "16384",
        })

    result = probe_http_range("https://example.test/sample.tif", open_url=opener)
    assert result == {"asset_size_bytes": 1000000, "range_probe_bytes": 16384}
    assert calls[1][0] == "GET"


def test_range_unsupported_response_stops_before_consuming_full_body():
    body = b"large" * 100_000
    response = Response(body, status=200, headers={"Content-Length": str(len(body))})

    def opener(request, timeout):
        return Response(status=200, headers={"Content-Length": str(len(body))}) if request.get_method() == "HEAD" else response

    with pytest.raises(RangeUnsupportedError, match="not attempted"):
        probe_http_range("https://example.test/no-range.tif", open_url=opener)
    assert response.bytes_read == 0


def test_missing_stac_asset_has_clear_error():
    with pytest.raises(AssetNotFoundError, match="missing"):
        get_asset_href({"assets": {}}, "dem")


def test_network_timeout_is_reported():
    def opener(request, timeout):
        raise TimeoutError("fixture timeout")

    with pytest.raises(RemoteInspectionError, match="Network error"):
        probe_http_range("https://example.test/timeout.tif", open_url=opener)


def test_incorrect_content_length_is_rejected():
    def opener(request, timeout):
        if request.get_method() == "HEAD":
            return Response(status=200, headers={"Content-Length": "100"})
        return Response(b"x" * 8, status=206, headers={
            "Content-Range": "bytes 0-15/100", "Content-Length": "8",
        })

    with pytest.raises(RemoteInspectionError, match="Content-Length"):
        probe_http_range("https://example.test/short.tif", probe_bytes=16, open_url=opener)


def test_remote_raster_metadata_validation_accepts_valid_and_rejects_invalid():
    validate_remote_metadata({
        "crs": "EPSG:4326", "width": 100, "height": 100, "count": 1,
        "transform": (1, 0, 0, 0, -1, 100),
    })
    with pytest.raises(RemoteMetadataError, match="no CRS"):
        validate_remote_metadata({
            "crs": None, "width": 100, "height": 100, "count": 1,
            "transform": (1, 0, 0, 0, -1, 100),
        })


@pytest.mark.parametrize("bounds", [
    (0, 0, 0, 1), (0, 2, 1, 1), (0, 0, float("nan"), 1),
])
def test_direct_window_rejects_invalid_bounds_before_network(bounds):
    def should_not_open(*args, **kwargs):
        pytest.fail("invalid bounds must be rejected before network access")

    with pytest.raises(ValueError, match="bounds"):
        read_remote_cog_window(
            "https://example.test/sample.tif", bounds, "EPSG:4326", open_url=should_not_open,
        )


def test_direct_window_rejects_nonpositive_pixel_limit_before_network():
    def should_not_open(*args, **kwargs):
        pytest.fail("invalid pixel limit must be rejected before network access")

    with pytest.raises(ValueError, match="max_pixels"):
        read_remote_cog_window(
            "https://example.test/sample.tif", (0, 0, 1, 1), "EPSG:4326",
            max_pixels=0, open_url=should_not_open,
        )
