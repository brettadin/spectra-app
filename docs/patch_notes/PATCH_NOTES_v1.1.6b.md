# Patch Notes — v1.1.6b
_Last updated: 2025-09-22T01:22:08Z_

## Scope
v1.1.6b focuses on resolving archive/overlay UX friction and delivering a high-density solar reference example that defaults to a smoothed render for performance while preserving raw detail on demand.

## Highlights
- Collapse archive metadata and provenance JSON behind closed expanders and keep primary actions (Add to overlay) above the fold.
- Retire the redundant `Visible` checkbox column in the overlay table; rely exclusively on the multiselect control for visibility.
- Add a telescope-observed solar spectrum example (targeting NSO/Kitt Peak FTS or equivalent) with:
  - Smoothed data as the default render for fast loading,
  - A toggle that restores full-resolution samples,
  - Wavelength-band filters (IR, near-IR, VIS, UV-VIS, UV, etc.) driven by precomputed tags.
- Teach overlays about flux unit families and semantic axes so emission and absorption data plot on separate, correctly labeled y-axes.

## Implementation Sketch
1. Update `ArchiveUI._render_provider` to wrap metadata/provenance JSON in `st.expander` widgets (`expanded=False`) and reposition the overlay CTA above them.
2. Remove the `Visible` column from `_render_overlay_table` and refine helper copy so users treat the multiselect as the single visibility controller.
3. Pull a solar spectrum from a telescope-backed archive (e.g., NSO FTS via VizieR), normalize wavelength to nm, and generate both raw and smoothed datasets stored under `data/examples/` with provenance metadata.
4. Extend example-loading helpers so the solar entry becomes the default sidebar example, exposes smoothed/full-resolution toggles, and filters wavelengths by band without reprocessing.
5. Enrich overlay trace metadata with unit labels, physical quantity classifications, and semantic axis hints; render emission vs absorption on distinct y-axes with accurate unit strings and safe conversions (Fλ ↔ Fν when applicable).
6. Document behavior in the export manifest if additional metadata is surfaced, ensuring provenance accompanies both smoothed and raw representations.

## Verification
- Automated: run `pytest` (full suite) plus any new tests covering preprocessing helpers or overlay model/unit utilities.
- Manual: Streamlit smoke test to confirm collapsed expanders, smooth overlay toggles, solar example defaults/toggles/band filters, and dual-axis labeling.

## References
- Brains entry: [docs/brains/brains_v1.1.6b.md](../brains/brains_v1.1.6b.md)
- Patch summary (txt): [docs/PATCH_NOTES/v1.1.6b.txt](../PATCH_NOTES/v1.1.6b.txt)
- AI handoff prompt: [docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.6b.md](../ai_handoff/AI_HANDOFF_PROMPT_v1.1.6b.md)
- REF: 1.1.6b-A01
