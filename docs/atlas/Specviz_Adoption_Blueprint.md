# Specviz Adoption Blueprint

## 1. Why Specviz is a relevant benchmark
* **End-to-end spectral workflows:** Specviz delivers a complete 1D spectral experience, from ingestion to analysis to export, all within a consistent interface.
* **Shared stack alignment:** The application builds on the Astropy and specutils ecosystems that Spectra App already targets, easing conceptual reuse.
* **Hybrid UI patterns:** Specviz runs as a desktop app, Jupyter helper, or embedded web widget without diverging UX models, offering reusable design blueprints for our Streamlit shell.

## 2. Feature inventory distilled from JDaviz/Specviz
### 2.1 Data ingestion surfaces
* Command-line bootstrap: `jdaviz --layout=specviz` accepts optional file paths and multiple spectra, allowing scripted batch launches.
* GUI import dialog: the in-app *Import Data* button walks users through local file selection with success notifications and labeling for viewer menus.
* Helper API: `Specviz.load_data` ingests `specutils.Spectrum`, paths, SpectrumList collections, JWST `MultiSpecModel`, and even generated NumPy arrays.
* List-aware workflows: SpectrumList ingestion creates both combined and component traces, with optional concatenation controls tailored to JWST MIRI data.

### 2.2 Visualization & interaction patterns
* Glue-powered viewers: modular viewers let users toggle layers, manage visibility per dataset, and remove or re-add traces via a contextual data menu.
* Rich toolbar: cursor readouts, home, pan/zoom variants (2D, horizontal, vertical), and right-click option swapping promote discoverability for fine-grained navigation.
* Spectral regions: draggable ROIs, subset management, and API hooks via Glue ROIs enable repeatable selections for downstream plugins.
* Plot styling: layer-specific line color, width, opacity, step profile toggle, and uncertainty overlays unify UI controls with API parity for automation.

### 2.3 Analysis plugin suite
* Metadata & plot options: quick-inspection panes centralize WCS/metadata and viewer tuning so scientists avoid context switching.
* Gaussian smoothing: configurable kernel smoothing spawns derived spectra that auto-display and stay available to other plugins.
* Model fitting: component-driven Astropy model assembly with equation editor, fitter selection, parameter locking, and API automation covers common emission/absorption modeling use cases.
* Unit conversion: decoupled spectral and flux unit pickers keep data in canonical units while presenting user-preferred axes.
* Line lists & redshift slider: curated and custom line catalogs with interactive redshift adjustments help align catalogs with observed features, accessible via UI or helper methods.
* Line analysis: continuum fitting, centroid/FWHM/flux reporting, and centroid-to-redshift propagation deliver repeatable measurements tied to spectral subsets.
* Export plugin: viewer snapshots plus spectral/spatial region exports (FITS/REG/ECSV) keep analysis outputs portable.

### 2.4 Export & notebook integration
* `Specviz.get_spectra()` returns Spectrum objects or labeled dictionaries that reflect UI selections, bridging visual work and notebooks.
* Helper accessors provide masked subset extraction, region dictionaries, fitted model retrieval, and Astropy Table exports for plugin tables.

### 2.5 Architectural takeaways
* Helper pattern: each configuration exposes a helper object that unifies viewer access, plugin control, and data exchange for scripted workflows.
* Plugin registry: self-describing plugin modules cover discovery, UI layout, and API surfaces, simplifying extension and reuse across configurations.
* Glue/event backbone: region selections, viewer state, and plugin communication ride on Glue’s event system, ensuring consistent synchronization without bespoke wiring.

## 3. Gap analysis vs. Spectra App
* **Data ingestion breadth:** Our current loaders lack SpectrumList stitching, JWST datamodel support, and CLI parity; replicating Specviz patterns would unlock richer JWST and MIRI workflows.
* **Viewer ergonomics:** Streamlit wrappers provide fewer navigation affordances than Specviz’s toolbar, limiting productivity for deep spectral inspection.
* **Analysis depth:** Spectra App presently offers limited plugin-caliber tools; adopting Specviz’s Gaussian smoothing, modeling, unit conversion, and line-analysis flows would satisfy user requests for quick-look measurements.
* **Export fidelity:** We lack the selective export hooks (subsets, models, tables) that let Specviz bridge interactive and scripted analysis.
* **Automation bridge:** Without a helper-style API, our UI cannot be scripted headlessly, impeding reproducibility compared to Specviz notebooks.

## 4. Adoption strategy
### Phase 0 — Alignment groundwork
1. **Adopt specutils as the canonical spectrum container** to mirror Specviz expectations and reduce conversion friction.
2. **Map Spectra App state to helper semantics** (viewers, plugins, data registry) so API hooks can mirror Specviz method names where sensible.
3. **Assess packaging/licensing** for embedding JDaviz components or selectively porting patterns while preserving BSD compatibility.

### Phase 1 — Ingestion parity
1. Implement CLI entry invoking our Streamlit app with optional dataset paths, aligning with `jdaviz --layout=specviz` ergonomics.
2. Extend UI importers to accept multiple files, SpectrumList-style directories, and JWST datamodel extracts with concatenation toggles.
3. Expose a Python helper for `load_data` equivalents (path, Spectrum, SpectrumList, URL), ensuring idempotent labeling and notifications.

### Phase 2 — Viewer & interaction uplift
1. Introduce modular viewer classes to manage layer toggles, cursor overlays, and saved zoom states akin to Glue-powered viewers.
2. Port pan/zoom tooling (2D, axis-locked, history) plus spectral region creation with ROI persistence and API accessors.
3. Recreate plot options tray with layer-specific styling toggles and uncertainty overlays, synchronized with helper methods.

### Phase 3 — Analysis plugin suite
1. Build plugin architecture supporting tray registration, dataset/subset selectors, and derived-layer publication.
2. Implement priority plugins: Gaussian smoothing, model fitting (Astropy), unit conversion, line lists with redshift slider, and line analysis summaries.
3. Ensure plugin outputs integrate with viewer layers, export routines, and helper APIs for reproducibility.

### Phase 4 — Export, provenance, and scripting
1. Mirror `get_spectra`, `get_data`, `get_regions`, and `get_models` helpers so interactive work can be serialized into specutils objects and Astropy tables.
2. Add export plugin for viewer captures plus FITS/REG/ECSV region outputs, respecting Spectra App’s provenance manifest requirements.
3. Document scripting recipes showing helper-driven automation for tests and reproducible science notebooks.

## 5. Technical integration considerations
* **Streamlit embedding of Glue widgets:** Evaluate ipywidgets → Streamlit bridges (e.g., `streamlit-ipywidgets`) or reimplement viewer primitives with Plotly while preserving API semantics.
* **State management:** Adopt a central registry akin to JDaviz’s `app.data_collection`, ensuring selections/subsets propagate consistently between viewers and plugins.
* **Performance:** JDaviz warns about redshift slider performance with many lines; we should plan virtualization and throttling strategies for large catalogs.
* **Testing parity:** Reproduce plugin API usage patterns in integration tests to guarantee helper compatibility and regression coverage for ROI/export flows.

## 6. Follow-up research tasks
1. Deep-dive JDaviz helper implementation (`jdaviz/configs/specviz/helper.py`) to model our helper class contract.
2. Audit plugin source modules for UI/layout patterns we can adapt into Streamlit components or wrappers.
3. Explore JDaviz’s exporter code paths to ensure our provenance hooks capture derived regions, models, and tabular outputs consistently.
4. Engage with STScI docs (JWST mode coverage, citation guidance) to align documentation and credit when referencing JDaviz assets.
