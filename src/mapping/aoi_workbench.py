"""Draft-only Earth AOI tools. Nothing created here is scientifically approved."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from pyproj import Geod
from shapely.geometry import shape
from shapely.validation import explain_validity

EARTH_SITE_CATALOG = {
    "haughton": {
        "site_name": "Haughton Crater, Devon Island",
        "latitude": 75.3772222, "longitude": -89.68, "analysis_crs": "EPSG:32616",
        "source_id": "Copernicus_DSM_COG_10_N75_00_W090_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N75_00_W090_00_DEM/Copernicus_DSM_COG_10_N75_00_W090_00_DEM.tif",
        "reference_source": "Patterson & Ernst (2020), crater-centre reference",
        "reference_url": "https://doi.org/10.1111/maps.13573",
        "source_coverage_bounds_wgs84": [-90.0004167, 75.0001389, -89.0004167, 76.0001389],
        "candidate_status": "PRIMARY CANDIDATE · AOI NOT APPROVED",
        "landform_guidance": "Choose a specific mapped unit: central basin, final rim/faulted terraces, or crater-fill unit. Do not draw one circle for the full apparent crater.",
    },
    "askja": {
        "site_name": "Askja, Iceland",
        "latitude": 65.033, "longitude": -16.783, "analysis_crs": "EPSG:32628",
        "source_id": "Copernicus_DSM_COG_10_N65_00_W017_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N65_00_W017_00_DEM/Copernicus_DSM_COG_10_N65_00_W017_00_DEM.tif",
        "reference_source": "Smithsonian Global Volcanism Program — Askja",
        "reference_url": "https://volcano.si.edu/volcano.cfm?vn=373060",
        "source_coverage_bounds_wgs84": [-17.0002778, 65.0001389, -16.0002778, 66.0001389],
        "candidate_status": "PRIMARY SHORTLIST · AOI NOT APPROVED",
        "landform_guidance": "Select a named caldera, crater, lava field or other volcanic unit. The volcano reference point is not an AOI.",
    },
    "mauna_kea": {
        "site_name": "Mauna Kea, Hawaiʻi",
        "latitude": 19.82, "longitude": -155.47, "analysis_crs": "EPSG:32605",
        "source_id": "Copernicus_DSM_COG_10_N19_00_W156_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N19_00_W156_00_DEM/Copernicus_DSM_COG_10_N19_00_W156_00_DEM.tif",
        "reference_source": "USGS Hawaiian Volcano Observatory — Mauna Kea",
        "reference_url": "https://www.usgs.gov/volcanoes/mauna-kea",
        "source_coverage_bounds_wgs84": [-156.0001389, 19.0001389, -155.0001389, 20.0001389],
        "candidate_status": "PRIMARY CANDIDATE · AOI NOT APPROVED",
        "landform_guidance": "Choose a summit-cone field, lava surface, glacially modified unit or flank sector. Do not use the whole volcano.",
    },
    "yungay": {
        "site_name": "Yungay hyper-arid core, Atacama",
        "latitude": -24.0637778, "longitude": -69.8805, "analysis_crs": "EPSG:32719",
        "source_id": "Copernicus_DSM_COG_10_S25_00_W070_00_DEM",
        "source_url": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_S25_00_W070_00_DEM/Copernicus_DSM_COG_10_S25_00_W070_00_DEM.tif",
        "reference_source": "Published Yungay hyper-arid-core study reference",
        "reference_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8859261/",
        "source_coverage_bounds_wgs84": [-70.0001389, -24.9998611, -69.0001389, -23.9998611],
        "candidate_status": "HELD · AREA 67 FIELD-PLOT IDENTITY NOT CONFIRMED",
        "landform_guidance": "This is a published study-site search anchor, not confirmation of the team's intended field plot. Confirm the site before digitizing.",
    },
}


def normalize_drawings(raw_drawings: Any) -> list[dict[str, Any]]:
    """Normalize streamlit-folium Draw return values to GeoJSON Features."""
    if raw_drawings is None:
        return []
    if isinstance(raw_drawings, dict):
        kind = raw_drawings.get("type")
        if kind == "FeatureCollection":
            items = raw_drawings.get("features", [])
        elif kind == "Feature":
            items = [raw_drawings]
        else:
            items = []
    elif isinstance(raw_drawings, list):
        items = raw_drawings
    else:
        return []
    return [
        item for item in items
        if isinstance(item, dict)
        and item.get("type") == "Feature"
        and isinstance(item.get("geometry"), dict)
    ]


def build_draft_aoi_feature_collection(
    drawings: Any,
    *,
    site_id: str,
    landform_label: str,
    mission_question: str,
    source_reference: str = "",
    author: str = "",
    created_at: str | None = None,
) -> dict[str, Any]:
    """Create GeoJSON whose approval status is unconditionally DRAFT_NOT_APPROVED."""
    if site_id not in EARTH_SITE_CATALOG:
        raise ValueError(f"Unknown Earth candidate site_id: {site_id}")
    normalized = normalize_drawings(drawings)
    if not normalized:
        raise ValueError("Draw at least one polygon or rectangle before exporting.")
    if not landform_label.strip():
        raise ValueError("Enter the named landform / geomorphic unit.")
    if not mission_question.strip():
        raise ValueError("Enter the mission or science question for this AOI.")

    site = EARTH_SITE_CATALOG[site_id]
    geod = Geod(ellps="WGS84")
    exported = []
    for index, feature in enumerate(normalized, start=1):
        geometry = shape(feature["geometry"])
        if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"Drawing {index} is {geometry.geom_type}; only Polygon/MultiPolygon is accepted.")
        if geometry.is_empty:
            raise ValueError(f"Drawing {index} is empty.")
        if not geometry.is_valid:
            raise ValueError(
                f"Drawing {index} has invalid polygon topology ({explain_validity(geometry)}). "
                "Edit the shape; AREA 67 will not silently repair it."
            )
        if geometry.area <= 0:
            raise ValueError(f"Drawing {index} has no usable area.")
        min_lon, min_lat, max_lon, max_lat = geometry.bounds
        if min_lon < -180 or max_lon > 180 or min_lat < -90 or max_lat > 90:
            raise ValueError(f"Drawing {index} has coordinates outside WGS84 longitude/latitude bounds.")
        west, south, east, north = site["source_coverage_bounds_wgs84"]
        if (
            min_lon < west or max_lon > east
            or min_lat < south or max_lat > north
        ):
            raise ValueError(
                f"Drawing {index} extends beyond the currently catalogued source tile for {site_id}. "
                "Acquire/check adjacent source tiles before exporting a larger draft AOI."
            )
        signed_area_m2, _ = geod.geometry_area_perimeter(geometry)
        area_km2 = abs(float(signed_area_m2)) / 1_000_000.0
        properties = {
            "aoi_id": f"AOI_DRAFT_{site_id.upper()}_{index:02d}",
            "site_id": site_id,
            "site_name": site["site_name"],
            "landform_label": landform_label.strip(),
            "mission_question": mission_question.strip(),
            "source_reference": source_reference.strip(),
            "author": author.strip(),
            "created_at_utc": created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "geometry_area_km2_geodesic": round(area_km2, 6),
            "bounds_wgs84_lon_lat": [min_lon, min_lat, max_lon, max_lat],
            "analysis_crs_proposal": site["analysis_crs"],
            "source_dem_id": site["source_id"],
            "source_dem_url": site["source_url"],
            "source_coverage_bounds_wgs84": site["source_coverage_bounds_wgs84"],
            "reference_anchor": {
                "latitude": site["latitude"],
                "longitude": site["longitude"],
                "source": site["reference_source"],
                "source_url": site["reference_url"],
            },
            "review_status": "DRAFT_NOT_APPROVED",
            "aoi_approval": "NOT_APPROVED",
            "scientific_status": "DRAFT_GEOMETRY_ONLY",
            "ranking_eligible": False,
            "approval_note": (
                "User-drawn screening geometry only. Requires source-map provenance, "
                "GIS topology/coverage checks, scale/CRS review and explicit team scientific approval."
            ),
        }
        exported.append({
            "type": "Feature",
            "id": properties["aoi_id"],
            "geometry": feature["geometry"],
            "properties": properties,
        })

    return {
        "type": "FeatureCollection",
        "name": f"AREA67_DRAFT_AOI_{site_id.upper()}",
        "coordinate_reference": "OGC:CRS84 / WGS84 longitude, latitude (RFC 7946 GeoJSON order)",
        "review_status": "DRAFT_NOT_APPROVED",
        "aoi_approval": "NOT_APPROVED",
        "features": exported,
    }


def site_catalog_rows() -> list[dict[str, Any]]:
    """Human-readable catalogue rows for the AOI workspace."""
    rows = []
    for site_id, site in EARTH_SITE_CATALOG.items():
        rows.append({
            "site_id": site_id,
            "site_name": site["site_name"],
            "candidate_status": site["candidate_status"],
            "reference_anchor": f"{site['latitude']:.6f}, {site['longitude']:.6f}",
            "landform_guidance": site["landform_guidance"],
            "reference_url": site["reference_url"],
        })
    return rows
