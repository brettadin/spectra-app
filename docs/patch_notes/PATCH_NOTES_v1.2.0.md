# Patch Notes — v1.2.0

## Highlights
- **REF 1.2.0-A01**: Fixed FITS table ingestion so non-positive wavenumber samples are discarded safely, avoiding crashes when provenance tries to report dropped rows. The regression suite now covers the mixed wavenumber scenario.
- **REF 1.2.0-C01**: Captured the active runtime package versions in `docs/runtime.json` to realign documentation with the current toolchain.

## Follow-up
- The large ingestion roadmap (SIMBAD resolver, archive fetch consolidation, provenance overhaul) remains outstanding and should be prioritised for subsequent v1.2.x patches.
- Review whether documentation mirroring needs to be regenerated for the recorded library versions once the tooling scripts are restored.

## Continuity
- Updated `app/version.json`, `PATCHLOG.txt`, `docs/PATCH_NOTES/v1.2.0.txt`, `docs/brains/brains_v1.2.0.md`, `docs/brains/brains_INDEX.md`, `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.2.0.md`, and `docs/ai_log/2025-09-30.md` for v1.2.0 (REF 1.2.0-A01 / 1.2.0-C01).
