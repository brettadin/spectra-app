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
- Only seed the provider multiselect with defaults when the session key is unset so Streamlit relies on the stored selection thereafter, eliminating rerun warnings. 【F:app/ui/example_browser.py†L199-L218】
- Normalise any cached provider list before rendering and sync it back to session state so stale providers disappear without losing user intent. 【F:app/ui/example_browser.py†L185-L198】

## Asynchronous overlay ingest queue — 2025-10-11
- Manage overlay downloads through a session-scoped executor that tracks queued, running, and completed jobs with shared progress snapshots for reruns to consume. 【F:app/ui/main.py†L526-L792】
- Render an “Overlay downloads” sidebar cluster so users can watch job states resolve without leaving the workspace controls. 【F:app/ui/main.py†L795-L839】【F:app/ui/main.py†L3426-L3451】
- Locked a regression that stalls network fetches to prove reruns stay responsive and jobs surface success once the worker completes. 【F:tests/ui/test_overlay_ingest_queue_async.py†L12-L112】
