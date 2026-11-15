# Hiba Terrain Validation Handoff

This folder contains the handoff package for the Terrain Fingerprint / Statistics / Quality Validation workstream.

## Deliverables

1. [Execution readiness and runbook](HIBA_EXECUTION_READINESS_2026-11-15.md) — Hiba's exact current status, blockers, approved run sequence, test commands and handoff checklist.
2. [Method and validation report](TERRAIN_FINGERPRINT_METHOD_AND_VALIDATION_2026-11-15.md) — formulas, units, scale/window semantics, NoData, quality semantics and test coverage.
3. [Handoff assessment](TERRAIN_VALIDATION_HANDOFF_ASSESSMENT_2026-11-15.md) — assessment of the original 9-page personal playbook and distinction between methodology and completed scientific evidence.
4. [Canonical run checklist](../../CANONICAL_TERRAIN_RUN_CHECKLIST.md) — approval gates and extractor invocation requirements.

## Status

- Five terrain groups are implemented.
- Synthetic validation suite and the PR #103 full CI passed; post-merge main CI also passed.
- Method, validation and runbook documents are committed on main.
- Canonical real-data fingerprints and derived maps are **not yet produced** because approved AOIs, lunar ROI frame handling, common-grid/resampling/NoData policy and run settings remain unresolved.

## Handoff owners

- **Ghassan/team:** source-backed Earth AOIs, source manifests and grid preparation.
- **Hiba:** confirm method settings with the team, execute the canonical extractor after input approval, inspect outputs and deliver CSV/maps/quality notes.
- **Omar:** consume the canonical fingerprint CSV and produce matching/ranking plus robustness evidence.
- **Mohammed:** validate the paired output files in Streamlit and confirm the Analog Passport.

Do not label exploratory pilot outputs as canonical fingerprints.
