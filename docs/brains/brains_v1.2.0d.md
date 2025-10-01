# Brains — v1.2.0d

## REF 1.2.0-A04 — Gate overlays to 1-D products
- **Problem**: The targets panel allowed overlaying any curated MAST product, including 2-D images/cubes that the overlay renderer cannot plot. This produced ingestion entries that failed later without user guidance.
- **Decision**: Classify each product via `_product_overlay_support` so only spectra/SEDs/time-series expose an active Overlay button while images/cubes render a disabled control with an explanatory note.
- **Implementation**: Added `SUPPORTED_OVERLAY_TYPES` and `_product_overlay_support` in `app/ui/targets.py`, wiring the panel loop to respect the helper before appending to `st.session_state['ingest_queue']`. Unsupported entries now show a caption clarifying overlays are 1-D only. 【F:app/ui/targets.py†L19-L150】
- **Alternatives considered**: Filtering the manifest earlier in the registry build would hide image products entirely, but product review UI feedback requested visibility with clear affordances, so we opted for inline annotations.
- **Verification**: Added `tests/ui/test_targets_overlay_support.py` to assert spectra/time-series remain eligible and image/missing types are annotated. 【F:tests/ui/test_targets_overlay_support.py†L1-L40】
- **Follow-ups**: Extend the helper to flag future dataproduct types (e.g., cubes sliced to 1-D) once ingestion pipelines support them, and consider surfacing provider/tooltips describing how to fetch 2-D assets outside the overlay workspace.
