import json

from src.data import ci_gis_audit


def test_build_report_serializes_nodata_nan_as_json_null(tmp_path, monkeypatch):
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    (raw_root / "synthetic_nan.tif").write_bytes(b"synthetic")

    monkeypatch.setattr(ci_gis_audit, "ROOT", tmp_path)
    monkeypatch.setattr(
        ci_gis_audit,
        "inventory_raster",
        lambda _path, checksum=True: {
            "bands": [{"statistics": {"minimum": 1.0, "maximum": float("nan")}}]
        },
    )
    monkeypatch.setattr(
        ci_gis_audit,
        "preflight_raster",
        lambda _path: {
            "status": "REVIEW",
            "checks": [{"name": "nodata", "value": float("nan")}],
        },
    )

    report = ci_gis_audit.build_report(raw_root)
    encoded = json.dumps(report, allow_nan=False)
    decoded = json.loads(encoded)

    assert decoded["raster_count"] == 1
    assert decoded["rasters"][0]["inventory"]["bands"][0]["statistics"]["maximum"] is None
    assert decoded["rasters"][0]["preflight"]["checks"][0]["value"] is None


def test_source_documentation_reads_lunar_layer_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(ci_gis_audit, "ROOT", tmp_path)
    manifest = tmp_path / "data" / "metadata" / "lunar_5mpp_manifest.csv"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        "relative_path,data_kind,value_unit,coordinate_reference_frame,frame_source_url,vertical_reference,vertical_reference_status,vertical_reference_applicable,source_product,source_url,pixel_posting_m,notes\n"
        "data/raw/moon/site01/Site01_final_adj_5mpp_slp.tif,slope,degrees,MOON_ME/DE421,https://pgda.gsfc.nasa.gov/products/78,,not_applicable,false,NASA PGDA LOLA,https://pgda.gsfc.nasa.gov/products/78,5,Slope in degrees\n",
        encoding="utf-8",
    )
    path = tmp_path / "data" / "raw" / "moon" / "site01" / "Site01_final_adj_5mpp_slp.tif"

    source = ci_gis_audit._source_documentation(path)

    assert source["data_kind"] == "slope"
    assert source["value_unit"] == "degrees"
    assert source["coordinate_reference_frame"] == "MOON_ME/DE421"
    assert source["vertical_reference_applicable"] is False
    assert source["vertical_reference"] is None


def test_source_documentation_reads_earth_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(ci_gis_audit, "ROOT", tmp_path)
    manifest = tmp_path / "data" / "metadata" / "earth_dem_manifest.csv"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        "source_id,source_name,source_url,crs,vertical_datum,elevation_unit,effective_resolution_note,quality_layers,uncertainty_note\n"
        "copernicus_tile,Copernicus DEM GLO-30 DSM,https://example.invalid/tile.tif,EPSG:4326,EGM2008 (product documentation),m (product documentation),1 arc-second grid,not included,not retrieved\n",
        encoding="utf-8",
    )
    path = tmp_path / "data" / "raw" / "earth" / "copernicus_tile.tif"

    source = ci_gis_audit._source_documentation(path)

    assert source["data_kind"] == "elevation"
    assert source["value_unit"] == "m"
    assert source["vertical_reference"] == "EGM2008"
    assert source["vertical_reference_applicable"] is True
    assert source["horizontal_crs"] == "EPSG:4326"
    assert "coordinate_reference_frame" not in source


def test_build_report_passes_layer_semantics_to_preflight(tmp_path, monkeypatch):
    raw_root = tmp_path / "data" / "raw"
    path = raw_root / "moon" / "site01" / "Site01_final_adj_5mpp_slp.tif"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"synthetic")
    manifest = tmp_path / "data" / "metadata" / "lunar_5mpp_manifest.csv"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        "relative_path,data_kind,value_unit,coordinate_reference_frame,frame_source_url,vertical_reference,vertical_reference_status,vertical_reference_applicable,source_product,source_url,pixel_posting_m,notes\n"
        "data/raw/moon/site01/Site01_final_adj_5mpp_slp.tif,slope,degrees,MOON_ME/DE421,https://pgda.gsfc.nasa.gov/products/78,,not_applicable,false,NASA PGDA LOLA,https://pgda.gsfc.nasa.gov/products/78,5,Slope in degrees\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ci_gis_audit, "ROOT", tmp_path)
    monkeypatch.setattr(ci_gis_audit, "inventory_raster", lambda _path, checksum=True: {"bands": []})
    captured = {}

    def fake_preflight(_path, **kwargs):
        captured.update(kwargs)
        return {"status": "PASS", "checks": []}

    monkeypatch.setattr(ci_gis_audit, "preflight_raster", fake_preflight)

    report = ci_gis_audit.build_report(raw_root)

    assert report["rasters"][0]["source_documentation"]["data_kind"] == "slope"
    assert captured["data_kind"] == "slope"
    assert captured["value_unit"] == "degrees"
    assert captured["vertical_reference_applicable"] is False
    assert captured["coordinate_reference_frame"] == "MOON_ME/DE421"


def test_markdown_separates_earth_horizontal_crs_from_lunar_frame():
    report = {
        "generated_at_utc": "2026-11-15T00:00:00+00:00",
        "raster_count": 2,
        "status_counts": {"PASS": 1, "REVIEW": 1, "FAIL": 0},
        "rasters": [
            {
                "path": "data/raw/earth/copernicus_tile.tif",
                "inventory": {"bands": []},
                "preflight": {"status": "REVIEW"},
                "source_documentation": {
                    "data_kind": "elevation",
                    "value_unit": "m",
                    "horizontal_crs": "EPSG:4326",
                    "coordinate_reference_frame": None,
                    "vertical_reference": "EGM2008",
                    "vertical_reference_applicable": True,
                    "source_url": "https://example.invalid/earth",
                },
            },
            {
                "path": "data/raw/moon/site01/Site01_final_adj_5mpp_slp.tif",
                "inventory": {"bands": []},
                "preflight": {"status": "PASS"},
                "source_documentation": {
                    "data_kind": "slope",
                    "value_unit": "degrees",
                    "horizontal_crs": None,
                    "coordinate_reference_frame": "MOON_ME/DE421",
                    "vertical_reference": None,
                    "vertical_reference_applicable": False,
                    "source_url": "https://pgda.gsfc.nasa.gov/products/78",
                },
            },
        ],
        "errors": [],
    }

    markdown = ci_gis_audit._markdown(report)

    assert "| copernicus_tile.tif | elevation | m | EPSG:4326 | — | EGM2008 |" in markdown
    assert "| Site01_final_adj_5mpp_slp.tif | slope | degrees | — | MOON_ME/DE421 | not applicable |" in markdown
