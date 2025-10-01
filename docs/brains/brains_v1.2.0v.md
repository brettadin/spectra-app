# Brains — v1.2.0v

## Release focus
- **REF 1.2.0v-A01**: Align the patch log and surfaced metadata so the header and Docs banner quote the quick-add summary verbatim. 【F:PATCHLOG.txt†L24-L26】【F:tests/ui/test_docs_tab.py†L16-L78】

## Implementation notes
- Appended the `v1.2.0v` entry to `PATCHLOG.txt` so `_resolve_patch_metadata()` reads the same summary that lives in `app/version.json`, keeping continuity helpers in sync. 【F:PATCHLOG.txt†L24-L26】【F:app/_version.py†L30-L64】
- Refreshed the Docs tab and header regression to pin against the quick-add summary so future releases surface the right text without manual string swaps. 【F:tests/ui/test_docs_tab.py†L16-L78】

## Testing
- `pytest tests/ui/test_docs_tab.py` 【245a80†L1-L5】

## Continuity updates
- Logged the alignment in the atlas brains overview, refreshed patch notes, and wrote the AI log entry for the release. 【F:docs/atlas/brains.md†L1-L18】【F:docs/patch_notes/v1.2.0v.md†L1-L22】【F:docs/ai_log/2025-10-13.md†L1-L22】
