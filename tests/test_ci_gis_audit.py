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
