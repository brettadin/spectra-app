# Overlay trace helper relocation — 2025-10-17
- Shifted dataframe conversion, sampling, vectorisation, and point counting helpers onto `OverlayTrace` so downstream UI logic works directly with the trace model instead of ingest result shims. 【F:app/ui/main.py†L43-L174】
- Updated overlay regressions to rely on the embedded helpers while covering mixed-axis figure builds and metadata summaries. 【F:tests/ui/test_overlay_mixed_axes.py†L9-L118】【F:tests/ui/test_metadata_summary.py†L1-L229】

# Time-axis offset normalization — 2025-10-16
- Subtract detected FITS time-axis offsets before storing payload values so time-series overlays render near zero while keeping the original epoch in metadata and provenance. 【F:app/server/ingest_fits.py†L1468-L1505】
- Extend the UI helpers to reuse time-axis provenance for axis titles and metadata summaries, surfacing reference epochs alongside the de-offset ranges. 【F:app/ui/main.py†L1693-L1753】【F:app/ui/main.py†L2230-L2249】
- Harden ingestion, local ingest, and UI regressions with BJD-offset fixtures to ensure ranges start near zero and provenance cites the removed offset. 【F:tests/server/test_ingest_fits.py†L435-L557】【F:tests/server/test_local_ingest.py†L633-L686】【F:tests/ui/test_metadata_summary.py†L133-L160】【F:tests/ui/test_overlay_mixed_axes.py†L7-L127】

# FITS wavelength alias canonicalisation — 2025-10-15
- Funnel `_normalise_wavelength_unit` candidates through a canonicaliser so byte-decoded aliases (e.g., `Angstroms`) resolve to the singular FITS label before `_unit_is_wavelength` validates them. 【F:app/server/ingest_fits.py†L758-L805】
- Let `_unit_is_wavelength` trust canonical strings while still decoding defensive byte inputs, ensuring previously-normalised units skip redundant coercion. 【F:app/server/ingest_fits.py†L343-L356】
- Locked regressions for plural byte `TUNIT`/`CUNIT` headers to prove ingestion surfaces canonical units and preserved metadata. 【F:tests/server/test_ingest_fits.py†L371-L426】

# Overlay ingest thread-safety — 2025-10-14
- **REF 1.2.0x-A01**: Route overlay payload additions through the main thread by returning ingest results from worker futures and finalising state updates in `_refresh_ingest_jobs`, eliminating cross-thread Streamlit mutations. 【F:app/ui/main.py†L621-L678】【F:app/ui/main.py†L680-L713】
- Hardened the ingest queue regression to assert queued overlays complete without `ScriptRunContext` warnings while preserving async progress. 【F:tests/ui/test_overlay_ingest_queue_async.py†L9-L128】
- Added the v1.2.0x patch log entry so `_resolve_patch_metadata()` propagates the main-thread ingestion summary to the header and Docs banner. 【F:PATCHLOG.txt†L27-L27】【F:tests/ui/test_docs_tab.py†L16-L102】
- Recorded the thread-safety fix in the v1.2.0x patch notes and AI activity log alongside the version bump. 【F:docs/patch_notes/v1.2.0x.md†L1-L21】【F:app/version.json†L1-L5】【F:docs/ai_log/2025-10-14.md†L1-L16】

# Runtime manifest continuity — 2025-10-13
- **REF 1.2.0w-A01**: Restored `docs/runtime.json` to a single JSON object so tooling can parse python, platform, and library metadata without errors. 【F:docs/runtime.json†L1-L23】
- Recorded the fix in the v1.2.0w patch notes and AI log while bumping the version manifest to keep release metadata aligned. 【F:docs/patch_notes/v1.2.0w.md†L1-L15】【F:docs/ai_log/2025-10-01.md†L1-L15】【F:app/version.json†L1-L5】
- Alternative considered: mirror the runtime manifest into YAML for readability, but JSON remains the contract consumed by automation so we kept the format and corrected structure instead.

# Patch log continuity — 2025-10-13
- **REF 1.2.0v-A01**: Added the `v1.2.0v` patch log entry so `_resolve_patch_metadata()` keeps the header and Docs banner in sync with version metadata. 【F:PATCHLOG.txt†L24-L26】【F:app/_version.py†L30-L64】
- Locked the Docs tab and header regression against the quick-add summary so continuity helpers surface the expected copy without manual updates. 【F:tests/ui/test_docs_tab.py†L16-L78】
- Rolled the release docs (brains, patch notes, AI log) to capture the alignment work. 【F:docs/patch_notes/v1.2.0v.md†L1-L22】【F:docs/brains/brains_v1.2.0v.md†L1-L17】【F:docs/ai_log/2025-10-13.md†L1-L22】

# Examples quick-add focus — 2025-10-13
- Remove the example browser launcher and associated favourites/recents panels so the Examples sidebar leans on the quick-add selector only. 【F:app/ui/main.py†L1230-L1245】
- Drop the dormant browser state initialisers to prevent future Streamlit warnings now that the sheet is gone. 【F:app/ui/main.py†L468-L483】
- Refresh the sidebar regression to assert the button is gone while the quick-add form remains reachable. 【F:tests/ui/test_sidebar_examples.py†L1-L37】

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
