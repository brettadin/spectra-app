# Repository Audit for Spectra‑App (fttr‑prediction branch)

This report inventories the current `spectra‑app` repository and summarises the state of its code base, highlighting high–level modules, noted redundancies and visible issues.  The analysis draws on both the GitHub tree and a brief code review.  Where relevant, requirements from the redesign brief are quoted directly for context.

## Inventory of Directories and Files

At the root of the repository there are approximately a dozen top‑level directories and numerous auxiliary files.  The major directories are:

| Directory | Purpose |
|---|---|
| `.devcontainer` and `.github` | Dev‑container configuration and CI workflows. |
| `RUN_CMDS` | Scripts for launching the Streamlit app in different contexts (e.g. local vs. build). |
| `app` | The main application package containing the Streamlit front‑end, backend services, ingestion and provider logic. |
| `data` | Reference spectra and other data assets used by the app. |
| `data_registry` | A YAML/JSON registry describing external data sources. |
| `docs` | Documentation and assorted notes (including a technote, patch log and agents history). |
| `ml` and `ml_models` | Early experiments with machine‑learning classifiers for identifying functional groups in spectra. |
| `scripts` | Helper scripts for converting data formats and generating manifests. |
| `tests` | Pytest‑based tests for specific modules. |
| `tools` | Packaging and build helpers. |

Alongside these directories are numerous text files: `CHANGELOG.md`, `PATCHLOG.txt`, `AI_PROTOCOL.txt`, `requirements.txt`, `targets.yaml`, etc.  Many of these capture the history of AI‑driven edits and patch applications.  The README on the `ftir‑prediction` branch is an informal personal note capturing the author’s reflections on the project’s evolution.

### Structure of the `app` Package

The `app` package contains the largest portion of code.  Its structure mirrors a traditional MVC separation:

- **`ui`**: Contains Streamlit front‑end components.  The entry point is `app/app_merged.py`, which logs errors and delegates rendering to `app.ui.entry.render()`.  From there, `app/ui/main.py` orchestrates the entire interactive page: page layout, sidebars, targets panel, overlay logic, differential operations, annotation panels, similarity calculations and export options.  The UI imports a mix of data‑processing functions from the server layer and utilities (e.g. down‑sampling, duplicate detection).  Several panels (similarity, IR group overlays, provider search) are dynamically registered via a panel registry.
- **`server`**: Back‑end services and mathematical operations.  For instance, `differential.py` exposes `resample_to_common_grid()`, `subtract()` and `ratio()` to align spectra on a common wavelength grid and compute differences or ratios with an epsilon term to prevent division by zero【948877707604069†L9-L32】.  `ir_units.py` defines an `IRMeta` dataclass and `to_A10()` conversion function that transforms transmittance, absorbance or absorption coefficient units into base‑10 absorbance (A₁₀) while tracking provenance【328409478188748†L0-L62】.
- **`ingest`**: Provides a simple `OverlayIngestResult` dataclass used by asynchronous upload jobs【563035467008438†L0-L15】.
- **`providers`** and **`server/fetchers`**: Modules that query external services such as the NIST IR Quantitative database and telescope archives.  These modules are thin wrappers around HTTP requests and return parsed results for ingestion.
- **`utils`**: Assorted helper functions: down‑sampling of large spectra (`downsample.py`), duplicate detection (`duplicate_ledger.py`), flux range calculation (`flux.py`), local file ingestion support (`local_ingest.py`), etc.  Many of these functions are reused across the UI.
- **`similarity`**: Implements vectorization and similarity metrics for comparing spectra; used by the similarity panel.
- **`continuity.py`**: Implements the self‑learning and continuity mechanism.  This module reads and writes notes in the `brains` and `atlas` folders, enabling the AI agent to persist context across sessions.
- **`export_manifest.py`**: Generates a manifest capturing the provenance of exported plots and data, including SHA‑256 checksums and metadata.
- **`version.json`**, **`_version.py`**: Keep version information and build dates for the version badge displayed in the UI【949348365484271†L14-L40】.

### Duplicate and Legacy Files

There are two near‑identical launchers (`app/app_merged.py` and `app/app_patched.py`), each wrapping Streamlit initialisation with error logging.  This duplication appears to stem from patching cycles.  Some modules also exist both under `app` and in `app/ui`; for example, an older `archive_ui.py` and `similarity_panel.py` remain even though the functionality has been integrated into `app/ui/main.py`.  These vestigial files contribute to clutter.

### Observed Issues and Pain Points

* **UI responsiveness and double‑click behaviour** – The Streamlit UI sometimes requires a double click on certain widgets (e.g. file uploaders and buttons) before updates propagate.  This appears to be a side effect of using Streamlit’s session state incorrectly (e.g. using local variables rather than `st.session_state`) and heavy reliance on `st.cache_data()`.  The brief explicitly notes that users often must double‑click UI elements for changes to take effect【875267955107972†L5-L9】.

* **Cluttered interface** – The current design places many controls on the sidebars and in the main area.  Panels such as overlay options, functional‑group predictions, similarity search, differential analysis and export controls coexist in a single page, making it overwhelming.  Labels can be long and the legend in the Plotly chart grows unwieldy as more traces are added.

* **Unit conversions and metadata handling** – Unit handling is spread across `ir_units.py`, `server/differential.py` and the UI.  Wavelength units (nm, μm, Å, cm⁻¹) are sometimes converted by directly multiplying arrays rather than re‑deriving from canonical values, leading to potential accumulation of rounding errors.  There is little centralised enforcement of canonical units or idempotent conversions.  The redesign brief demands that all values “be handled correctly” and displayed exactly as provided unless the user explicitly converts them【875267955107972†L29-L41】.

* **Redundant and legacy logic** – The presence of `app/app_merged.py` and `app/app_patched.py` plus multiple unused panels suggests that the code base has undergone many patch cycles without comprehensive refactoring.  Several functions appear to be copied between modules rather than imported from shared utilities, leading to inconsistency.

* **Patch and log naming inconsistencies** – The repository contains numerous patch logs and “brains/atlas” files with inconsistent naming.  Some logs are labelled with the day of the month rather than a proper date, making it difficult to trace the sequence of changes.  The redesign brief calls out this issue and asks for normalisation【875267955107972†L63-L74】.

* **Hidden dependencies** – The `requirements.txt` lists dozens of third‑party packages (Streamlit, Plotly, requests, numpy, pandas, etc.).  Some modules import packages (e.g. `requests`, `pytest`) without declaring them in the requirements.  A clean refactoring should unify dependency management and reduce unused libraries.

## Summary

The existing code base implements a feature‑rich Streamlit application for overlaying and analysing spectra from multiple sources.  However, it has accumulated significant technical debt: duplicated launchers, scattered unit conversions, inconsistent logging and a cluttered UI that can require double clicks.  The redesign should preserve the current capabilities while organising modules more coherently, centralising unit management, and replacing the Streamlit front‑end with a modern desktop UI.