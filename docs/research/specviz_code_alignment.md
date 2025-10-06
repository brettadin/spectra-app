# SpecViz Adaptation — Code Alignment Review

## 1. GitHub documentation takeaways
- **Layered application engine** — The `Jdaviz Design and Infrastructure` note shows how each viewer layout, plugin registry, and event hub lives in a shared application engine that orchestrates glue-jupyter widgets while pushing reusable logic upstream.[^jdaviz-infrastructure]
- **Vue/traitlet component pattern** — Plugin components are split into Python mixins plus `.vue` templates registered at startup so reusable controls (subset selectors, model fit editors, etc.) stay reactive without duplicating traitlet wiring.[^jdaviz-plugin-components]
- **Glupyter separation of state vs. view** — The UI design guide emphasises keeping widget state in Python traitlets while delegating rendering to Vuetify templates, enabling procedural control in notebooks alongside GUI interactions.[^jdaviz-ui-overview]
- **Subset propagation as spectral regions** — The selection primer highlights that Specviz converts interactive selections into `specutils.SpectralRegion` masks returned through helper APIs, ensuring plugins and exports consume identical definitions.[^jdaviz-selections]

## 2. Spectra App baseline (2025-10)
### 2.1 Overlay data model and rendering
- `OverlayTrace` keeps every loaded series (label, units, provenance, cached down-samples) in session state so tables, charts, and exports share a canonical payload.[^spectra-overlay-trace]
- Sampling honours viewport bounds, tiered down-samples, and LTTB fallbacks before streaming vectors to similarity metrics or Plotly figures, echoing Specviz’s need for responsive rendering with dense spectra.[^spectra-overlay-sample]

### 2.2 Async ingestion and duplicate control
- The ingest queue lazily seeds a session-scoped `ThreadPoolExecutor`, normalises queued items, and records progress snapshots for the sidebar “Overlay downloads” panel.[^spectra-ingest-runtime]
- Each job resolves archives, annotates provenance (`ingest.method`, URLs, cache hits), then hands payloads to `_add_overlay_payload`, which also walks any companion traces and records ledger fingerprints to block duplicates.[^spectra-ingest-prep]
- Local uploads detect ASCII/FITS/ZIP payloads, auto-decompress when required, and fall back to dense parsers for million-row tables while synthesising user-facing labels and summaries.[^spectra-local-ingest]

### 2.3 Analysis pipelines
- The similarity stack memoises pairwise metrics behind `SimilarityCache`, normalises traces per user choice, and renders ribbon + matrix summaries via `render_similarity_panel` tabs.[^spectra-similarity]
- Differential maths resamples pairs onto a shared grid and exposes subtraction/ratio helpers that downstream panels already call.[^spectra-differential]

### 2.4 Export and provenance
- `build_manifest` gathers export timestamps, version metadata, continuity links, and per-series counts so CSV/PNG dumps stay auditable.[^spectra-manifest]
- The duplicate ledger hashes payloads to disk, tracks session IDs, and offers purge hooks so reruns reset state, mirroring Specviz’s emphasis on reproducible ingestion.[^spectra-duplicate-ledger]

### 2.5 Target registry governance
- The targets panel scans manifest axis hints, filters to 1-D-compatible products, and surfaces user-facing rejection reasons (e.g., JWST CALINTS cubes) before enabling overlay actions.[^spectra-targets]

## 3. Alignment opportunities
| Specviz insight | Spectra baseline | Adoption tasks |
| --- | --- | --- |
| Application engine manages layouts + plugin registry.[^jdaviz-infrastructure] | Streamlit entrypoint imports `app.ui.main` and renders everything inside a monolithic module.[^spectra-main-entry] | Extract a registry-driven panel manager so sidebar/workspace panels register like Jdaviz plugins, enabling mode-specific layouts. |
| Vue/traitlet components encapsulate reusable controls.[^jdaviz-plugin-components] | Controls are repeated across sidebar forms and tabs (normalisation widgets, overlay toggles).[^spectra-main-controls] | Introduce reusable component classes (e.g., overlay visibility, normalization) to reduce duplication and prepare for notebook embedding. |
| Traitlet-backed state enables notebook automation.[^jdaviz-ui-overview] | Session state and helper functions exist but lack a thin API for notebook users (`SpectraApp.load_data`, `SpectraApp.get_overlays`).[^spectra-overlay-trace][^spectra-ingest-prep] | Wrap ingest/add/export flows in helper classes returning dataclasses so notebooks can control the app without Streamlit. |
| Spectral selections become `specutils.SpectralRegion` masks fed into helpers.[^jdaviz-selections] | ROI selection does not yet persist beyond Plotly interactions; exports/manifests lack subset masks.[^spectra-overlay-sample] | Store Plotly selection bounds in session state, convert to `specutils` regions, and extend manifest/export payloads to include them. |
| Plugins share specutils/astropy pipelines for smoothing, fitting, etc.[^jdaviz-infrastructure] | Similarity/differential math live in bespoke modules without specutils integration.[^spectra-similarity][^spectra-differential] | Evaluate migrating normalization/fitting to `specutils` routines, exposing plugin-style hooks for advanced analysis. |

## 4. Immediate next steps
1. Draft a `panel_registry` module that mirrors Specviz’s plugin registration (ID, label, render callable) and refactor overlay/similarity/differential panels to register themselves before render.[^spectra-main-entry]
2. Prototype a `SpectraWorkspace` helper exposing `load_overlay`, `list_overlays`, and `export_view` methods backed by `_add_overlay_payload` and `build_manifest`, enabling notebook parity with Specviz helpers.[^spectra-ingest-prep][^spectra-manifest]
3. Capture viewport-derived selections inside `OverlayTrace` and serialise them into export manifests while experimenting with `specutils.SpectralRegion` for ROI persistence.[^spectra-overlay-trace][^spectra-overlay-sample]
4. Spike a specutils-based fitting plugin by wrapping similarity normalization options around `specutils.manipulation` utilities and comparing outputs against existing NumPy routines.[^spectra-similarity]
5. Update docs/UI contract once the registry abstraction lands, ensuring layout and provenance promises stay aligned with the v1.2+ continuity checklist.

[^jdaviz-infrastructure]: “Jdaviz Design and Infrastructure,” *Jdaviz Docs* (GitHub). <https://raw.githubusercontent.com/spacetelescope/jdaviz/main/docs/dev/infrastructure.rst>
[^jdaviz-plugin-components]: “Plugin Components,” *Jdaviz Docs* (GitHub). <https://raw.githubusercontent.com/spacetelescope/jdaviz/main/docs/dev/ui_plugin_components.rst>
[^jdaviz-ui-overview]: “Glupyter Framework Overview,” *Jdaviz Docs* (GitHub). <https://raw.githubusercontent.com/spacetelescope/jdaviz/main/docs/dev/ui_description.rst>
[^jdaviz-selections]: “Specviz Selections,” *Jdaviz Docs* (GitHub). <https://raw.githubusercontent.com/spacetelescope/jdaviz/main/docs/dev/specviz_selection.rst>
[^spectra-overlay-trace]: `OverlayTrace` data model defining shared metadata for loaded spectra. 【F:app/ui/main.py†L63-L135】
[^spectra-overlay-sample]: `OverlayTrace.sample` handles viewport filtering, tiered down-samples, and LTTB fallbacks. 【F:app/ui/main.py†L102-L171】
[^spectra-ingest-runtime]: Ingest runtime initialisation and job tracking for the overlay queue. 【F:app/ui/main.py†L550-L833】
[^spectra-ingest-prep]: Ingest payload preparation adds provenance and duplicate protection before registering overlays. 【F:app/ui/main.py†L587-L1228】
[^spectra-local-ingest]: Local ingestion detects formats, decompresses archives, and synthesises overlay metadata. 【F:app/utils/local_ingest.py†L17-L200】
[^spectra-similarity]: Similarity metrics, caching, and Streamlit rendering pipeline. 【F:app/similarity.py†L1-L200】【F:app/similarity_panel.py†L1-L118】
[^spectra-differential]: Differential helpers resample traces and compute subtraction/ratio. 【F:app/server/differential.py†L1-L33】
[^spectra-manifest]: Export manifest builder captures version metadata and per-series counts. 【F:app/export_manifest.py†L1-L55】
[^spectra-duplicate-ledger]: Duplicate ledger hashes payloads and scopes entries per session. 【F:app/utils/duplicate_ledger.py†L1-L38】
[^spectra-targets]: Target panel analyses manifest axis hints to gate overlay enablement. 【F:app/ui/targets.py†L1-L200】
[^spectra-main-entry]: Streamlit entry point imports `app.ui.main` and defers to `render()`. 【F:app/app_merged.py†L1-L74】【F:app/ui/entry.py†L1-L19】
[^spectra-main-controls]: Overlay, normalization, and analysis controls share duplicated widget wiring inside `app/ui/main.py`. 【F:app/ui/main.py†L883-L1276】【F:app/ui/main.py†L3097-L3190】
