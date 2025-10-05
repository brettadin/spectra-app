# SpecViz Adaptation Blueprint

## 1. Why SpecViz matters
- **Purpose-fit for 1D spectra** – SpecViz focuses on rapid visual inspection and quick-look analysis of single-spectrum and stacked-spectrum data, pairing flexible plotting with specutils-powered analysis. [1]
- **Jupyter-native but API-driven** – every GUI capability has a parallel helper API so notebooks and automations can drive the tool. [2][3]
- **Glue-based data backbone** – the viewer stack relies on glue for data/link management, enabling layered plots, subsets, and cross-plugin synchronization. [4]
- **JWST-aligned data products** – official support spans JWST NIRSpec/NIRISS/NIRCam/MIRI Level 2b/3 products, giving us authoritative ingestion rules for space-telescope archives. [5]

## 2. Data ingestion patterns to adopt
1. **Standardize on specutils containers**
   - Accept `Spectrum`, `SpectrumList`, and stitched concatenations as first-class inputs so science packages dictate IO rules instead of bespoke loaders. [1]
   - Preserve JWST `datamodels` compatibility by translating tables into Spectrum objects while we wait on upstream decoupling. [1]
2. **Multiple entry points**
   - Mirror SpecViz’s CLI (`jdaviz --layout=specviz ...`), GUI “Import Data,” and helper-based `load_data` pathways to serve both UI and programmatic users. [1]
   - Allow directory ingestion plus toggles like `concat_by_file`, `load_as_list`, caching hints, and remote URI fetch support to smooth large observing programs. [1]
3. **Import UX**
   - Surface notifications for success/failure, auto-register new datasets into per-viewer data menus, and respect cached/remote provenance for auditability. [1]

## 3. Display and interaction capabilities to emulate
- **Layer control menus** with visibility toggles, remove/re-add actions, and plugin data-source filtering tied to the viewer legend. [4]
- **Cursor readouts** pinned to the toolbar that can lock to specific layers, giving immediate wavelength/flux feedback. [4]
- **Rich zoom & pan toolkit** covering home/reset, box/x-range zoom, scroll-wheel pan/zoom, and axis-flip/autoscale shortcuts (all available through the API). [4]
- **Spectral region tools** that create subsets, synchronize colors/labels, and expose helper methods to define ROIs programmatically. [4]
- **Plot option controls** for per-layer color/opacity/line style, uncertainty overlays, and API hooks to script those changes. [4]

## 4. Analysis plugin suite inspiration
1. **Gaussian Smooth** – generate smoothed spectra as new layers with configurable kernel width. [6]
2. **Model Fitting** – build labeled Astropy model components, edit initial guesses, compose equations, pick fitters, and capture parameter tables (with export hooks). [6]
3. **Unit Conversion** – centralize spectral axis and flux unit toggles that ripple across viewers/plugins without mutating source data. [6]
4. **Line Lists & Redshift slider** – manage curated/custom line catalogs, color controls, global show/hide, plus an interactive slider that offsets all lines and feeds helper outputs. [6]
5. **Line Analysis** – tie subset selections to specutils analysis (centroid, FWHM, flux, EW) with continuum windows and API access. [6]
6. **Export plugin** – capture viewer screenshots and region definitions (FITS/REG/ECSV) directly from the UI. [6]

## 5. Helper/API behaviors worth porting
- `Specviz.load_data(...)` handles file paths, Spectrum objects, SpectrumList concatenation, caching hints, and ensures unique labels across viewers. [7]
- `Specviz.get_spectra(...)` returns dictionaries keyed by layer, applies optional redshift slider offsets, and respects subsets. [7]
- `Specviz.get_spectral_regions(...)` (deprecated in favor of subset tools) highlights the need for typed region exports with unit conversion options. [7]
- Axis utility helpers (`set_limits`, `reset_limits`, `set_tick_format`) demonstrate how scriptable viewer state should behave even as GUI controls evolve. [7]
- Internally the helper listens for hub messages (e.g., `RedshiftMessage`) to synchronize sliders and exported spectra—our architecture should expose a comparable event bus so UI widgets and data operations stay decoupled. [7]

## 6. JWST mode alignment
- Adopt SpecViz’s mode-to-configuration matrix (e.g., NIRSpec X1D → SpecViz, MIRI S3D → Cubeviz) as acceptance criteria for archive products, ensuring we warn users when a file demands a different workspace. [5]
- Encode pipeline-level expectations (Level 2b/3 vs unsupported INT products) to guard ingestion and steer users toward supported reductions. [5]

## 7. Implementation roadmap for Spectra App
1. **Foundation (Sprint 1)**
   - Map our existing ingestion stack to specutils containers; add adapters for Spectrum/SpectrumList and JWST datamodel translation.
   - Introduce a viewer data registry mirroring SpecViz’s layer menus, including success/error toasts on import.
2. **Viewer parity (Sprint 2)**
   - Implement cursor readouts, pan/zoom toolkit, and spectral subset creation in our Streamlit UI (respecting UI contract) while exposing equivalent API hooks.
   - Build plot styling controls with persistence, ensuring unit conversion stubs exist even if backend conversion is deferred.
3. **Plugin phase (Sprints 3-4)**
   - Port Gaussian smoothing and unit conversion (leveraging specutils/astropy) as first analysis plugins.
   - Scaffold plugin tray architecture, dataset dropdown wiring, and plugin-to-viewer data publication semantics akin to SpecViz.
   - Design plugin result export surfaces (tables, derived spectra) and align with our provenance manifest.
4. **Advanced analysis (Sprints 5-6)**
   - Implement line list management and redshift slider with asynchronous performance guards.
   - Add line analysis + model fitting, reusing astropy models/fitting and ensuring parameter tables export via our existing export manifest pipeline.
5. **Interoperability & archives (Sprint 7+)**
   - Integrate remote archive loaders (MAST/JWST) that deliver Spectrum/SpectrumList payloads and register provenance.
   - Encode JWST mode compatibility checks with user messaging and routing to alternate workspaces when required.
6. **Automation & testing**
   - Mirror helper behaviors with a Python API layer so tests (and power users) can script data loads, viewer changes, and plugin invocations.
   - Expand regression coverage to include viewer state (zoom, subsets) and plugin outputs, using fixtures modeled after SpecViz tutorials.

## 8. Documentation & product alignment
- Maintain parity docs: create import, display, plugin, and export guides for Spectra App mirroring SpecViz sections to onboard users.
- Establish citation guidance similar to SpecViz’s Zenodo record so downstream researchers can reference our tool properly. [8]
- Track instrumentation compatibility and supported pipelines in a living document (mirroring SpecViz’s JWST mode table) so science teams know what to expect. [5]

## 9. Open questions for discovery
- How do we adapt glue’s event-driven model inside Streamlit? Evaluate lightweight message bus implementations or embedding glue as a backend service.
- What performance budget do we need to keep redshift sliders and heavy line lists responsive in a web-deployed environment?
- Which SpecViz plugins map cleanly to our product vision, and which require rethinking (e.g., 2D viewers, MOS pipelines)?
- How will we expose notebook-friendly helper APIs while maintaining a hosted Streamlit front end—do we bundle a Python SDK or rely on REST endpoints?

---

**References**
1. SpecViz data ingestion documentation — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/import_data.rst
2. SpecViz overview — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/index.rst
3. SpecViz exporting data and API usage — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/export_data.rst
4. SpecViz display interactions — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/displaying.rst
5. JWST mode support matrix — https://github.com/spacetelescope/jdaviz/blob/main/docs/index_jwst_modes.rst
6. SpecViz plugin catalog — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
7. SpecViz helper implementation — https://github.com/spacetelescope/jdaviz/blob/main/jdaviz/configs/specviz/helper.py
8. SpecViz citation guidance — https://github.com/spacetelescope/jdaviz/blob/main/docs/index_citation.rst
