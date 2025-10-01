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

## REF 1.2.0-A04 — Gate overlays to 1-D products
- **Problem**: The targets panel allowed overlaying any curated MAST product, including 2-D images/cubes that the overlay renderer cannot plot. This produced ingestion entries that failed later without user guidance.
- **Decision**: Classify each product via `_product_overlay_support` so only spectra/SEDs/time-series expose an active Overlay button while images/cubes render a disabled control with an explanatory note.
- **Implementation**: Added `SUPPORTED_OVERLAY_TYPES` and `_product_overlay_support` in `app/ui/targets.py`, wiring the panel loop to respect the helper before appending to `st.session_state['ingest_queue']`. Unsupported entries now show a caption clarifying overlays are 1-D only. 【F:app/ui/targets.py†L19-L150】
- **Alternatives considered**: Filtering the manifest earlier in the registry build would hide image products entirely, but product review UI feedback requested visibility with clear affordances, so we opted for inline annotations.
- **Verification**: Added `tests/ui/test_targets_overlay_support.py` to assert spectra/time-series remain eligible and image/missing types are annotated. 【F:tests/ui/test_targets_overlay_support.py†L1-L40】
- **Follow-ups**: Extend the helper to flag future dataproduct types (e.g., cubes sliced to 1-D) once ingestion pipelines support them, and consider surfacing provider/tooltips describing how to fetch 2-D assets outside the overlay workspace.

