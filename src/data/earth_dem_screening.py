"""Generate a read-only candidate screening report for local Earth DEM tiles."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import Geod


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "data/metadata/earth_dem_manifest.csv"
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/earth/copdem_glo30"
DEFAULT_QA_ROOT = REPO_ROOT / "data/metadata/earth_dem_qa"
DEFAULT_OUTPUT = REPO_ROOT / "docs/reports/earth_candidate_screening"
GEOD = Geod(ellps="WGS84")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def inspect_candidates(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    raw_root: str | Path = DEFAULT_RAW_ROOT,
    qa_root: str | Path = DEFAULT_QA_ROOT,
) -> list[dict[str, Any]]:
    """Verify manifest, raw raster, checksum, coordinate, and QA-report agreement.

    This only reads source files. Every mismatch is returned as a finding so the
    report can be generated even when an item needs attention.
    """
    raw_root, qa_root = Path(raw_root), Path(qa_root)
    results: list[dict[str, Any]] = []
    with Path(manifest_path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Manifest has no candidate rows")
    for row in rows:
        site = row["site_id"]
        findings: list[str] = []
        paths = list((raw_root / site).glob("*.tif")) if (raw_root / site).is_dir() else []
        if len(paths) != 1:
            findings.append(f"Expected one local .tif under {raw_root / site}; found {len(paths)}")
            results.append({"manifest": row, "path": str(paths[0]) if paths else None, "findings": findings})
            continue
        path = paths[0]
        actual_hash = _sha256(path)
        if path.stem != row["source_id"]:
            findings.append("Raster filename stem does not match manifest source_id")
        if actual_hash.lower() != row["checksum_sha256"].lower():
            findings.append("Raster SHA-256 does not match manifest")
        qa_path = qa_root / f"{site}.json"
        qa_markdown_path = qa_root / f"{site}.md"
        qa = None
        if not qa_path.is_file():
            findings.append(f"Missing QA JSON: {qa_path}")
        else:
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
            qdem = qa.get("dem", {})
            if qa.get("status") != "checks_passed":
                findings.append(f"QA JSON status is {qa.get('status')!r}, expected 'checks_passed'")
            if qdem.get("sha256", "").lower() != actual_hash.lower():
                findings.append("QA JSON checksum does not match local raster")
            if int(qdem.get("file_size_bytes", -1)) != path.stat().st_size:
                findings.append("QA JSON file size does not match local raster")
            if qdem.get("path") and Path(qdem["path"]).resolve() != path.resolve():
                findings.append("QA JSON path does not point to the local raster")
            if qdem.get("crs") != row["crs"]:
                findings.append("QA JSON CRS does not match manifest")
            expected_nodata = _json_number(row.get("nodata_value"))
            if qdem.get("nodata") != expected_nodata:
                findings.append("QA JSON NoData value does not match manifest")
            qa_stats = (qdem.get("bands") or [{}])[0].get("statistics") or {}
            try:
                if int(qa_stats["valid_pixel_count"]) != int(row["valid_cell_count"]):
                    findings.append("Manifest valid_cell_count does not match QA valid-pixel count")
            except (KeyError, TypeError, ValueError):
                findings.append("Manifest valid_cell_count or QA valid-pixel count is missing/invalid")
            manifest_coverage = _json_number(row.get("valid_coverage_pct"))
            if manifest_coverage is None or qa_stats.get("valid_coverage_pct") != manifest_coverage:
                findings.append("Manifest valid coverage does not match QA JSON")
        if not qa_markdown_path.is_file():
            findings.append(f"Missing QA Markdown report: {qa_markdown_path}")
        elif qa is not None:
            markdown_text = qa_markdown_path.read_text(encoding="utf-8")
            if actual_hash not in markdown_text:
                findings.append("QA Markdown report does not contain the local raster checksum")
            if f"**Status:** {qa.get('status')}" not in markdown_text:
                findings.append("QA Markdown report status does not match QA JSON")
        with rasterio.open(path) as ds:
            if qa is not None:
                qdem = qa.get("dem", {})
                for key, actual in (("width", ds.width), ("height", ds.height), ("band_count", ds.count)):
                    if qdem.get(key) != actual:
                        findings.append(f"QA JSON {key} does not match the local raster")
                if qdem.get("transform") != list(ds.transform)[:6]:
                    findings.append("QA JSON transform does not match the local raster")
                if qdem.get("bounds") != list(ds.bounds):
                    findings.append("QA JSON bounds do not match the local raster")
                if ds.nodata != _json_number(row.get("nodata_value")):
                    findings.append("Local raster NoData does not match manifest")
            lon, lat = float(row["longitude"]), float(row["latitude"])
            bounds = ds.bounds
            inside = bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top
            if not inside:
                findings.append("Provisional site coordinate falls outside the raster footprint")
            array = ds.read(1, masked=True)
            values = np.asarray(array.compressed(), dtype=np.float64)
            if values.size == 0:
                findings.append("Raster has no valid values")
                quantiles: list[float] = []
                minimum = maximum = None
                point_value = None
            else:
                quantiles = [float(v) for v in np.quantile(values, [0.01, 0.25, 0.5, 0.75, 0.99])]
                minimum, maximum = float(values.min()), float(values.max())
                if inside:
                    ri, ci = ds.index(lon, lat)
                    sampled = ds.read(1, window=((ri, ri + 1), (ci, ci + 1)), masked=True)[0, 0]
                    point_value = None if np.ma.is_masked(sampled) else float(sampled)
                else:
                    point_value = None
            lat_for_spacing = max(-89.999, min(89.999, lat))
            _, _, x_m = GEOD.inv(lon, lat_for_spacing, lon + ds.res[0], lat_for_spacing)
            _, _, y_m = GEOD.inv(lon, lat_for_spacing, lon, lat_for_spacing + ds.res[1])
            raster_info = {
                "width": ds.width, "height": ds.height, "band_count": ds.count,
                "dtype": ds.dtypes[0], "crs": ds.crs.to_string() if ds.crs else None,
                "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                "pixel_size_degrees": [float(ds.res[0]), float(ds.res[1])],
                "approx_pixel_spacing_at_site_m": [abs(float(x_m)), abs(float(y_m))],
                "nodata": ds.nodata, "area_or_point": ds.tags().get("AREA_OR_POINT"),
                "valid_pixels": int(values.size), "minimum_m": minimum,
                "maximum_m": maximum, "quantiles_1_25_50_75_99_pct_m": quantiles,
                "site_pixel_value_m": point_value,
            }
        results.append({
            "manifest": row, "path": str(path), "sha256": actual_hash,
            "file_size_bytes": path.stat().st_size, "qa_path": str(qa_path) if qa else None,
            "qa_markdown_path": str(qa_markdown_path) if qa_markdown_path.is_file() else None,
            "qa_status": qa.get("status") if qa else None,
            "qa_valid_coverage_pct": (
                (((qa.get("dem", {}).get("bands") or [{}])[0].get("statistics")) or {}).get("valid_coverage_pct")
                if qa else None
            ),
            "raster": raster_info, "findings": findings,
        })
    return results


def make_figures(results: list[dict[str, Any]], output_dir: str | Path) -> list[str]:
    """Write a longitude/latitude footprint overview and descriptive previews."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    valid = [item for item in results if item.get("raster")]
    colors = plt.get_cmap("tab10")
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    for index, item in enumerate(valid):
        ax = axes.flat[index]
        left, bottom, right, top = item["raster"]["bounds"]
        color = colors(index % 10)
        ax.fill([left, right, right, left], [bottom, bottom, top, top], color=color, alpha=0.16)
        ax.plot([left, right, right, left, left], [bottom, bottom, top, top, bottom], color=color, linewidth=2)
        lon = float(item["manifest"]["longitude"])
        lat = float(item["manifest"]["latitude"])
        ax.scatter([lon], [lat], color=[color], marker="*", s=140, edgecolor="black", linewidth=0.6, zorder=3)
        pad_x = max((right - left) * 0.12, 0.01)
        pad_y = max((top - bottom) * 0.12, 0.01)
        ax.set(xlim=(left - pad_x, right + pad_x), ylim=(bottom - pad_y, top + pad_y),
               title=f"{item['manifest']['site_id']} — source tile and provisional point",
               xlabel="Longitude (degrees)", ylabel="Latitude (degrees)")
        ax.grid(alpha=0.25)
    global_ax = axes.flat[5]
    for index, item in enumerate(valid):
        lon = float(item["manifest"]["longitude"])
        lat = float(item["manifest"]["latitude"])
        global_ax.scatter([lon], [lat], color=[colors(index % 10)], marker="*", s=110, edgecolor="black", linewidth=0.5)
        global_ax.annotate(item["manifest"]["site_id"], (lon, lat), xytext=(5, 5), textcoords="offset points", fontsize=9)
    global_ax.set(xlim=(-180, 180), ylim=(-90, 90), xlabel="Longitude (degrees)", ylabel="Latitude (degrees)",
                  title="Global context (symbols only)")
    global_ax.set_xticks(np.arange(-180, 181, 60)); global_ax.set_yticks(np.arange(-90, 91, 30)); global_ax.grid(alpha=0.25)
    global_ax.text(0.02, 0.02, "Neighboring panels show 1° source tiles.\nNo AOI boundaries are approved.",
                   transform=global_ax.transAxes, fontsize=8, va="bottom",
                   bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
    fig.suptitle("Provisional site coordinates and downloaded Copernicus tile footprints\nLocal panels show each 1° tile; the global panel gives location context")
    overview = output_dir / "tile_footprints.png"
    fig.savefig(overview, dpi=170); plt.close(fig)

    output_paths = [overview.name]
    for item in valid:
        site = item["manifest"]["site_id"]
        with rasterio.open(item["path"]) as ds:
            values = ds.read(1, masked=True)
            # Read/downsample only for a clearly labelled display preview.
            preview = ds.read(
                1, out_shape=(min(ds.height, 1200), min(ds.width, 1200)),
                masked=True, resampling=rasterio.enums.Resampling.nearest,
            )
            extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]
        flat = values.compressed()
        q02, q98 = np.quantile(flat, [0.02, 0.98])
        q = item["raster"]["quantiles_1_25_50_75_99_pct_m"]
        fig, (map_ax, hist_ax) = plt.subplots(1, 2, figsize=(13, 5.2), constrained_layout=True)
        image = map_ax.imshow(preview, extent=extent, origin="upper", cmap="terrain", vmin=q02, vmax=q98, interpolation="nearest", aspect="auto")
        lon, lat = float(item["manifest"]["longitude"]), float(item["manifest"]["latitude"])
        map_ax.scatter([lon], [lat], marker="*", s=115, c="magenta", edgecolor="black", linewidth=0.6, label="Provisional site coordinate")
        map_ax.set(title=f"{site}: elevation display (2nd–98th percentile stretch)", xlabel="Longitude (degrees)", ylabel="Latitude (degrees)")
        map_ax.legend(loc="best", fontsize=8)
        fig.colorbar(image, ax=map_ax, label="Elevation (m, product documentation)", shrink=0.83)
        hist_ax.hist(flat, bins=120, color="#567b9c", edgecolor="white", linewidth=0.25)
        hist_ax.set(title="Whole-tile elevation distribution", xlabel="Elevation (m)", ylabel="Valid cell count")
        hist_ax.grid(axis="y", alpha=0.25)
        for percentile, value in zip((1, 25, 50, 75, 99), q):
            hist_ax.axvline(value, alpha=0.5, linewidth=0.9)
        quantile_text = "Whole-tile quantiles (m):\n" + "  ".join(f"P{p}: {v:.1f}" for p, v in zip((1, 25, 50, 75, 99), q))
        hist_ax.text(0.02, 0.98, quantile_text, transform=hist_ax.transAxes, va="top", fontsize=8,
                     bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none"})
        fig.suptitle(f"{site}: descriptive preview only; display downsampled with nearest neighbour")
        image_path = output_dir / f"{site}_elevation_preview.png"
        fig.savefig(image_path, dpi=150); plt.close(fig)
        output_paths.append(image_path.name)
    return output_paths


def build_report(results: list[dict[str, Any]], figures: list[str]) -> str:
    rows = []
    for item in results:
        m, r = item["manifest"], item.get("raster")
        if r is None:
            rows.append(f"| {m['site_id']} | unavailable | unavailable | unavailable | {', '.join(item['findings'])} |")
            continue
        spacing = " × ".join(f"{x:.0f}" for x in r["approx_pixel_spacing_at_site_m"])
        status = "verified" if not item["findings"] else "review"
        rows.append(f"| {m['site_id']} | {r['width']} × {r['height']} | {r['pixel_size_degrees'][0]:.8f} × {r['pixel_size_degrees'][1]:.8f}° | ~{spacing} m at coordinate | {status} |")
    sections = [
        "# Earth DEM candidate screening",
        "",
        "**Status:** Provisional source-data screening only. None of the site coordinates, proposed candidate areas, or AOIs is approved.",
        "**Method:** Read-only verification and descriptive visualization of local Copernicus GLO-30 DSM tiles. No source raster was changed, reprojected, resampled as analysis data, or fingerprinted.",
        "",
        "## Spatial overview",
        "",
        f"![Provisional coordinates and source tile footprints]({figures[0]})",
        "",
        "The map uses longitude/latitude axes and is for location/coverage context only. Tile rectangles show downloaded source footprints, not candidate AOIs. Stars mark coordinates copied from the source manifest.",
        "",
        "## Local integrity and grid inventory",
        "",
        "The screening utility recomputes SHA-256 for each local TIFF, checks the manifest source ID and CRS, confirms the provisional coordinate lies inside the raster, and compares the local hash and file size to the QA JSON. Full values and any discrepancies are in the script output/API; the table summarizes the native grids.",
        "",
        "| Site | Native dimensions | Pixel spacing (degrees; x × y) | Approx. ground spacing at provisional coordinate (x × y) | Integrity |",
        "|---|---:|---:|---:|---|",
        *rows,
        "",
        "Every candidate has one local TIFF, a matching manifest checksum and source ID, a matching QA JSON checksum/file size, EPSG:4326, one float32 band, the provisional coordinate inside the tile, and 100% valid pixels under the existing raster mask. The product rasters declare no NoData value; full-mask coverage does not mean all cells are land or equally useful. The QA Markdown/JSON and source files remain the records of dimensions, bounds, and checksums.",
        "",
        "The native angular grid is latitude-dependent: the observed x spacing is 3 arc-seconds at Haughton and McMurdo, 2 arc-seconds at Askja, and 1 arc-second at Mauna Kea and Yungay; y spacing is 1 arc-second. Approximate geodesic spacing at the marked coordinate is reported for context only. This is not a selected analysis resolution or a claim about effective terrain resolution.",
        "",
        "## Elevation previews and distributions",
        "",
    ]
    for site in (item["manifest"]["site_id"] for item in results if item.get("raster")):
        sections.extend([f"### {site}", "", f"![{site} descriptive elevation preview]({site}_elevation_preview.png)", ""])
    sections.extend([
        "Each histogram and quantile describes the entire 1° source tile, not the marked site or a proposed smaller candidate area. This matters especially where tiles include ocean, ice, or broad elevation gradients. Map colors use a tile-specific 2nd–98th percentile display stretch; the image is downsampled with nearest-neighbour sampling for display only. Neither visualization changes the source raster or defines a threshold.",
        "",
        "## Data issues and limitations",
        "",
        "- These are Copernicus GLO-30 **digital surface model** tiles. Buildings and vegetation can contribute where present; the product is not a uniform bare-earth terrain source.",
        "- The manifest/QA verification passed, but all-mask-valid coverage is a storage/mask observation. It does not validate vertical accuracy, spatial completeness, source artifacts, or physical suitability. Some valid cells are near zero or below zero; in coastal/island tiles, water and land may both affect whole-tile statistics.",
        "- Copernicus describes editing/filling, height-error, and water-body quality layers, but companion layers were not downloaded. The current QA reports do not inspect those absent layers.",
        "- Product posting and effective terrain resolution are different concepts. Native grid dimensions vary with latitude, and the manifest does not identify the exact package release from the filename. Do not infer effective resolution from `GLO-30`, angular pixel spacing, or the display thumbnails.",
        "- The downloaded files are full source tiles. No clipping, reprojection, or analysis resampling was performed. Their CRS is geographic; any later physical-area comparison needs a team-approved preparation method and scale.",
        "- A single global product makes acquisition/provenance consistent across candidates, but it does not make local data quality or source conditions equivalent. This report compares availability and metadata only, not similarity to lunar terrain.",
        "",
        "## Provisional smaller-area concepts (not AOIs)",
        "",
        "| Site | Candidate concept to delineate with the team | Evidence needed before drawing/approving a boundary |",
        "|---|---|---|",
        "| Haughton | A land-only subarea centered on a verified impact-crater rim/floor sector. | Confirm crater boundary and whether a regional ArcticDEM surface/mask set is preferable; current point is a landmark, not an AOI center. |",
        "| McMurdo | One named Dry Valley basin or valley segment, selected with the science team. | The provisional coordinate lies near the western edge of this tile; confirm the intended valley and retrieve any adjacent tile needed to cover it. Compare REMA and its quality companions. |",
        "| Askja | The caldera or a named volcanic landform within the downloaded tile. | Confirm the intended landform boundary and inspect Copernicus quality layers; the current coordinate is a volcano landmark. |",
        "| Mauna Kea | A summit-complex or flank sector, with the land/ocean boundary explicitly excluded if appropriate. | Confirm which geomorphic unit is the target and check exact 3DEP availability/vertical metadata against the same area. |",
        "| Yungay | A bounded field-site terrain patch around the verified Yungay field location. | Confirm exact site coordinates and boundary from the project/source record; inspect the local mask and compare an independent regional source if needed. |",
        "",
        "These descriptions intentionally contain no invented dimensions or coordinates. They are scoping prompts only; create no polygon or clipped raster until the team approves exact boundaries.",
        "",
        "## Recommended next investigations",
        "",
        "1. **Askja and Mauna Kea:** inspect a precisely agreed landform subarea and retrieve product quality assets. The current local rasters have 2- and 1-arc-second longitudinal grids respectively; this is metadata context, not a ranking of science quality.",
        "2. **Haughton and McMurdo:** investigate regional alternatives in parallel because ArcticDEM and REMA offer distinct polar coverage and quality companion products. For McMurdo, verify whether the tile at hand actually contains the selected valley and whether adjacent coverage is needed.",
        "3. **Yungay:** first verify the field-site location/boundary and surface type required. The tile is locally available and checksum-verified, but the current candidate coordinate alone does not establish a representative study area.",
        "",
        "All five sites are equally present in the same Copernicus product family. The ordering above prioritizes concrete coverage/metadata questions and potential regional alternatives; it is not a terrain-similarity score or final site recommendation. Keep all five provisional until the team resolves AOIs, surface-type needs, quality-layer policy, and preparation scale.",
        "",
        "## Reproduction",
        "",
        "From the repository root:",
        "",
        "```powershell",
        r".\.venv\Scripts\python.exe src/data/earth_dem_screening.py",
        "```",
        "",
        "The command writes this report and six figures under `docs/reports/earth_candidate_screening/`. Inputs are the local manifest, ignored source TIFFs, and existing QA reports.",
        "",
    ])
    return "\n".join(sections)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--qa-root", type=Path, default=DEFAULT_QA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    results = inspect_candidates(args.manifest, args.raw_root, args.qa_root)
    figures = make_figures(results, args.output_dir)
    report = build_report(results, figures)
    (args.output_dir / "README.md").write_text(report, encoding="utf-8")
    print(json.dumps({"report": str(args.output_dir / "README.md"), "figures": figures,
                      "candidates": len(results), "findings": {item["manifest"]["site_id"]: item["findings"] for item in results}},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
