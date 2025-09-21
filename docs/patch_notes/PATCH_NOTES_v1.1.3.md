# PATCH_NOTES_v1.1.3
Date: 2025-09-19T21:28:36.545880Z

## Summary
- Roadmap kickoff per v1.1.2c handoff: utilities added, docs scaffolding, apply steps included.
- Duplicate upload guard via SHA-256 ledger utility.
- Provenance schema and helper added.
- Unit utilities for toggles nm/Å/µm/cm⁻¹ with logging hooks.
- Export consistency checklist included.
- No breaking UI changes; downstream code can import these utilities when ready.

## Changes
- `app/version.json` created/updated.
- `app/utils/duplicate_ledger.py` added.
- `app/utils/provenance.py` added.
- `app/utils/units.py` added.
- `docs/brains/v1.1.3 brains.txt` added.
- `RUN_CMDS/Apply-Patch_v1.1.3.txt` with exact steps.
- `CHECKSUMS.txt` for patch files.

## Known Issues
- Utilities are inert until wired in; import and call sites must be added in the main app.
- Unit logging hook provided but not connected to export manifest writer yet.
- Dual-panel emission/absorption UI is documented, not implemented in this patch.

## Next
- Wire `duplicate_ledger` into the upload handler.
- Call `provenance.write_provenance` after fetch/ingest.
- Use `units.resolve_units` in all loaders; pass `units.LogSink` to record conversions.
- Implement dual-panel / offset-baseline in UI with legend hygiene.
