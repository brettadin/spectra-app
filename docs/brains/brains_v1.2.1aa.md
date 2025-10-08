# IR JCAMP health hotfix — 2025-10-28
- Normalised JCAMP ingestion to scale raw Y samples by `YFACTOR`, verify `FIRSTY`, capture IR diagnostics, and convert supported inputs to decadic absorbance via the new `IRMeta`/`to_A10` helper (with coefficient parameter requirements surfaced when absent).【F:app/server/ingest_jcamp.py†L357-L571】【F:app/server/ir_units.py†L7-L64】
- Extended the overlay workspace to prompt for path length and mole fraction, rebuild downsample tiers after conversion, surface IR sanity expanders, and switch Plotly axes/hover formatting to scientific notation with conditional cm⁻¹ reversal.【F:app/ui/main.py†L279-L467】【F:app/ui/main.py†L2452-L2687】
- Added a Streamlit health gate plus first-run routing guard, refreshed the export manifest with IR provenance, and published supporting documentation for the conversion workflow.【F:app/ui/main.py†L66-L92】【F:app/app_patched.py†L1-L48】【F:app/export_manifest.py†L23-L74】【F:docs/app/ir_import_units.md†L1-L11】

## Regression coverage
- Introduced unit tests for IR conversions across transmittance, absorbance, and coefficient inputs (including parameter validation).【F:tests/test_ir_units.py†L1-L38】

## Continuity & release notes
- Bumped `app/version.json`, appended changelog/patch log entries, and published v1.2.1aa patch notes (Markdown/txt) documenting the hotfix scope.【F:app/version.json†L1-L5】【F:CHANGELOG.md†L1-L8】【F:PATCHLOG.txt†L45-L55】【F:docs/patch_notes/v1.2.1aa_hotfix.md†L1-L9】【F:docs/PATCH_NOTES/v1.2.1aa.txt†L1-L1】
