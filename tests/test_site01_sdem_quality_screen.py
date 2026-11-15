import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from src.data import site01_sdem_quality_screen as m

LUNAR = rasterio.crs.CRS.from_proj4(
    "+proj=stere +lat_0=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs"
)


def write_raster(path: Path, arr: np.ndarray, transform, crs=LUNAR, nodata=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", width=arr.shape[1], height=arr.shape[0],
                       count=1, dtype=arr.dtype, crs=crs, transform=transform,
                       nodata=nodata) as dataset:
        dataset.write(arr, 1)


def make_inputs(root: Path):
    roi_dir = root / "data/raw/moon/roi_shapes/Site01"
    roi_dir.mkdir(parents=True, exist_ok=True)
    polygons = [
        box(-995, -995, -955, -955),
        box(-945, -995, -905, -955),
        box(-895, -995, -855, -955),
        box(-845, -995, -805, -955),
        box(-795, -995, -755, -955),
    ]
    gdf = gpd.GeoDataFrame({"id": range(5)}, geometry=polygons, crs=LUNAR)
    roi_path = roi_dir / "Site01_ROIs.shp"
    gdf.to_file(roi_path)

    lola_dir = root / "data/raw/moon/site01"
    sdem_dir = root / "data/raw/moon/sdem_connecting_ridge/A3CLR22_6_Connecting_Ridge"
    transform_5m = from_origin(-1500, 0, 5, 5)
    transform_15m = from_origin(-1500, 0, 15, 15)
    values_5m = np.arange(300 * 300, dtype=np.float32).reshape(300, 300) / 100
    values_15m = np.arange(100 * 100, dtype=np.float32).reshape(100, 100)

    for filename in m.LOLA_LAYERS.values():
        write_raster(lola_dir / filename, values_5m, transform_5m, nodata=-9999)
    for name, filename in list(m.SDEM_LAYERS.items())[:5]:
        values = values_5m if name == "sdem_elevation" else values_15m
        transform = transform_5m if name == "sdem_elevation" else transform_15m
        write_raster(sdem_dir / filename, values, transform, nodata=-9999)
    return roi_path, lola_dir, sdem_dir


def test_nominal_signature_ignores_datum_label_but_checks_map_math():
    left = rasterio.crs.CRS.from_wkt(
        'PROJCS["unnamed",GEOGCS["unnamed ellipse",DATUM["unknown",SPHEROID["unnamed",1737400,0]],'
        'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],'
        'PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",-90],'
        'PARAMETER["central_meridian",0],PARAMETER["false_easting",0],'
        'PARAMETER["false_northing",0],UNIT["metre",1],AXIS["Easting",NORTH],AXIS["Northing",NORTH]]'
    )
    right = rasterio.crs.CRS.from_wkt(
        'PROJCRS["unknown",BASEGEOGCRS["unknown",DATUM["unknown",ELLIPSOID["unknown",1737400,0,LENGTHUNIT["metre",1,ID["EPSG",9001]]]],'
        'PRIMEM["Reference meridian",0,ANGLEUNIT["Degree",0.0174532925199433]]],'
        'CONVERSION["unnamed",METHOD["Polar Stereographic (variant B)",ID["EPSG",9829]],'
        'PARAMETER["Latitude of standard parallel",-90,ANGLEUNIT["Degree",0.0174532925199433],ID["EPSG",8832]],'
        'PARAMETER["Longitude of origin",0,ANGLEUNIT["Degree",0.0174532925199433],ID["EPSG",8833]],'
        'PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],'
        'PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],'
        'CS[Cartesian,2],AXIS["easting",north,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],'
        'AXIS["northing",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]'
    )
    assert m.same_nominal_polar_math(left, right)


def test_nominal_projection_check_rejects_different_standard_parallel_and_scale():
    reference = rasterio.crs.CRS.from_proj4(
        "+proj=stere +lat_0=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +k=1 +units=m"
    )
    different_parallel = rasterio.crs.CRS.from_proj4(
        "+proj=stere +lat_ts=-80 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m"
    )
    different_scale = rasterio.crs.CRS.from_proj4(
        "+proj=stere +lat_0=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +k=0.9 +units=m"
    )
    assert not m.same_nominal_polar_math(reference, different_parallel)
    assert not m.same_nominal_polar_math(reference, different_scale)


def test_summary_separates_zero_from_nonfinite():
    result = m.summarize_values(np.array([0.0, 1.0, np.nan, -9999.0]), masked_count=1)
    assert result["valid_count"] == 3
    assert result["masked_or_nonfinite_count"] == 2
    assert result["zero_pct"] == pytest.approx(100 / 3)


def test_window_sample_rejects_oversized_window(tmp_path):
    path = tmp_path / "bounded.tif"
    values = np.ones((4, 4), dtype=np.float32)
    write_raster(path, values, from_origin(0, 20, 5, 5))
    with rasterio.open(path) as dataset:
        with pytest.raises(ValueError, match="limit is 15"):
            m._window_sample(dataset, (0, 0, 20, 20), max_pixels=15)


def test_read_only_local_screen_creates_reports_without_overwriting(tmp_path):
    roi, lola, sdem = make_inputs(tmp_path)
    output_base = tmp_path / "data/metadata/screen"
    output = m.run_screen(
        sdem_root=sdem,
        roi_path=roi,
        lola_root=lola,
        output_root=output_base,
        include_remote=False,
    )
    report = json.loads((output / "site01_sdem_quality_screen.json").read_text(encoding="utf-8"))
    assert report["source_data_modified"] is False
    assert report["reprojection_performed"] is False
    assert report["coordinate_review"]["site01_vs_sdem_nominal_math_match"] is True
    assert len(report["coordinate_review"]["sdem_layer_checks"]) == len(m.SDEM_LAYERS)
    assert report["coordinate_review"]["sdem_all_expected_layers_present"] is False
    assert len(report["local_samples"]) == 10
    assert len(report["feature_samples"]) == 5
    assert (output / "site01_sdem_quality_screen.md").is_file()

    second = m.run_screen(
        sdem_root=sdem,
        roi_path=roi,
        lola_root=lola,
        output_root=output_base,
        include_remote=False,
    )
    assert second != output
