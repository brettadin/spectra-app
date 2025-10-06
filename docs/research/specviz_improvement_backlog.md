# SpecViz-Inspired Improvement Backlog

## Purpose
- Translate SpecViz's mature 1D spectroscopy workflows into actionable upgrades for Spectra App so our roadmap targets proven interaction models and helper APIs. [1][2]
- Highlight near-term improvements that de-risk ingestion, visualization, and analysis parity while respecting Spectra App's Streamlit-first architecture. [1][3]

## Spectra ↔ SpecViz parity matrix

| Spectra feature area | SpecViz reference docs | Summary of current delta |
| --- | --- | --- |
| Ingestion workflows | [Importing data][import], [JWST mode matrix][jwst] | Spectra App lacks SpecViz's multi-entry loaders, auto-mode routing, and ingest helper diagnostics; roadmap items aim to align affordances and provenance handling. |
| Viewer interactions | [Displaying spectra][display] | The viewer currently provides Plotly-driven basics without SpecViz's layer list, toolbar breadth, or ROI/readout tooling, motivating the queued viewer upgrades. |
| Plugin & analysis suite | [Plugin catalog][plugins], [Helper APIs][helper] | Plugin coverage is limited to core Spectra features; SpecViz's modeling, smoothing, and export surfaces drive the plugin parity tranche and helper API expansion. |

> **Attribution.** SpecViz documentation excerpts and comparisons credit the [jdaviz authors](https://github.com/spacetelescope/jdaviz) who maintain the upstream guides and helper APIs that informed this matrix.

[import]: https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/import_data.rst
[jwst]: https://github.com/spacetelescope/jdaviz/blob/main/docs/index_jwst_modes.rst
[display]: https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/displaying.rst
[plugins]: https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
[helper]: https://github.com/spacetelescope/jdaviz/blob/main/jdaviz/configs/specviz/helper.py

## Ingestion Enhancements
1. **Adopt SpecViz loader affordances**
   - Offer separate UI affordances for single-file, directory, and helper-driven loads mirroring SpecViz's CLI/UI/API entry points so observers can stage whole programs quickly. [1]
   - Provide load options (`concat_by_file`, `stash_in_catalog`, remote URI fetch) exposed both in the sidebar and helper API, keeping ingestion reproducible. [1][3]
2. **Specutils-native payload contracts**
   - Normalize all internal ingestion outputs to `Spectrum1D`/`SpectrumList` containers and surface coercion errors clearly, leveraging SpecViz's helper validations as guidance. [1][3]
   - When ingestion fails, capture the offending header/column diagnostics in provenance (similar to SpecViz's toast + helper exceptions) so analysts can remediate upstream files. [1]
3. **Mode-aware routing**
   - Detect JWST mode/product mismatches during ingest (e.g., MIRI MRS cubes) and steer users toward alternative workspaces before rendering errors propagate, following SpecViz's mode matrix. [4]
   - Persist accepted/rejected mode decisions in provenance to reinforce reproducibility when sharing sessions. [4]

## Viewer & Interaction Upgrades
1. **Layer-aware viewer controls**
   - Mirror SpecViz's layer list with per-trace visibility, styling, and unlink actions to reduce reliance on sidebar toggles. [2]
   - Introduce hover/cursor readouts and ROI subset tools that sync with exported metadata, honoring SpecViz's glue-backed interactions. [2]
2. **Toolbar modernization**
   - Expand the toolbar with reset, autoscale, zoom box, and pan controls plus keyboard shortcuts, matching SpecViz's Matplotlib/Glue toolset to quicken exploratory analysis. [2]
   - Provide helper endpoints (`set_limits`, `link_limits`) so notebooks and regression fixtures can assert viewer state deterministically. [3]
3. **Unit conversion & scaling**
   - Embed a unit conversion widget that propagates axis and flux unit changes across visible traces without mutating source data, borrowing SpecViz's plugin UX. [5]
   - Cache user-selected unit preferences per session and expose them through our helper API so automation runs can align outputs. [3][5]

## Analysis & Plugin Parity
1. **Core plugin tranche**
   - Prioritize Gaussian smoothing, line list management, and redshift slider plugins that deliver immediate science value and mirror SpecViz's defaults. [5]
   - Ensure each plugin registers derived layers/data tables with provenance hooks so export manifests stay audit-ready. [5]
2. **Model fitting workflow**
   - Provide a component builder similar to SpecViz's model fitting plugin: selectable Astropy models, editable initial guesses, and fit diagnostics exported alongside plots. [5]
   - Integrate helper calls to rerun fits programmatically, enabling regression tests to replay scenarios without UI driving. [3]
3. **Export surfaces**
   - Replicate SpecViz's export plugin paths (spectrum subsets, region definitions, viewer captures) and tie them to Spectra App's existing manifest schema. [1][5]
   - Document the export behaviors with parity tables so operations knows which artefacts match SpecViz outputs and where divergences remain. [5]

## Collaboration & Automation
1. **Helper API coverage**
   - Publish a `spectra.helpers.SpecvizCompat` module that wraps ingestion, viewer state, plugin triggers, and export retrieval mirroring SpecViz helper signatures for low-friction migration. [3]
   - Log helper calls into provenance (similar to SpecViz's hub events) so shared sessions reveal the scripted steps behind derived products. [3]
2. **Test & contract extensions**
   - Expand regression suites to capture viewer state (limits, subsets) and plugin outputs, using SpecViz tutorial scenarios as fixtures to ensure parity. [2][5]
   - Update the UI contract to enumerate toolbar expectations, layer list controls, and plugin affordances before implementing UI changes, minimizing regressions. [2]
3. **Documentation alignment**
   - Mirror SpecViz's documentation structure—importing data, displaying spectra, plugin guides, API usage—and link Spectra App equivalents so users recognize familiar workflows. [1][2][3][5]
   - Add citation guidance referencing Spectra App's Zenodo/DOI once available, following SpecViz's approach to crediting software releases. [6]

---

**References**
1. SpecViz data ingestion documentation — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/import_data.rst
2. SpecViz display interactions — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/displaying.rst
3. SpecViz helper implementation — https://github.com/spacetelescope/jdaviz/blob/main/jdaviz/configs/specviz/helper.py
4. JWST mode support matrix — https://github.com/spacetelescope/jdaviz/blob/main/docs/index_jwst_modes.rst
5. SpecViz plugin catalog — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
6. SpecViz citation guidance — https://github.com/spacetelescope/jdaviz/blob/main/docs/index_citation.rst
