# AI Handoff Prompt — v1.2.0a

## Snapshot
- Version: v1.2.0a (REF 1.2.0-A02, 1.2.0-D01)
- Focus: Normalise FITS ingestion for plural Angstrom labels and capture the continuity collateral for the hotfix.

## Completed in this patch
1. `_normalise_wavelength_unit` strips plural suffixes / alias spellings and falls back to `Angstrom` before deferring to `canonical_unit`, matching the shared alias handling in `app/server/units._as_unit`.
2. Added `test_parse_fits_table_accepts_angstroms_alias` to cover FITS tables that supply `Angstroms` in both the column metadata and header.
3. Updated patch notes, brains, AI log, AI handoff brief, and patch log to document v1.2.0a.

## Outstanding priorities
- Continue the v1.2 roadmap: SIMBAD resolver, ingestion consolidation, provenance enrichment, caching automation, export audits.
- Restore the FAISS-backed documentation tooling or introduce a lightweight substitute so the docs-first workflow (search endpoint) is available again.
- Re-run provider verification scripts (e.g., `Verify-Project.ps1`) in a Windows environment to confirm caches and overlays remain valid.

## Suggested next steps
- Stand up the documentation search stack by packaging FAISS or swapping to an alternate vector backend so AGENTS.md requirements are practical.
- Extend ingestion regression coverage to additional CALSPEC/MAST samples that advertise other pluralised units (`Microns`, `nanometers`) and ensure provenance remains consistent.
- Plan UI work to surface unit alias information (tooltip or ingestion summary) so users know when units have been normalised implicitly.
