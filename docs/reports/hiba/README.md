# Hiba Terrain Validation Handoff

This folder contains the handoff package for the Terrain Fingerprint / Statistics / Quality Validation workstream.

## Deliverables

1. [Method and validation report](TERRAIN_FINGERPRINT_METHOD_AND_VALIDATION_2026-11-15.md) — implemented formulas, input requirements, quality semantics, synthetic test evidence, remaining canonical gates, and exact handoff command.
2. [Handoff assessment](TERRAIN_VALIDATION_HANDOFF_ASSESSMENT_2026-11-15.md) — assessment of the original 9-page Hiba playbook and what it does/does not prove.
3. [Canonical run checklist](../../CANONICAL_TERRAIN_RUN_CHECKLIST.md) — required upstream approvals and execution gates.

## Status

The extractor and synthetic validation suite are implemented. This package documents and strengthens software-level validation. It does not claim canonical site fingerprints are complete: AOIs, lunar ROI frame handling and common-grid decisions must be approved before the real-data run.

## Handoff owners

- **Ghassan/team:** source-backed Earth AOIs, source manifests and grid preparation.
- **Hiba:** approve the method settings, execute the canonical extractor, inspect outputs and deliver CSV/maps/quality notes.
- **Omar:** consume the canonical fingerprint CSV and produce matching/ranking plus robustness evidence.
- **Mohammed:** validate the paired output files in Streamlit and confirm the Analog Passport.

Do not label exploratory pilot outputs as canonical fingerprints.
