# Bugs and UX Issues Identified

This document compiles notable defects and usability problems in the current Spectra‑App.  Issues were identified through examination of the source code, inspection of logs, and reproduction in the Streamlit UI.  Each entry includes reproduction steps and a recommended remediation strategy.  Where relevant, the redesign brief is referenced for context.

## 1. Double‑Click Requirement on UI Elements

**Symptoms:** Users often need to double‑click buttons, dropdowns or file uploaders before the UI updates.  For example, uploading a local CSV may not trigger the ingest until the file is selected twice.  Similarly, toggling the unit conversion radio buttons sometimes has no effect until clicked again.

**Cause:**  Streamlit widgets update session state only when their return value changes.  In several places, the code assigns widget outputs to local variables and uses them directly without storing them in `st.session_state`.  When subsequent code runs within the same execution cycle, the state may not yet be updated, leading to inconsistent reactions.  Additionally, repeated use of `@st.cache_data` around functions that depend on mutable objects may cause stale values to persist.

**Reproduction:**
1. Launch the existing Streamlit app via `streamlit run app/app_merged.py`.
2. In the sidebar, click the **Local Upload** widget and select a CSV file.  Observe that nothing appears.  Click again to select the same file; only then does the overlay appear.
3. Repeat with other widgets (e.g. unit toggles or filter sliders) and notice inconsistent updates.

**Remediation:** Adopt a reactive UI framework (e.g. Qt or Tauri) where state changes are explicit.  When using Streamlit, always persist widget outputs in `st.session_state` and avoid caching functions that depend on stateful objects.  Replace custom double‑click detection with proper event handlers.

## 2. Cluttered and Unintuitive Layout

**Symptoms:** The main page features sidebars overflowing with options: ingest sources, similarity search, differential operations, functional‑group overlays and export options.  The central plot area’s legend grows with each overlay, making it difficult to distinguish traces.  Some labels are truncated or duplicated (e.g. “Sun (2)” appears even when the spectrum was ingested once).  As the brief states, the current interface “feels cluttered with overlapping controls”【875267955107972†L5-L9】.

**Cause:**  The existing UI uses a single Streamlit page to host multiple panels.  Without navigation hierarchy or tabbed views, all controls are rendered simultaneously.  Duplicate labels stem from the duplicate ledger miscounting overlays when a file is re‑ingested after a failed attempt.

**Remediation:** Design a multi‑tab desktop interface with clear separation: a dedicated **Data** tab for ingestion and units, a **Compare** tab for overlay and differential operations, a **Functional Groups** tab for predictions, a **Similarity** tab and a **Logs/History** tab.  Use collapsible panels and responsive grids.  Consolidate legend entries by computing a stable fingerprint for each spectrum and using it as a key in the duplicate ledger.

## 3. Unit Conversion Errors and Mutable Data

**Symptoms:** Switching units (e.g. from nm to µm to cm⁻¹) sometimes yields different values depending on the order of conversions.  Dividing spectra with nearly zero denominators produces spikes rather than masked values.  Subtracting a spectrum from itself yields a non‑zero trace due to floating‑point errors.  These behaviours violate the requirement that data should “never be altered unintentionally” and conversions must be “100 % accurate”【875267955107972†L29-L45】.

**Cause:**  Conversions are often applied by directly multiplying the wavelength or flux arrays and storing the result back into the original object.  Because subsequent conversions operate on the already‑converted values, rounding error accumulates.  The ratio function (`server/differential.py`) adds an epsilon to the denominator but does not mask points where the denominator is effectively zero, leading to large spikes.  Subtraction uses `np.array(a) - np.array(b)` which may not cancel exactly due to float precision.

**Remediation:** Maintain canonical internal units: store wavelengths internally in nm and derive Å, µm and cm⁻¹ only for display.  Always recompute derived values from the canonical array rather than chaining conversions.  In ratio calculations, mask points where the denominator’s magnitude falls below a threshold and display a warning; use an epsilon only as a fallback.  Suppress trivial results when subtracting identical spectra and display an informational toast.

## 4. Inconsistent Patch Naming and Log Dates

**Symptoms:** The `PATCHLOG.txt`, `brains/` and `atlas/` directories contain entries where the patch name does not correspond to the actual date of the work.  For example, an update applied on 10 May appears as “05.txt” and is interleaved with work from different days.  Some logs are labelled only by the day of the month without the month or year, making chronology ambiguous【875267955107972†L63-L74】.

**Remediation:** Establish a standard naming convention: `YYYY-MM-DD_description.md` for patches and knowledge logs.  Use ISO‑8601 timestamps within the files.  Write a normalisation script to traverse existing logs, extract date information from headers, and rename files accordingly.  Append a header to each normalised file indicating the original filename for traceability.

## 5. Hidden and Broken Dependencies

**Symptoms:** Some modules import libraries that are not listed in `requirements.txt` (e.g. `python-docx` for reading `.docx` patch notes).  Others rely on external services (NIST API, telescope archives) without clearly specifying endpoints or API keys.  When run in a fresh environment, the app may fail due to missing packages or network access.

**Remediation:** Audit all imports and update `requirements.txt` accordingly.  Provide stubs or mocks for remote services in the test suite.  Document all external dependencies and their licences.  For the standalone desktop version, consider bundling small datasets locally to reduce reliance on network calls.

## 6. Lack of Modular Boundaries

**Symptoms:** Business logic (e.g. differential operations, unit conversions, ML predictions) is interwoven with UI code.  Functions in `app/ui/main.py` make HTTP requests, perform numerical operations and update session state.  This tight coupling makes it hard to test modules independently and replace the front‑end without rewriting the backend.

**Remediation:** Separate concerns into distinct layers: a **data layer** for reading and converting spectra; a **service layer** for transformations, ML predictions and similarity calculations; and a **presentation layer** for the UI.  Define clear interfaces between layers.  Use dependency inversion to allow the UI to call into services via well‑defined APIs.