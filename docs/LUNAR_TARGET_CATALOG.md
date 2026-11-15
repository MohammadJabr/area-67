# AREA 67 — NASA Lunar South-Pole Target Catalogue

**Source reviewed:** NASA GSFC Planetary Geodesy Data Archive (PGDA), High-Resolution LOLA Topography for Lunar South Pole Sites.  
**Catalogue:** https://pgda.gsfc.nasa.gov/products/78  
**Status:** Candidate target catalogue, not an approved base-site ranking.

## Core sites and published ROI archive availability

| PGDA site | Provider label | ROI archive linked on PGDA page | AREA 67 status |
|---|---|---:|---|
| Site01 | Connecting ridge | Yes | High-priority alternative to inspect; NASA page highlights favorable illumination analysis |
| Site04 | Shackleton rim | Yes | Existing provisional target; five rasters locally downloaded and QA-inspected |
| Site06 | Nobile rim 1 | Yes | Available for ROI boundary inspection |
| Site07 | Peak near Shackleton | Yes | Available for ROI boundary inspection |
| Site11 | de Gerlache rim | Yes | Available for ROI boundary inspection |

The page lists LDEM, LDEC, slope, total Z RMS uncertainty and slope RMS uncertainty for these sites; it also lists XYZI point clouds and 100 elevation clones. AREA 67 acquisition tooling intentionally downloads only the five named raster layers when explicitly selected. It never downloads clones or point clouds implicitly.

## Additional PGDA south-pole target names

The same page lists:

- Site20 and Site20v2 — Leibnitz beta plateau (Site20v2 is an extended boundary version).
- Site23 — Malapert massif.
- Site42 — de Gerlache–Kocher massif.
- Haworth.
- Shoemaker.
- DM1 — Amundsen rim.
- DM2 — Nobile rim 2.
- SL2 — de Gerlache rim.
- SL3 — Connecting ridge extension.
- NPA — Cabeus exterior wall 1.
- NPB — Amundsen 1.
- NPC — Idel'son L crater 1.
- NPD — Malapert crater 1.
- LM1 — Shackleton Rim B.
- LM2 — Shoemaker Rim A.
- LM3 — Shoemaker Rim B.
- LM4 — Shoemaker Rim C.
- LM5 — Shoemaker Rim D.
- LM6 — Shoemaker Rim E.
- LM7 — Faustini Rim A.
- LM8 — Shoemaker Rim F.

The current acquisition helper deliberately supports only Site01, Site04, Site06, Site07 and Site11 because the PGDA page explicitly links ROI archives for those five. Other targets require a separate check of their exact available files and any provider-defined ROIs before being added to the automated download allowlist.

## Site01 versus Site04 — why compare, not choose prematurely

NASA's PGDA product description reports that, in its illumination analysis for 2024-01-01 through 2026-01-01, Site01 had the largest area with average illumination above 70% at 1 m above the surface among the listed sites. It also reports longer continuous illumination at 5 m above the surface for Site01. The same page explains that illumination variability is affected by height uncertainty.

This makes Site01 especially relevant to a sustained-operations question. It does not make Site01 the best overall lunar base site. That decision also needs surface/terrain hazards, resource context, temperatures, communication, uncertainty and mission constraints.

Site04 is already present locally and has the following observed support split in the current raster:
- Positive LDEC spot-count cells: 9.1541%.
- Zero-count / interpolated cells: 90.8459%.
- Raster valid mask: 100%.

These are properties of the downloaded Site04 files and must not be generalized to the other PGDA sites.

## Method notes from the PGDA product page

- The 5 m/pixel LDEM products are south-polar stereographic GeoTIFFs in the MOON_ME reference frame of ephemeris DE421.
- PGDA states that roughly 90% of the 5 m pixels are interpolated because of LOLA's cross-track and inter-spot sampling gaps.
- The page reports track geolocation uncertainty of roughly 10–20 cm horizontally and 2–4 cm vertically after co-adjustment. This is not the same as effective raster resolution.
- The page reports median RMS Z error around 0.30–0.50 m and median RMS slope error around 1.5–2.5° within the studied ROIs. These are published product-level/ROI summaries, not per-pixel guarantees or universal quality thresholds.
- Height uncertainty, slope uncertainty, observation support and illumination uncertainty should remain distinct evidence fields.

Source: https://pgda.gsfc.nasa.gov/products/78  
Further method reference: Barker et al. (2021), https://doi.org/10.1016/j.pss.2020.105119  
Foundational illumination analysis: Mazarico et al. (2011), https://doi.org/10.1016/j.icarus.2010.10.030
