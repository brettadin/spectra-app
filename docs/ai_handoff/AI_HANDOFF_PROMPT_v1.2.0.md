# AI Handoff Prompt — v1.2.0

## Snapshot
- Version: v1.2.0 (REF 1.2.0-A01, 1.2.0-C01)
- Focus: Stabilise FITS table ingestion for wavenumber data and restore missing runtime inventory documentation.

## Completed in this patch
1. `_extract_table_data` now tracks a defined `dropped_nonpositive_rows` counter so provenance recording no longer triggers `UnboundLocalError` when non-positive wavenumbers are dropped.
2. Added regression coverage (`tests/server/test_ingest_fits.py::test_parse_fits_table_filters_nonpositive_wavenumbers`) ensuring zero/negative wavenumbers are culled and provenance counts are recorded.
3. Recreated `docs/runtime.json` with the active package versions and rolled continuity docs (patch notes, brains, AI log, patch log, version file).

## Outstanding priorities
- Implement the SIMBAD resolver, archive fetch orchestration, CALSPEC/ESO/HARPS/IRSA ingestion flows, provenance enrichment, and caching layers outlined in the v1.2 roadmap.
- Restore documentation mirroring scripts (`tools/search_server.py`, `tools/mirror_docs.py`, `tools/build_index.py`) so library references can be regenerated for the recorded runtime versions.
- Run `Verify-Project.ps1` in a Windows environment, confirm provider caches remain valid, and expand regression coverage per the backlog (overlay warnings, DOI support, continuity automation).

## Suggested next steps
- Stand up the SIMBAD resolver service and provider cache directory (`data/providers/simbad/`) before tackling archive fetch automation, since the fetch workflow depends on resolver metadata.
- Audit unit conversion helpers and start migrating shared logic into a dedicated normalization module as called out in prior follow-ups.
- Plan documentation updates (README, docs/index) once ingestion roadmap milestones ship to keep user guidance aligned with new workflows.
