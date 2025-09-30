# Brains — v1.2.0

## Release focus
- **REF 1.2.0-A01**: Hardened FITS table ingestion so zero/negative wavenumber samples are culled before unit conversion, ensuring provenance recording cannot raise `UnboundLocalError` and the surviving payload preserves flux alignment.
- **REF 1.2.0-C01**: Documented the active Python environment in `docs/runtime.json` to re-establish the runtime baseline after prior handoffs lost the inventory file.

## Implementation notes
- `_extract_table_data` now computes a consolidated `dropped_nonpositive_rows` counter after filtering both raw wavenumber inputs and nm-converted data. Flux and wavelength arrays are sliced only when rows are removed, preventing redundant copies.
- The regression suite includes `test_parse_fits_table_filters_nonpositive_wavenumbers` to cover the scenario that previously crashed when provenance logging referenced an undefined variable.
- Provenance captures both the specific wavenumber drop count and the aggregate row total so downstream audit logs can summarise row loss without recalculating masks.

## Testing
- `pytest` is expected to cover the new regression (run after changes).
- `Verify-Project.ps1` is still unavailable in this environment; rerun in Windows/PowerShell during integration testing.

## Outstanding work
- The SIMBAD resolver, archive ingestion overhaul, provenance enrichment, and caching directives outlined in the v1.2 blueprint remain open for follow-up patches.
- Recreate the documentation mirroring tooling referenced in earlier handoffs so library docs can be refreshed to match the recorded runtime versions.

## Continuity updates
- Version bumped to v1.2.0 alongside updated patch notes (`docs/patch_notes/PATCH_NOTES_v1.2.0.md` and `docs/PATCH_NOTES/v1.2.0.txt`), the AI handoff brief, AI log entry for 2025-09-30, and `PATCHLOG.txt` appendices.
