import pytest

from src.mapping.aoi_workbench import build_draft_aoi_feature_collection


def feature(coordinates):
    return {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "Polygon", "coordinates": [coordinates]},
    }


def haughton_rectangle():
    return feature([
        [-89.6820, 75.3760],
        [-89.6780, 75.3760],
        [-89.6780, 75.3790],
        [-89.6820, 75.3790],
        [-89.6820, 75.3760],
    ])


def test_draft_aoi_export_is_never_ranking_eligible():
    result = build_draft_aoi_feature_collection(
        [haughton_rectangle()],
        site_id="haughton",
        landform_label="Example mapped crater-floor unit",
        mission_question="Screen terrain for rover traverse test planning",
        source_reference="Team review placeholder",
        author="AREA 67 GIS",
        created_at="2026-11-16T10:00:00+00:00",
    )
    assert result["type"] == "FeatureCollection"
    assert result["aoi_approval"] == "NOT_APPROVED"
    assert result["review_status"] == "DRAFT_NOT_APPROVED"
    assert len(result["features"]) == 1
    props = result["features"][0]["properties"]
    assert props["ranking_eligible"] is False
    assert props["scientific_status"] == "DRAFT_GEOMETRY_ONLY"
    assert props["geometry_area_km2_geodesic"] > 0
    assert props["source_dem_id"] == "Copernicus_DSM_COG_10_N75_00_W090_00_DEM"


def test_invalid_polygon_topology_is_rejected_not_repaired():
    bow_tie = feature([
        [-89.6820, 75.3760],
        [-89.6780, 75.3790],
        [-89.6820, 75.3790],
        [-89.6780, 75.3760],
        [-89.6820, 75.3760],
    ])
    with pytest.raises(ValueError, match="invalid polygon topology"):
        build_draft_aoi_feature_collection(
            [bow_tie],
            site_id="haughton",
            landform_label="Crater-floor candidate",
            mission_question="Terrain screening",
            source_reference="Published geological map, figure 3",
        )


def test_draft_polygon_outside_catalogued_dem_tile_is_rejected():
    outside_tile = feature([
        [-90.2, 75.2],
        [-90.1, 75.2],
        [-90.1, 75.3],
        [-90.2, 75.3],
        [-90.2, 75.2],
    ])
    with pytest.raises(ValueError, match="extends beyond the currently catalogued source tile"):
        build_draft_aoi_feature_collection(
            [outside_tile],
            site_id="haughton",
            landform_label="Crater unit",
            mission_question="Terrain screening",
            source_reference="Published geological map, figure 3",
        )


def test_empty_geometry_or_missing_mission_question_is_rejected():
    with pytest.raises(ValueError, match="Draw at least one polygon"):
        build_draft_aoi_feature_collection(
            [],
            site_id="haughton",
            landform_label="Crater unit",
            mission_question="Terrain screening",
        )
    with pytest.raises(ValueError, match="mission or science question"):
        build_draft_aoi_feature_collection(
            [haughton_rectangle()],
            site_id="haughton",
            landform_label="Crater unit",
            mission_question="",
        )
