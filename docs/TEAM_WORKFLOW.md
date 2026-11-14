# Team Workflow — Area 67

## Team roles
- Mohammed Jabr — team lead, repository coordination, application integration
- Ghassan Al-Shoubi — data collection and GIS preparation
- Hiba Sbouh — terrain fingerprint and validation
- Omar Salous — similarity matching and mission planning

## Branches
- `main`: stable integrated version
- `feature/ghassan-data-gis`: data acquisition and GIS preparation
- `feature/hiba-terrain-validation`: five terrain features and validation
- `feature/omar-matching-planning`: similarity, mission profiles, and route analysis
- `feature/mohammad-app-integration`: application and integration

## Rules
1. Do not commit directly to `main`.
2. Pull the latest `main` before starting work.
3. Commit only your work to your assigned branch.
4. Use small, descriptive commits (for example: `feat: calculate slope statistics`).
5. Open a Pull Request from your feature branch into `main`.
6. Review the diff and run relevant tests before merging.
7. Do not commit large raster files, downloaded archives, credentials, API keys, or private data.
8. Keep a source manifest for every dataset: provider, product ID/version, access date, spatial resolution, CRS, vertical reference, units, coverage, quality flags, and usage terms.
9. Distinguish measured values, derived metrics, assumptions, and future work.

## 24-hour prototype priority
1. One target planetary area and one mission profile.
2. A small number of Earth candidate areas.
3. Reproducible loading and quality checks for real DEM data.
4. The five terrain feature groups.
5. Explainable weighted similarity and ranking.
6. A minimal interface showing candidate evidence.
7. A first Analog Passport.

A* route analysis and illumination/shadow simulation are extensions. Implement them only after the core data-to-ranking workflow is working and validated.
