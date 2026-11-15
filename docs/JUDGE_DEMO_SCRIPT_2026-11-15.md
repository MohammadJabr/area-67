# AREA 67 judge demo - 2 to 3 minutes

**Use only with the app's exploratory warning visible.** The current comparisons are reference-centered windows, not approved geomorphic AOIs, and rankings are not suitability certification.

1. **Open the app** (`streamlit run app/main.py`). Say: "AREA 67 compares terrain descriptors from a lunar context window with selected Earth reference windows. This is an exploratory software MVP, not a lunar-site approval tool."
2. **Mission Setup:** choose the supplied Site01 target and Rover Navigation / Terrain Traversal profile. Explain that Site01 is the project's current illumination/SDEM anchor; it is not asserted to be the best base location.
3. **Results & Comparison:** show the three current Earth windows and their relative indices: Haughton 73.7870, Yungay 66.1325, Mauna Kea 27.3897. Explain that the existing five-group matcher exposes per-feature contributions, while the Slope-only baseline preserves the same ordering in this small pilot. The score is not a probability.
4. **Point out evidence limits:** the Site01 context window has 9.235% positive LOLA LDEC support, distinct from valid raster coverage. The Copernicus inputs are DSMs; effective resolution and per-pixel quality were not established. Haughton's window is not a digitized crater AOI; Yungay's reference identity has a roughly 5.81 km discrepancy; all AOIs and settings are provisional.
5. **Site Passport:** open one candidate and show source provenance, feature values, assumptions, and limitations. Close with: "The next scientific step is team-approved AOIs and common analysis settings, followed by independent fingerprint and matching validation."

Do not describe the ranking as a probability, physical equivalence, rover-safety result, or certification that an Earth site is suitable for a lunar base.
