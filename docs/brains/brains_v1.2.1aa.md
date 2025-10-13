# IR JCAMP health hotfix — 2025-10-28
- Normalised JCAMP ingestion to scale raw Y samples by `YFACTOR`, verify `FIRSTY`, capture IR diagnostics, and convert supported inputs to decadic absorbance via the new `IRMeta`/`to_A10` helper (with coefficient parameter requirements surfaced when absent).【F:app/server/ingest_jcamp.py†L357-L571】【F:app/server/ir_units.py†L7-L64】
- Extended the overlay workspace to prompt for path length and mole fraction, rebuild downsample tiers after conversion, surface IR sanity expanders, and switch Plotly axes/hover formatting to scientific notation with conditional cm⁻¹ reversal.【F:app/ui/main.py†L279-L467】【F:app/ui/main.py†L2452-L2687】
- Added a Streamlit health gate plus first-run routing guard, refreshed the export manifest with IR provenance, and published supporting documentation for the conversion workflow.【F:app/ui/main.py†L66-L92】【F:app/app_patched.py†L1-L48】【F:app/export_manifest.py†L23-L74】【F:docs/app/ir_import_units.md†L1-L11】

## Regression coverage
- Introduced unit tests for IR conversions across transmittance, absorbance, and coefficient inputs (including parameter validation).【F:tests/test_ir_units.py†L1-L38】

## Continuity & release notes
- Bumped `app/version.json`, appended changelog/patch log entries, and published v1.2.1aa patch notes (Markdown/txt) documenting the hotfix scope.【F:app/version.json†L1-L5】【F:CHANGELOG.md†L1-L8】【F:PATCHLOG.txt†L45-L55】【F:docs/patch_notes/v1.2.1aa_hotfix.md†L1-L9】【F:docs/PATCH_NOTES/v1.2.1aa.txt†L1-L1】

## Decision log — FTIR functional-group classifier (v1.2.1ad)
- Integrated the irchracterizationcnn FTIR classifier with a shared loader module, REST API, Streamlit UI button, shaded band overlays, and attribution docs covering NIST/SDBS sources.【F:ml/ir_group_classifier.py†L1-L236】【F:app/server/ir_groups_api.py†L1-L75】【F:app/utils/ir_group_client.py†L1-L63】【F:app/ui/main.py†L1-L362】【F:app/ui/ir_group_overlays.py†L1-L204】【F:README.md†L1-L127】
- Added dependency and asset management collateral: download script, requirements updates, patch notes, and release metadata for v1.2.1ad.【F:scripts/fetch_ir_model.py†L1-L46】【F:requirements.txt†L1-L15】【F:app/version.json†L1-L5】【F:docs/patch_notes/v1.2.1ad.md†L1-L4】【F:PATCHLOG.txt†L46-L47】
- Landed unit coverage for the classifier preprocessing/threshold logic so regressions surface without TensorFlow at test time.【F:tests/ml/test_ir_group_classifier.py†L1-L57】

## Decision log — IR classifier fallback (v1.2.1ae)
- Added a rule-based fallback model, shared correlation-band metadata, backend reporting, and heuristic thresholds so missing TensorFlow weights no longer block the workflow.【F:ml/ir_group_classifier.py†L1-L247】【F:ml/ir_group_data.py†L1-L161】【F:app/utils/ir_group_client.py†L1-L103】【F:app/ui/main.py†L3601-L3638】【F:app/ui/ir_group_overlays.py†L1-L81】【F:app/server/ir_groups_api.py†L1-L63】
- Documented the fallback behaviour, refreshed the download helper guidance, and recorded release metadata for v1.2.1ae.【F:README.md†L98-L110】【F:scripts/fetch_ir_model.py†L1-L43】【F:app/version.json†L1-L5】【F:PATCHLOG.txt†L56-L58】【F:docs/patch_notes/v1.2.1ae.md†L1-L9】
- Extended classifier unit coverage to assert the heuristic path raises carbonyl detections and reports the fallback backend state.【F:tests/ml/test_ir_group_classifier.py†L1-L78】
