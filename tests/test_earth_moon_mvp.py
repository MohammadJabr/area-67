import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS
from rasterio.transform import from_origin
from shapely.geometry import Polygon

from scripts.run_earth_moon_mvp import build_site04_aoi, normalize_missing_values


def test_site04_operational_aoi_uses_exactly_registered_local_roi(tmp_path):
    lunar_crs = CRS.from_proj4(
        "+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 "
        "+a=1737400 +b=1737400 +units=m +type=crs"
    )
    dem_path = tmp_path / "dem.tif"
    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        width=1000,
        height=1000,
        count=1,
        dtype="float32",
        crs=lunar_crs.to_wkt(),
        transform=from_origin(-2500, 2500, 5, 5),
        nodata=np.nan,
    ) as dataset:
        dataset.write(np.ones((1000, 1000), dtype=np.float32), 1)
    roi_path = tmp_path / "rois.gpkg"
    # Coordinates are pixel centres on the synthetic 5 m polar grid.
    roi = Polygon([(2.5, 2.5), (12.5, 2.5), (12.5, 12.5), (2.5, 12.5)])
    gpd.GeoDataFrame({"id": [1]}, geometry=[roi], crs=lunar_crs).to_file(
        roi_path, layer="rois", driver="GPKG"
    )

    circle, center, crs, _, residual = build_site04_aoi(roi_path, dem_path, radius_m=100)

    assert circle.is_valid
    assert center == (7.5, 7.5)
    assert crs.is_projected
    assert residual == 0
    assert circle.bounds == (-92.5, -92.5, 107.5, 107.5)


def test_optional_blank_csv_values_are_null_not_imputed():
    frame = pd.DataFrame({"direct_observation_coverage_pct": [np.nan, 12.5]})

    normalized = normalize_missing_values(frame)

    assert normalized.iloc[0, 0] is None
    assert normalized.iloc[1, 0] == 12.5
