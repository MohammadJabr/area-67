# Haughton Earth AOI boundary evidence review

**Review date:** 2026-11-15  
**Status:** literature-backed boundary options identified; no polygon digitized or approved  
**Purpose:** prevent the current reference-centred 990 m sample window from being misrepresented as a geomorphic AOI.

## Decision summary

Haughton is a defensible *candidate region* for an impact-structure terrain analogue, but the literature describes several nested and materially different boundaries. The team must select the landform/process relevant to the rover mission before Ghassan digitizes an AOI.

Do **not** generate a 990 m square around the crater-centre coordinate and call it the Haughton crater AOI. Do **not** substitute a circle based only on an apparent diameter for a mapped geological boundary.

## Published geomorphic boundaries

Patterson & Ernst (2020), *A novel geomatics method for assessing the Haughton impact structure*, summarizes the Osinski et al. interpretation and gives the following radial structure from the interpreted crater centre (75°22'38"N, 89°40'48"W):

| Feature | Published size | Approx. radius from centre | Interpretation |
|---|---:|---:|---|
| Transient cavity | 10–12 km diameter | 5–6 km | Excavation cavity, not the present outer crater boundary |
| Central basin | 10–13 km diameter (radial extent 5–6.5 km) | 5–6.5 km | Basin occupying the transient-cavity-scale region |
| Final crater rim | ~16 km diameter | ~8 km | Faulted terraces / rim zone; greatest vertical offsets |
| Apparent crater rim | ~23 km diameter | 11–12 km | Outermost semi-continuous circumferential fault |
| Outer deformation evidence | not a single closed rim | up to 14–15 km | Patterson & Ernst report vertical offsets suggesting deformation beyond the apparent rim |

The paper explicitly distinguishes the final rim from the apparent rim. A single 23 km circle would include a broad outer annulus and is not equivalent to the 16 km final rim.

## Mission-specific AOI alternatives

### Option A — Final-rim / faulted-terrace traverse
- Candidate footprint: mapped final-rim/faulted-terrace geological units, approximately 8 km radial scale.
- Relevance: terrain transitions, faulted blocks, slopes and local relief for rover traversal.
- Main risk: a radial buffer is only a screening envelope; it is not the mapped rim polygon. Use the digitized geological map and topographic/structural boundaries.

### Option B — Central basin / crater-fill terrain
- Candidate footprint: mapped central basin and crater-fill units, approximately 5–6.5 km radial extent.
- Relevance: basin-floor and crater-fill terrain, potentially more relevant to local traverse planning than the full apparent structure.
- Main risk: lake, fluvial and glacial deposits overprint parts of the basin. Patterson & Ernst specifically note post-impact deposits and valleys that complicate structural interpretation.

### Option C — Multi-zone comparison (recommended for the study design)
- Create separate stable AOIs for central basin, inner/outer ring, and faulted terraces, only where the published geological map supports the boundaries.
- Compare these zones independently against the lunar target rather than averaging the entire crater into one fingerprint.
- Preserve landform labels and rejected/uncertain segments. This lets the team test whether the analogy is basin-floor, rim, or faulted-terrace specific.
- Do not treat these zones as one contiguous rover-safe route.

## Source-backed cautions

1. The apparent crater diameter is about 23 km, while the final crater rim is about 16 km; these are not interchangeable boundaries.
2. The published 2020 geomatics analysis georeferenced and digitized Osinski's published geological map, then combined the mapped lithologies with a 20 m Canadian DEM. This is a reproducible source pathway for Ghassan to investigate; it is not proof that a ready-to-use GIS polygon is publicly downloadable.
3. The Haughton structure is modified by fluvial incision, lakes/ponds, glacial and fluvial deposits. The study explicitly removed some post-impact units from parts of its structural interpretation.
4. The 2020 paper reports the interpreted centre at 75°22'38"N, 89°40'48"W. This differs from other catalogue centre coordinates; use the paper's stated centre only when reproducing that study, and record the chosen coordinate provenance.
5. None of these published extents by itself defines the mission's final AOI. AOI geometry must follow the chosen mapped landform, data availability and team decision.

## Recommended next GIS action

Ghassan should obtain the Osinski (2005) geological map (the map cited and digitized by Patterson & Ernst), georeference it against the published control/DEM, and digitize separate polygons for the central basin, mapped ring/faulted terraces, and any selected crater-fill units. Record:
- source map edition and page/figure;
- georeferencing control points and residual error;
- digitization scale and operator;
- polygon geometry validity and area;
- overlap with the available Copernicus/ArcticDEM coverage;
- exclusions for water, lakes, fluvial/glacial deposits, and NoData;
- a stable AOI ID and explicit review status.

Until that work and team review are complete, retain Haughton as a candidate region and keep the current REF990 window labelled as an exploratory sample window only.

## References

- Patterson, C. W. & Ernst, R. E. (2020). *A novel geomatics method for assessing the Haughton impact structure*. Meteoritics & Planetary Science 55(10), E22–E34. https://doi.org/10.1111/maps.13573  
  Full text: https://onlinelibrary.wiley.com/doi/full/10.1111/maps.13573
- Osinski, G. R. et al. (2005). *Geological overview and cratering model for the Haughton impact structure, Devon Island, Canadian High Arctic*. Meteoritics & Planetary Science. https://www.research.ed.ac.uk/en/publications/geological-overview-and-cratering-model-for-the-haughton-impact-s/
- Impact Earth Database, Haughton entry (catalogue centre and apparent diameter): https://impact.uwo.ca/impact-craters/map/?crater_id=59

This is a literature review and digitization specification, not a final AOI geometry, DEM processing decision, or scientific approval.
