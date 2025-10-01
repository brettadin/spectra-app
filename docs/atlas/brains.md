# Axis-aware viewport handling — 2025-10-08
- Maintain a `viewport_axes` session map keyed by axis kind so wavelength and time traces stop overwriting each other's zoom state.
- Mixed-axis overlays reuse per-kind ranges during sampling/export while the chart surfaces a "Mixed axes" title and warning instead of forcing a shared x-range.
- Export payloads now include `axis_kind` + unit metadata, keeping time-series rows intact when spectral viewports tighten.

## Overlay clear control relocation — 2025-10-08
- Move the destructive "Clear overlays" action into the Display & viewport cluster so overlay management lives beside viewport tools.
- Raise a transient warning banner within the overlay tab after clearing so users receive immediate confirmation in the workspace context.
- Differential tab keeps its reference selector without destructive controls, reducing the risk of accidental overlay loss while preparing comparisons.

## Image overlay ingestion — 2025-10-10
- Treat FITS HDUs lacking spectral axes but carrying WCS metadata as `axis_kind="image"`, preserving masks, shape, and WCS serialisation for downstream viewers. 【F:app/server/ingest_fits.py†L1120-L1350】
- Skip spectral sample requirements in local ingest, summarising images via pixel dimensions while leaving existing spectral flows untouched. 【F:app/utils/local_ingest.py†L433-L517】
- Overlay UI renders Plotly heatmaps with intensity sliders and excludes image traces from spectral viewport math to keep axis warnings accurate. 【F:app/ui/main.py†L1910-L2079】【F:app/ui/main.py†L1608-L1756】

## Byte-string FITS unit coercion — 2025-10-10
- Normalise FITS wavelength/time unit hints by decoding header bytes through `_coerce_header_value` before canonical checks so `TUNIT`/`CUNIT` byte strings match aliases. 【F:app/server/ingest_fits.py†L233-L305】【F:app/server/ingest_fits.py†L751-L799】
- Preserve time-frame detection by case-folding decoded hints, keeping BJD offsets intact when headers arrive as byte strings. 【F:app/server/ingest_fits.py†L233-L305】
- Locked regression coverage on byte-string table headers to ensure wavelength and time ingestion keep reporting the right `axis_kind`. 【F:tests/server/test_ingest_fits.py†L375-L395】【F:tests/server/test_ingest_fits.py†L442-L466】

## Example browser provider persistence — 2025-10-11
- Only seed the provider multiselect with defaults when the session key is unset so Streamlit relies on the stored selection thereafter, eliminating rerun warnings. 【F:app/ui/example_browser.py†L192-L210】
- Normalise any cached provider list before rendering and sync it back to session state so stale providers disappear without losing user intent. 【F:app/ui/example_browser.py†L185-L197】

## Example browser provider filter normalisation — 2025-10-12
- Populate the provider filter session key via `setdefault` and mutate the cached list in place so reruns keep user selections without triggering Streamlit's state reassignment warning. 【F:app/ui/example_browser.py†L189-L207】
- Keep the UI regression that drives reruns with narrowed and stale providers to ensure the warning stays silent while selections persist. 【F:tests/ui/test_example_browser.py†L63-L97】

## Example browser provider setdefault guard — 2025-10-12
- Seed the provider filter session key before constructing the widget and defer normalisation until after the multiselect returns so reruns avoid Streamlit's "widget has already been registered" warning. 【F:app/ui/example_browser.py†L185-L220】
- Extended the AppTest assertions to capture warning output explicitly while verifying narrowed and stale selections persist across reruns. 【F:tests/ui/test_example_browser.py†L107-L128】【F:tests/ui/test_example_browser.py†L213-L215】

## Asynchronous overlay ingest queue — 2025-10-11
- Manage overlay downloads through a session-scoped executor that tracks queued, running, and completed jobs with shared progress snapshots for reruns to consume. 【F:app/ui/main.py†L526-L792】
- Render an “Overlay downloads” sidebar cluster so users can watch job states resolve without leaving the workspace controls. 【F:app/ui/main.py†L795-L839】【F:app/ui/main.py†L3426-L3451】
- Locked a regression that stalls network fetches to prove reruns stay responsive and jobs surface success once the worker completes. 【F:tests/ui/test_overlay_ingest_queue_async.py†L12-L112】

## Differential controls relocate to workspace — 2025-10-11
- Move normalization and differential-mode selectors into the differential tab so the compute form and explanatory caption live together, avoiding sidebar context switches during analysis. 【F:app/ui/main.py†L3097-L3130】【F:app/ui/main.py†L3285-L3288】
- House similarity metric, weighting, and normalization widgets in a tab expander so users configure comparisons beside the plotted results instead of scrolling the sidebar. 【F:app/ui/main.py†L3132-L3190】
- Verified the relocation with focused UI tests that assert the sidebar no longer exposes these controls while the differential tab does. 【F:tests/ui/test_sidebar_display_controls.py†L1-L33】【F:tests/ui/test_differential_form.py†L1-L109】

## Target library overlay gating — 2025-10-01
- Parse manifest extension metadata for axis keywords and dimensionality before enabling overlays so only 1-D spectra and time series remain interactive. 【F:app/ui/targets.py†L19-L219】
- Treat JWST CALINTS cubes as unsupported even when labelled as time-series, wiring the disabled overlay button to explain the axis mismatch. 【F:app/ui/targets.py†L181-L199】
- Extended regression coverage proving axis-hint parsing blocks CALINTS cubes and missing time axes. 【F:tests/ui/test_targets_overlay_support.py†L24-L98】

## Target catalog summary-first layout — 2025-10-12
- Render the target manifest name, narrative summary, and status metrics in a dedicated container before offering the registry grid so the curated context stays visible. 【F:app/ui/targets.py†L260-L326】
- Tuck the full catalog dataframe into an optional “Browse catalog entries” expander, keeping the manifest summary adjacent to the curated product groups. 【F:app/ui/targets.py†L328-L352】
- Locked a regression asserting the new expander label is present and the grid remains available for discovery. 【F:tests/ui/test_targets_panel_layout.py†L53-L74】
