import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from affine import Affine
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "data"))
from preview_invalid_roi_repairs import (  # noqa: E402
    build_repair_preview_report,
    make_valid_preview,
)
from lola_roi_quality import ASSET_NAMES  # noqa: E402


def write_rasters(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    arrays = {
        "elevation": np.arange(100, dtype="float32").reshape(10, 10) + 100,
        "counts": np.ones((10, 10), dtype="float32"),
        "slope": np.full((10, 10), 10.0, dtype="float32"),
        "z_uncertainty": np.full((10, 10), 0.4, dtype="float32"),
        "slope_uncertainty": np.full((10, 10), 2.0, dtype="float32"),
    }
    for name in ASSET_NAMES:
        path = folder / f"{name}.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=10,
            height=10,
            count=1,
            dtype="float32",
            crs="EPSG:3031",
            transform=Affine(1, 0, 0, 0, -1, 10),
        ) as dataset:
            dataset.write(arrays[name], 1)
        paths[name] = path
    return paths


def test_make_valid_preview_splits_bowtie_without_changing_source():
    bowtie = Polygon([(1, 1), (5, 5), (1, 5), (5, 1), (1, 1)])
    assert not bowtie.is_valid

    info, candidate = make_valid_preview(bowtie)

    assert info["status"] == "preview_available"
    assert "Self-intersection" in info["validity_reason"]
    assert info["polygon_component_count_before_union"] == 2
    assert candidate is not None and candidate.is_valid
    assert bowtie.is_valid is False  # original input was not changed


def test_repair_preview_lists_nonpolygonal_output_and_uses_polygon_only():
    polygon_with_cut = Polygon(
        [(1, 1), (5, 5), (1, 5), (5, 1), (1, 1)],
        [[(2, 2), (3, 3), (2, 3), (2, 2)]],
    )
    info, candidate = make_valid_preview(polygon_with_cut)
    assert info["status"] in {"preview_available", "no_polygonal_output"}
    if candidate is not None:
        assert candidate.geom_type in {"Polygon", "MultiPolygon"}
        assert candidate.is_valid


def test_report_keeps_invalid_source_stats_separate_from_preview(tmp_path):
    raster_paths = write_rasters(tmp_path / "rasters")
    roi_dir = tmp_path / "rois"
    roi_dir.mkdir()
    invalid = Polygon([(1, 1), (5, 5), (1, 5), (5, 1), (1, 1)])
    valid = box(6, 6, 9, 9)
    frame = gpd.GeoDataFrame(
        {"roi_label": ["invalid", "valid"], "geometry": [invalid, valid]},
        crs="EPSG:3031",
    )
    shapefile = roi_dir / "rois.shp"
    frame.to_file(shapefile)

    report = build_repair_preview_report(
        "Site04",
        roi_dir,
        raster_paths=raster_paths,
    )

    features = report["shapefiles"][0]["features"]
    assert report["summary"]["invalid_source_feature_count"] == 1
    assert features[0]["status"] == "repair_preview_only"
    assert features[0]["repair_preview_statistics"]["preview_only"] is True
    assert features[0]["repair_preview_statistics"]["roi_pixel_center_count"] > 0
    assert len(features[0]["repair_preview_component_statistics"]) == 2
    assert all(
        item["statistics"]["preview_only"]
        for item in features[0]["repair_preview_component_statistics"]
    )
    assert "source_statistics" not in features[0]
    assert features[1]["status"] == "valid_source_geometry"
    assert "source_statistics" in features[1]
    reread = gpd.read_file(shapefile)
    assert not reread.geometry.iloc[0].is_valid
