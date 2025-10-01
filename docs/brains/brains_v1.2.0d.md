# Brains — v1.2.0d

## Release focus
- **REF 1.2.0d-A01**: Sync the Docs tab banner with build metadata so patch summaries stay current across releases and regression guard against drift.

## Implementation notes
- `_render_docs_tab` now receives `version_info` from the main render pipeline and derives its banner text via `_resolve_patch_metadata`, preferring the `patch_raw` string and falling back to the patch summary if needed.
- The banner defaults to "No summary recorded." if both the patch line and summary are blank, ensuring we always render a helpful message.
- A dedicated UI test (`tests/ui/test_docs_tab.py`) patches Streamlit widgets, injects a temporary documentation library, and verifies the banner equals the provided patch line.

## Testing
- `pytest tests/ui/test_docs_tab.py`

## Outstanding work
- Expand UI smoke coverage to exercise the Docs tab end-to-end once the documentation library grows beyond static markdown.

## Continuity updates
- Version bumped to v1.2.0d with accompanying updates to `PATCHLOG.txt`, markdown/txt patch notes, and the AI activity log.
