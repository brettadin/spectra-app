# Brains — v1.2.0a

## Release focus
- **REF 1.2.0-A02**: Normalise FITS ingestion so plural Angstrom labels (e.g., `Angstroms`, `ångströms`) resolve to the canonical unit before converting to nm, ensuring CALSPEC-style tables import without raising `ValueError`.
- **REF 1.2.0-D01**: Refresh regression coverage and continuity documents (patch notes, patch log, AI log, AI handoff, plaintext notes) to record the hotfix and its verification.

## Implementation notes
- `_normalise_wavelength_unit` now strips plural suffixes and recognises alias spellings before calling `canonical_unit`, tracking an alias fallback so provenance surfaces the canonical label even if Astropy rejects the raw token.
- `app/server/units._as_unit` shares the alias logic so any caller leveraging `canonical_unit` benefits from the same handling (plural/suffixed Angstrom strings resolve to `u.AA`).
- Added `test_parse_fits_table_accepts_angstroms_alias` covering the regression with both column and header units set to `Angstroms`.

## Testing
- `pytest tests/server/test_ingest_fits.py -k Angstroms`
- Manual `parse_fits` invocation against the generated regression FITS table (mirrors CALSPEC headers) to confirm provenance labelling and nm conversions.

## Outstanding work
- Resume the broader v1.2 backlog (SIMBAD resolver, ingestion consolidation, provenance enrichment, caching automation).
- Restore FAISS-backed documentation search tooling or replace with a lightweight alternative so the docs-first workflow remains actionable.

## Continuity updates
- Version bumped to v1.2.0a with matching entries in `PATCHLOG.txt`, `docs/patch_notes/PATCH_NOTES_v1.2.0a.md`, `docs/PATCH_NOTES/v1.2.0a.txt`, and `docs/ai_log/2025-09-30.md`.
