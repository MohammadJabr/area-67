"""Portable evidence-bundle export for AREA 67."""
from __future__ import annotations

import io
import json
import zipfile
from typing import Any, Mapping

import pandas as pd


def build_evidence_bundle(
    passport: Mapping[str, Any],
    fingerprint_row: Mapping[str, Any],
    ranking_row: Mapping[str, Any] | None,
    passport_markdown: str,
    demo_mode: bool = False,
) -> bytes:
    """Package supplied evidence and provenance; raw DEM/LOLA assets remain external."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        readme = [
            "AREA 67 — Evidence Bundle",
            "",
            "Contents: human-readable Analog Passport, structured Passport JSON, selected",
            "terrain fingerprint CSV, and matching-result CSV when a ranking row exists.",
            "",
            "Raw DEM/LOLA rasters are not included. Use the source URLs, repository",
            "manifests and processing instructions to reproduce the analysis.",
            "This export is not an AOI approval or site-suitability certification.",
            "",
            "Synthetic demo mode: " + ("YES — synthetic fixtures." if demo_mode else "NO — loaded app result pair."),
            "Inspect scientific status, AOI approval, coverage, direct-observation support,",
            "vertical-reference caveats, units and matching assumptions before reuse.",
        ]
        archive.writestr("README.txt", "\n".join(readme))
        archive.writestr("analog_passport.md", passport_markdown)
        archive.writestr(
            "analog_passport.json",
            json.dumps(passport, ensure_ascii=False, indent=2, default=str),
        )
        archive.writestr(
            "site_terrain_fingerprint.csv",
            pd.DataFrame([dict(fingerprint_row)]).to_csv(index=False),
        )
        archive.writestr(
            "matching_result.csv",
            pd.DataFrame([dict(ranking_row)]).to_csv(index=False) if ranking_row else "",
        )
    buffer.seek(0)
    return buffer.getvalue()
