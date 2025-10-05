# SpecViz Adaptation Blueprint

## 1. External Capability Survey

### 1.1 Platform scope and delivery
- **Multi-surface distribution**: Jdaviz applications run inside notebooks, as standalone browser apps launched via the `jdaviz` CLI, and embed consistently across environments, enabling the same UI to cover desktop, lab, and web workflows.[^quickstart]
- **Configuration presets**: Specviz (1D spectra), Cubeviz (data cubes + extracted spectra), Specviz2D (slit and IFU cutouts), Mosviz (multi-object sets), Imviz (2D images), and Rampviz provide tuned layouts over a shared engine so teams can mix viewers to match data shapes.[^specviz-index]

### 1.2 Data ingestion expectations
- **Spectrum-first contract**: Specviz only accepts inputs convertible to `specutils.Spectrum` objects, delegating parsing to `specutils` while keeping the viewer API coherent.[^specviz-import]
- **Multiple entry points**: Data load flows include CLI arguments, a GUI import dialog, and helper APIs (`Specviz.load_data`) that accept file paths, in-memory spectra, NumPy arrays with units, and JWST `stdatamodels` products.[^specviz-import]
- **Reusable products**: Documentation calls out “Jdaviz-readable products” guidelines so upstream pipelines can emit compliant artifacts that slot directly into viewers.[^user-guide-products]

### 1.3 Visualization and interactivity
- **Glue-powered viewers**: Display tooling leans on Glue’s data layer model, letting users toggle datasets per viewer, detach or reload layers, and coordinate UI state with plugin dropdowns.[^specviz-display]
- **Cursor + tool affordances**: Built-in controls cover cursor readouts, zoom history, box/x-range zoom, pan variants, axis lock, and programmable `set_limits`/`reset_limits` helpers for automation.[^specviz-display]
- **Region semantics**: Spectral subsets rely on Glue ROIs and propagate into plugins, exports, and API helpers for reproducible slice definitions.[^specviz-display]

### 1.4 Plugin ecosystem
- **Plugin tray architecture**: Analysis actions live in a tray surfaced by the plugin icon; outputs add new spectra/layers automatically while sharing a data menu for visibility control.[^specviz-plugins]
- **Specviz toolchain**: Core plugins span metadata/plot options, subset tools, markers, Gaussian smoothing, Astropy-powered model fitting (with equation editor + fitter choice), unit conversion, line lists, and line analysis, each scriptable through helper APIs.[^specviz-plugins]
- **Cubeviz & Specviz2D additions**: Cubeviz introduces collapse, spectral extraction, aperture photometry, moment maps, slicing, sonification, and region exports; Specviz2D focuses on slit extraction and 2D-specific plugin variants.[^cubeviz-plugins][^specviz2d-index]
- **Extensibility registry**: The reference API exposes helper classes, viewer registries, parser hooks, and plugin modules per configuration, reinforcing a modular registration system for new tools.[^reference-api]

### 1.5 Export and state management
- **Data extraction**: `get_spectra`/`get_data` return `Spectrum` objects (with subset masks) for notebook reuse; plugin tables (e.g., model fits, spectral regions, marker catalogs) offer export helpers back to Python or disk (ECSV).[^specviz-export]
- **Session persistence**: Users can save viewer state and plugin outputs, and documentation emphasizes round-tripping derived products into upstream workflows.[^user-guide-session]

### 1.6 Scientific coverage and provenance
- **JWST focus**: Mode tables enumerate supported NIRSpec, MIRI, NIRISS, and other JWST observing setups, illustrating how viewer presets adapt to instrument metadata.[^jwst-modes]
- **Citation guidance**: The project publishes Zenodo DOIs and attribution text, embedding citation practices into user documentation and export flows.[^jdaviz-citation]

## 2. Gap Analysis for Spectra App

| Capability | Jdaviz Pattern | Spectra App Opportunity |
| --- | --- | --- |
| Data ingestion | Spectrum-centric contract with CLI/GUI/API loaders | Define canonical ingest API that wraps our FITS/table handlers and mirrors helper ergonomics for notebooks & automation. |
| Viewer ergonomics | Glue-backed layer toggles, zoom history, ROI propagation | Audit our Plotly viewers for parity: add layer menus, zoom stacks, and ROI export hooks aligned with Glue semantics. |
| Analysis plugins | Tray-based plugins covering smoothing, model fits, line tools | Refactor Streamlit sidebar into pluggable panels with shared data selectors, using Astropy/specutils for heavy lifting. |
| Export surface | Consistent Python-returning helpers and ECSV dumps | Formalize `get_overlay_data`/`export_*` APIs that emit standardized tables & spectra, preserving subset masks and provenance. |
| Configuration presets | Named layouts for spectrum, cube, MOS, 2D use cases | Introduce layout profiles (spectral, differential, cube) that toggle widgets and defaults without code forks. |
| JWST instrument alignment | Documented mode support & metadata-driven defaults | Tie our registry to JWST mode metadata so available tools, unit defaults, and warnings track instrument context. |
| Provenance & citation | Built-in citation copy + DOI references | Extend export manifest to include citation templates and remind users about data/tool attribution. |

## 3. Adoption Roadmap

### Phase 0 — Discovery (1–2 sprints)
1. Catalogue our current ingest paths, viewer widgets, and analysis helpers against the matrix above; flag blockers for Spectrum-object parity.
2. Prototype a minimal helper class mirroring `Specviz.load_data`/`get_data`, backed by our overlay store, to validate API ergonomics in notebooks.
3. Inventory existing plugin-like panels (e.g., overlay math, line lists) and map them to a tray framework concept document.

### Phase 1 — Infrastructure alignment (3–4 sprints)
1. Ship a pluggable panel framework: registerable plugin objects with lifecycle hooks, shared data selectors, and policy for derived layer naming.
2. Normalize ingestion around Spectrum-like dataclasses, including JWST datamodel adapters and specutils compatibility shims.
3. Implement viewer layer menus, zoom history, and ROI serialization mirroring Glue behavior, ensuring UI contract coverage.

### Phase 2 — Feature parity (4–6 sprints)
1. Port high-value plugins (Gaussian smooth, model fitting, unit conversion, line lists/analysis) using Astropy components to match Specviz outputs.
2. Wire export APIs for spectra, subsets, model tables, and markers with ECSV/ASDF outputs and provenance stamps.
3. Introduce configuration presets that rearrange viewers/controls for spectral, cube, and MOS workflows, gated by metadata heuristics.

### Phase 3 — Advanced integration (ongoing)
1. Embed JWST mode awareness (unit defaults, warning banners, plugin enablement) derived from an instrument capability table.
2. Offer helper APIs for saving/loading session state, aligning with Jdaviz’s session export guidance for reproducibility.
3. Publish citation snippets and DOIs alongside exports, mirroring Jdaviz’s documentation cues.

## 4. Research Backlog & Open Questions
- **Glue integration depth**: Evaluate whether adopting Glue’s data structures directly would simplify ROI propagation or if a lighter compatibility layer suffices.
- **Specutils adoption plan**: Determine scope for leveraging specutils (e.g., uncertainties, spectral regions) without overhauling existing pandas/NumPy pipelines.
- **Plugin sandboxing**: Define security and performance expectations if we allow user-authored plugins, inspired by Jdaviz’s registry-based approach.
- **Session persistence UX**: Decide between file-based session dumps or database-backed histories, referencing Jdaviz’s save-state mechanics.

## 5. Source Links
- Quickstart & CLI usage: <https://jdaviz.readthedocs.io/en/latest/quickstart.html>
- Specviz data loading: <https://jdaviz.readthedocs.io/en/latest/specviz/import_data.html>
- Specviz display tooling: <https://jdaviz.readthedocs.io/en/latest/specviz/displaying.html>
- Specviz plugins: <https://jdaviz.readthedocs.io/en/latest/specviz/plugins.html>
- Specviz exports: <https://jdaviz.readthedocs.io/en/latest/specviz/export_data.html>
- Cubeviz plugins and exports: <https://jdaviz.readthedocs.io/en/latest/cubeviz/plugins.html>
- Specviz2D overview: <https://jdaviz.readthedocs.io/en/latest/specviz2d/index.html>
- Mosviz overview: <https://jdaviz.readthedocs.io/en/latest/mosviz/index.html>
- Developer API registry: <https://jdaviz.readthedocs.io/en/latest/reference/api.html>
- JWST mode support: <https://jdaviz.readthedocs.io/en/latest/index_jwst_modes.html>
- Citation guidance: <https://jdaviz.readthedocs.io/en/latest/index_citation.html>

[^quickstart]: “Quickstart,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/quickstart.html>
[^specviz-index]: “Specviz,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/specviz/index.html>
[^specviz-import]: “Importing Data Into Specviz,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/specviz/import_data.html>
[^user-guide-products]: “Creating Jdaviz-readable Products,” *Jdaviz User Guide*. <https://jdaviz.readthedocs.io/en/latest/index_using_jdaviz.html#creating-jdaviz-readable-products>
[^specviz-display]: “Displaying Spectra,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/specviz/displaying.html>
[^specviz-plugins]: “Data Analysis Plugins,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/specviz/plugins.html>
[^cubeviz-plugins]: “Data Analysis Plugins (Cubeviz),” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/cubeviz/plugins.html>
[^specviz2d-index]: “Specviz2D,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/specviz2d/index.html>
[^reference-api]: “Reference/API,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/reference/api.html>
[^specviz-export]: “Exporting Data From Specviz,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/specviz/export_data.html>
[^user-guide-session]: “Saving the State of Your Jdaviz Session,” *Jdaviz User Guide*. <https://jdaviz.readthedocs.io/en/latest/index_using_jdaviz.html#saving-the-state-of-your-jdaviz-session>
[^jwst-modes]: “JWST Instrument Modes in Jdaviz,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/index_jwst_modes.html>
[^jdaviz-citation]: “Citing Jdaviz,” *Jdaviz Documentation*. <https://jdaviz.readthedocs.io/en/latest/index_citation.html>
