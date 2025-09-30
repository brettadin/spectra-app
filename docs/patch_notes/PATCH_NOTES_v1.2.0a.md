# Patch Notes — v1.2.0a

## Highlights
- **REF 1.2.0-A02**: Normalised FITS wavelength unit parsing so plural Angstrom labels and their aliases resolve to the canonical unit before conversion, preventing ingestion failures for CALSPEC tables that advertise "Angstroms" in headers.
- **REF 1.2.0-D01**: Updated regression coverage, patch log, brains, AI handoff, and summary docs to capture the hotfix and verification steps.

## Follow-up
- Continue the v1.2 roadmap (SIMBAD resolver, ingestion consolidation, provenance enrichment, caching) as tracked in prior handoffs.
- Restore documentation mirroring tooling (`tools/mirror_docs.py`, `tools/build_index.py`, `tools/search_server.py`) once FAISS dependencies become available again.

## Verification
- `pytest tests/server/test_ingest_fits.py -k Angstroms`
- Manual `parse_fits` run against the synthetic "Angstroms" FITS table used in the regression test to confirm provenance and unit labelling.

## Continuity
- Updated `app/version.json` to v1.2.0a alongside `PATCHLOG.txt`, brains index/logs, AI log, AI handoff brief, and plaintext patch notes (`docs/PATCH_NOTES/v1.2.0a.txt`).
