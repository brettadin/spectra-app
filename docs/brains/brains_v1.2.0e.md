# Brains — v1.2.0e

## Release focus
- **REF 1.2.0e-A01**: Keep the Spectra App header in lockstep with the live patch metadata and guard it with UI coverage.

## Implementation notes
- Introduced `_render_app_header` to centralize title/caption rendering and reuse `_resolve_patch_metadata` for both the header and Docs tab.
- Header caption now prefers the resolved `patch_version` value and formatted timestamp, preventing mismatches when `version.json` falls behind.
- Added a regression test that patches Streamlit caption/title calls to assert the header string starts with the active patch version and retains the timestamp + summary text.

## Testing
- `pytest tests/ui/test_docs_tab.py`

## Outstanding work
- Expand smoke coverage to exercise `_render_app_header` via the full `render()` flow once we have Streamlit snapshot tooling in place.
- Continue the broader v1.2 backlog (Simbad resolver, ingestion queue refactors, provenance enrichment) noted in earlier brains logs.

## Continuity updates
- Version bumped to v1.2.0e with accompanying updates to `PATCHLOG.txt`, markdown/txt patch notes, AI handoff brief, brains index, and AI activity log.
