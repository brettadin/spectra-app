# AI Handoff Prompt — v1.1.6b
_Last updated: 2025-09-22T01:22:08Z_

This is a continuation of the live-archive work. Ship the UX and data upgrades without regressing the existing overlay, differential, export, or continuity contracts.

## Do Not Break
- Overlay, Differential, Export flows; unit conversions remain idempotent from the canonical nm baseline.
- Provenance payloads stay attached to every overlay (archive hits, uploads, examples, exports).
- Duplicate guard, normalization, and provider cache invariants introduced in v1.1.6 stay intact.
- Continuity docs (`brains`, `patch notes`, `AI handoff`, `PATCHLOG.txt`) stay cross-referenced.

## What to Ship in v1.1.6b (REF 1.1.6b-A01)
1. **Archive UI**: Wrap metadata/provenance JSON inside closed `st.expander` widgets and keep “Add to overlay” accessible without scrolling. Preserve success/warning toast behavior.
2. **Overlay visibility**: Remove the `Visible` checkbox column from `_render_overlay_table`; rely on the existing multiselect form for visibility and update helper copy to reflect that single source of truth.
3. **Solar example**: Acquire a telescope-observed solar spectrum (e.g., NSO/Kitt Peak FTS via VizieR), normalize wavelengths to nm, and store both raw and smoothed datasets plus band tags (IR, near-IR, VIS, UV-VIS, UV...). Default the example to the smoothed trace, surface a toggle for full resolution, and expose band filters in the UI.
4. **Unit semantics**: Extend overlay trace metadata to capture unit strings and physical quantity types (flux density, spectral radiance, equivalent width, etc.). Plot emission and absorption on distinct, unit-aware y-axes (secondary axis or comparable) so labels stay truthful and toggles/exports propagate the selected units.
5. **Performance & caching**: Persist processed solar datasets under `data/examples/` (Parquet/Feather). Memoize loads so switching smoothing/band options does not refetch archive data.

## Data & Provenance Requirements
- Record instrument, archive, observation program/ID, citation, and unit metadata for the solar spectrum. Include both smoothed and raw datasets in exports with explicit provenance blocks.
- If new conversion helpers are added, keep them dependency-light (NumPy/Pandas acceptable; avoid new third-party packages unless justified).

## Verification
- Automated: `pytest` (full suite) plus targeted tests for any new preprocessing or overlay helper functions.
- Manual: Streamlit smoke test — confirm archive metadata expanders stay collapsed by default, overlay visibility toggles run smoothly, solar example loads (smoothed default, raw toggle, band filters), and dual-axis labeling matches the chosen unit semantics.

## Continuity Links
- Brains: docs/brains/brains_v1.1.6b.md
- Patch notes: docs/patch_notes/PATCH_NOTES_v1.1.6b.md
- Patch summary: docs/PATCH_NOTES/v1.1.6b.txt
- REF: 1.1.6b-A01
