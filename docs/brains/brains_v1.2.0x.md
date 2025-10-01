# Brains — v1.2.0x

## Release focus
- **REF 1.2.0x-A02**: Keep the docs banner and app header synchronized with the hotfix summary by extending `_resolve_patch_metadata()` coverage. 【F:PATCHLOG.txt†L27-L27】【F:tests/ui/test_docs_tab.py†L16-L102】

## Implementation notes
- Appended the v1.2.0x entry to `PATCHLOG.txt` so `get_version_info()` delivers the main-thread ingestion summary everywhere `_resolve_patch_metadata()` is consumed. 【F:PATCHLOG.txt†L27-L27】【F:app/_version.py†L32-L67】
- Added a regression asserting `_resolve_patch_metadata()` now returns the v1.2.0x patch line derived from the log, ensuring the Docs tab banner renders the release copy verbatim. 【F:tests/ui/test_docs_tab.py†L16-L102】

## Testing
- `pytest tests/ui/test_docs_tab.py` 【0a2fd9†L1-L6】

## Continuity updates
- Logged the patch log alignment in the brains atlas, refreshed patch notes continuity, and recorded this AI log entry for the release. 【F:docs/atlas/brains.md†L1-L8】【F:docs/patch_notes/v1.2.0x.md†L1-L21】【F:docs/ai_log/2025-10-14.md†L1-L16】
