# MAKE NEW BRAINS EACH TIME YOU MAKE A CHANGE. DO NOT OVER WRITE PREVIOUS BRAINS
# Brains — v1.1.6b
_Last updated (UTC): 2025-09-22T01:22:08Z_

## Purpose
v1.1.6b carries forward the live-archive foundation from v1.1.6 and targets the UX gaps surfaced during archive browsing. The patch will collapse bulky provenance panels, streamline overlay visibility controls, and introduce a high-density solar spectrum example that defaults to a smoothed view while preserving full-resolution access.

## REF 1.1.6b-A01 — Archive UX, Solar reference, and unit semantics
- **What**
  - Collapse archive metadata/provenance readouts behind closed expanders and keep “Add to overlay” actions visible without scrolling.
  - Remove the redundant `Visible` checkbox column from the overlay table so the multiselect remains the single visibility control.
  - Seed the examples library with a telescope-observed solar spectrum that defaults to a smoothed trace, exposes a toggle to render the full-resolution dataset, and allows band-based wavelength filtering (IR, near-IR, VIS, UV-VIS, UV, etc.).
  - Extend overlay traces with explicit unit semantics so emission and absorption data can render on dedicated y-axes with correct labels and conversions.
- **Why**
  - Archive result panels currently expand metadata inline, pushing the overlay CTA below the fold and making quick comparisons painful.
  - Duplicate visibility toggles desynchronize state and create the “hiccups” reported when enabling or disabling overlays.
  - A solar reference rich in spectral features exercises the performance path; smoothing by default keeps load times reasonable while a raw toggle protects investigative fidelity.
  - Scientific overlays carry diverse flux units (e.g., W·m⁻²·nm⁻¹, erg·s⁻¹·cm⁻²·Å⁻¹, spectral radiance). Explicit semantics are required so emission peaks and absorption troughs present correctly and axes remain trustworthy.
- **Where**
  - UI adjustments: `app/archive_ui.py`, `app/ui/main.py`, associated widgets/helpers.
  - Example ingestion & caching: `app/examples/`, `data/examples/`, potential preprocessing helpers under `scripts/`.
  - Overlay data model & plotting: `app/overlay_models.py`, `app/plotting/`, `app/ui/overlays.py` (exact paths to confirm while implementing).
  - Continuity docs: `PATCHLOG.txt`, `docs/PATCH_NOTES/v1.1.6b.txt`, `docs/patch_notes/PATCH_NOTES_v1.1.6b.md`, `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.6b.md`.
- **How**
  1. Wrap metadata/provenance JSON blocks inside `st.expander(label, expanded=False)` within `ArchiveUI._render_provider`, keeping success toasts intact and positioning the “Add to overlay” button immediately above the expanders.
  2. Trim the `Visible` column from `_render_overlay_table`, refresh helper text to clarify the multiselect is authoritative, and ensure session-state updates remain synchronized.
  3. Acquire a solar spectrum observed by a reputable telescope (e.g., NSO/Kitt Peak FTS via VizieR). Normalize wavelength to nm, persist raw data, and generate a smoothed counterpart (Savitzky–Golay or rolling median) stored alongside band classifications for wavelength-range filtering.
  4. Extend example loading so the new solar entry becomes the default selection, exposes toggles for smoothed vs full-resolution traces, and leverages precomputed band tags for quick filter switches without re-fetching.
  5. Expand overlay trace metadata to include unit strings, physical quantity (flux density, spectral radiance, equivalent width, etc.), and a semantic axis type (`emission`, `absorption`, or other). Use Plotly secondary y-axes (or faceting, if cleaner) so emission peaks remain positive while absorption dips can plot on a logically separate axis with descriptive labels.
  6. Provide unit conversions only when scientifically compatible—e.g., Fλ ↔ Fν using ν = c/λ and the appropriate Jacobian—and surface helper text for unit families that cannot convert cleanly. Update exports to preserve the original and display units.
  7. Cache processed solar datasets under `data/examples/` (Parquet/Feather) and memoize loads inside Streamlit to keep the UI responsive.
- **Verification**
  - Automated: `pytest` (full suite) and any targeted unit tests for new preprocessing or overlay helpers.
  - Manual: launch Streamlit, confirm archive metadata/provenance expanders are collapsed by default, verify overlay visibility toggles behave smoothly, inspect the solar example (smoothed default, raw toggle, band filters), and ensure dual-axis labeling matches the underlying unit semantics.
- **Provenance**
  - User direction (2025-09-22) requesting v1.1.6b to collapse archive metadata, remove redundant overlay checkboxes, add a telescope-observed solar example with smoothing/full-resolution toggles, and document unit handling for emission vs absorption overlays.

## Knowledge Capture
- **Spectral flux density (Fλ)** expresses energy per unit area, time, and wavelength (e.g., W·m⁻²·nm⁻¹ or erg·s⁻¹·cm⁻²·Å⁻¹). Converting between wavelength and frequency representations requires Jacobian scaling (Fν = Fλ · λ² / c).
- **Spectral radiance (Iλ)** adds per-steradian context (W·m⁻²·sr⁻¹·nm⁻¹) and should not co-plot with flux density without explicit conversion or annotation.
- **Emission lines** rise above the continuum baseline, whereas **absorption lines** represent deficits relative to the continuum; plotting them on distinct y-axes (or using sign conventions) prevents misinterpretation when units mix.
- Band definitions for the solar example can follow approximate wavelength ranges: IR (>700 nm), Near-IR (700–1400 nm), VIS (380–700 nm), UV-VIS (320–380 nm), UV (10–320 nm). Tagging each sample enables quick filtering without recomputation.

## Follow-up Considerations
- Evaluate whether unit conversion helpers should live in a dedicated module to serve both archives and uploads.
- Consider capturing instrument/integration metadata in the solar example metadata to reinforce provenance in exports and overlays.
