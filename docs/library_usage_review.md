# Review of Library Usage in Spectra App

Executive summary

The spectra-app repository provides a Streamlit front-end for interactive exploration of example spectra and includes an ingestion engine that can parse local ASCII tables and FITS files as well as fetch curated data from external archives. The project relies on Streamlit, Plotly, NumPy, pandas, Astropy, astroquery, requests, PyVO, PyYAML and Rich. This report reviews how these libraries are used, identifies areas where they are used well, highlights misuses or inefficiencies and suggests alternatives or improvements. Official documentation is cited to anchor recommendations.

The table below lists the key dependencies and their official documentation sources. Each section following the table discusses how the library is currently used, whether it is being leveraged effectively, and recommendations to improve reliability, performance and maintainability.

| Library | Official documentation (primary source) |
| --- | --- |
| Streamlit | docs.streamlit.io |
| Plotly (Python graphing library) | plotly.com/python |
| NumPy | numpy.org |
| pandas | pandas.pydata.org |
| Astropy | astropy.org |
| astroquery | astroquery.readthedocs.io |
| requests | requests.readthedocs.io |
| PyVO | pyvo.readthedocs.io |
| PyYAML | pyyaml.org |
| Rich | rich.readthedocs.io |

---

## Streamlit

**Current usage:** The UI code (`app/app_merged.py` and `app/ui/example_browser.py`) uses Streamlit to render pages, accept user input and show Plotly graphs. It uses containers, columns, interactive widgets and session state to manage example selection. A render function wraps UI code in a try/except to capture exceptions and display them in a Streamlit error component.

**Strengths:**

- Streamlit allows the team to prototype interactive front-ends quickly. Its markdown support and simple widget API make the example browser easy to implement.
- The UI code uses dynamic lists of examples and provider filters; it updates UI state without requiring page reloads.
- Recent hotfix ensures provider multiselect state in the example browser persists via `st.session_state` without triggering widget key warnings.

**Issues:**

- **No caching:** Streamlit provides `st.cache_data` and `st.cache_resource` to memoize expensive data-fetching or computation functions.[^1] The current code repeatedly downloads remote spectra, parses FITS files and performs heavy NumPy operations every time the user selects an example. This leads to slow page loads and unnecessary network traffic.
- **Blocking network calls in UI thread:** Remote data are fetched synchronously inside Streamlit callbacks, blocking the UI while requests complete. Streamlit supports asynchronous functions (Python ≥3.11) or off-thread work, which can keep the UI responsive.
- **Limited use of built-in components:** The app manually builds search fields, filters and lists of examples. Streamlit’s `st.dataframe`, `st.selectbox` and `st.table` might simplify some of these tasks and provide built-in sorting/filtering.

**Recommendations:**

- Use `@st.cache_data` to wrap functions that download or parse data (e.g., NIST queries, SDSS/MAST downloads, FITS parsing) so that results are cached by input parameters, as recommended by the docs.[^1]
- Employ asynchronous calls or background threads (via `asyncio` or `concurrent.futures`) for network requests to avoid blocking the UI.
- Leverage Streamlit session state to persist loaded spectra and avoid repeated network calls when navigating between examples.
- Consider `streamlit-aggrid` or `st.data_editor` for interactive tables instead of manual column and search logic.

## Plotly

**Current usage:** The UI uses `plotly.graph_objects` to create sparklines for each example spectrum. When a user loads a spectrum, the full interactive plot is rendered using Plotly in the example viewer (not shown in this file but likely in `app/ui/main.py`).

**Strengths:**

- Plotly is a flexible, interactive graphing library that produces publication-quality charts.[^2] The code correctly uses `go.Figure` and `go.Scatter` to create line plots and adjusts axes and margins for sparklines.
- Plotly integrates well with Streamlit via `st.plotly_chart`.

**Issues:**

- **Not using Plotly Express:** Many simple line or scatter plots could be defined with Plotly Express (`px`), which requires less boilerplate and automatically sets axis titles and legend.
- **No performance optimisation for large datasets:** Some spectra may contain hundreds of thousands of points (event bins). Plotly rendering can become sluggish. Using `scattergl` or down-sampling before plotting may improve responsiveness.
- **No offline caching:** Each time a plot is generated, Plotly re-computes the figure. Caching the figure creation or down-sampled data would improve performance.

**Recommendations:**

- Use `plotly.express` for common plot types to simplify code and automatically handle labels.
- Down-sample dense spectra for plotting (e.g., using decimation or `hvplot`/Bokeh) and provide a toggle for high-resolution data.
- Explore Plotly’s `FigureWidget` for dynamic updates without re-plotting entire figures.

## NumPy

**Current usage:** NumPy is heavily used in ingestion modules (`ingest_fits.py`, `ingest_ascii.py`) and fetchers to manipulate arrays. Operations include normalising flux arrays, computing histograms for event data, and converting wavelengths.

**Strengths:**

- NumPy provides efficient array operations and broadcasting; the code uses `numpy.asarray`, `numpy.clip`, `numpy.mean`, etc., effectively.
- Vectorised operations are used in parts of `example_browser.py` to normalise flux for sparklines.

**Issues:**

- **Unnecessary Python loops:** `ingest_fits.py` manually bins event data via loops instead of using `numpy.histogram` or `numpy.bincount`. This is inefficient and error-prone.
- **Redundant type conversions:** The code repeatedly casts arrays to Python lists or calls `.tolist()`, which defeats the performance benefits of NumPy and complicates unit handling.
- **Manual flattening:** Some functions flatten multi-dimensional data via custom code instead of using `numpy.ravel` or `numpy.flatten`.

**Recommendations:**

- Replace manual binning and histogram logic with `numpy.histogram` or `numpy.bincount`.
- Keep data in NumPy arrays until final conversion for JSON output; avoid converting back and forth between lists and arrays.
- Use `numpy.vectorize` or broadcasting to eliminate slow Python loops.
- Use `numpy.memmap` for reading large FITS files; `astropy.io.fits` supports memory mapping (via `memmap=True`),[^3] which prevents loading the whole file into memory.

## pandas

**Current usage:** pandas is used in `tools/build_registry.py` to assemble star catalogs and export CSV files. In ingestion code for ASCII files, raw CSV data are read into pandas DataFrames for initial parsing, then converted to lists for output.

**Strengths:**

- pandas is a powerful data manipulation library.[^4] The code uses `pandas.read_csv`, `.rename`, `.astype`, `.sort_values` and DataFrame operations effectively.
- DataFrames are converted to dictionaries for JSON output; tests ensure correct columns are selected.

**Issues:**

- **Conversion overhead:** Converting DataFrames to lists and dictionaries repeatedly can be expensive. Many operations could be done directly on DataFrames and only converted at the end.
- **Not using `pandas.Series.astype` correctly:** Some code calls `.astype(object)` to circumvent missing values; better to use pandas’ built-in `.fillna` and numeric dtypes.
- **No type hints or docstrings:** Functions lack explicit docstrings and type hints, making it harder to understand DataFrame shapes and return types.

**Recommendations:**

- Perform filtering and unit conversions inside DataFrames; avoid converting to lists until needed for JSON payloads.
- Use `pandas.to_datetime` and `.dt` accessors for date manipulation rather than manual string operations.
- Consider using `xarray` for multi-dimensional spectral cubes if future features expand beyond 1-D spectra.

## Astropy

Astropy is a comprehensive package for astronomy; it provides modules for reading/writing FITS files, working with units, coordinates, time, and more.[^5] The repository uses two main parts: `astropy.io.fits` and `astropy.units`.

### FITS handling

**Current usage:** `app/server/ingest_fits.py` defines a complex FITS ingestion pipeline. It opens FITS files using `fits.open()`, then loops through HDUs to identify the primary data HDU. It manually interprets WCS keywords (`CRPIX1`, `CRVAL1`, `CDELT1`, etc.), computes wavelength arrays, normalises flux units, bins event lists, and collects metadata.

**Issues:**

1. **Reinventing functionality:** Astropy’s FITS I/O module already supports reading FITS tables and images and exposes header information. The `astropy.io.fits` docs recommend using the high-level I/O interface `Table.read()` and `hdu.data` rather than manual parsing.[^6] Many unit conversions implemented in `ingest_fits.py` could be replaced with Astropy’s `SpectralCoord`, `SpectralAxis` (in specutils), or WCS utilities.
2. **No use of `astropy.wcs.WCS`:** Converting pixel coordinates to world coordinates is done manually. Astropy’s `WCS` object can compute wavelength axes properly and handle more complicated cases (non-linear dispersion, binning).
3. **Discarding units:** FITS columns with units are converted to plain NumPy arrays and then cast to lists, losing physical units. Astropy’s `Quantity` should be used to attach units and convert them safely.[^7] `QTable` or `Table` can store units for each column.
4. **Error-prone heuristics:** The code tries to infer units from header keywords or column names using string matching. Astropy’s unit parsing (`u.Unit(header_unit)`) is more robust and avoids custom heuristics.
5. **Not reading binary tables via `Table.read`:** Instead of manually iterating through columns, `Table.read` (or `fits.getdata`) would return an Astropy Table with column names and units already parsed.
6. **Missing `memmap` option:** Opening large FITS files without `memmap=True` can consume a lot of memory.[^3]

### Unit handling

**Current usage:** The code imports `astropy.units as u` in some modules and uses `u.Unit` or manual multipliers to normalise wavelengths and flux. For example, NIST fetcher uses `_unit_to_nm_scale` to convert cm-1 to nm.

**Issues:**

- **Manual conversions:** Many functions manually convert units (e.g., dividing by 10 to convert Å to nm) instead of using `Quantity.to()`. This risks mistakes and does not record the conversion history.
- **Loss of units:** Data are returned as plain floats, so downstream functions cannot automatically combine or re-scale them.

**Recommendations:**

- Use `astropy.table.Table.read()` or `astropy.table.QTable` to load FITS tables; columns will be `Quantity` objects with units, and conversion to nm can be done via `.to(u.nm)`.
- Use `astropy.wcs.WCS` to compute wavelength axes for images and `astropy.nddata.CCDData` to wrap image data with WCS and units.
- Explore the `specutils` package (an Astropy-affiliated package) which provides `Spectrum1D` objects representing spectral data with wavelength, flux and metadata; it includes `SpectralAxis` for WCS transformations and built-in unit conversions.
- Use `memmap=True` when opening FITS files to avoid loading entire files into memory.[^3]
- Use `try`/`except` around `fits.open` to capture I/O errors and report user-friendly messages.

## astroquery

Astroquery provides a common interface to query remote astronomical archives and services.[^8] Modules like `astroquery.nist`, `astroquery.sdss` and `astroquery.mast` wrap HTTP requests and return Astropy Tables. The code uses astroquery in some places but not others:

**Current usage:**

- In `fetchers/nist.py`, the `astroquery.nist.Nist` service is used to query the NIST Atomic Spectra Database. The result is an Astropy Table. The code then manually infers the unit scale, converts wavelengths to nm and intensities to relative units.
- `tools/build_registry.py` uses `astroquery.simbad.Simbad` to query star metadata and `astroquery.mast.Observations` to query observations. It also optionally uses `astroquery.eso.Eso` for ESO Phase-3 products.

**Issues:**

- **Under-utilisation:** For other data sources (e.g., curated SDSS spectra, Zenodo DOIs, X-Shooter FITS), the code uses `requests` to download FITS files directly instead of available astroquery modules. For example, `astroquery.sdss.SDSS` can fetch SDSS spectra with built-in caching, but `app/server/fetchers/sdss.py` hard-codes download URLs and uses `requests`. `astroquery.mast` could also download CALSPEC or JWST spectra with proper authentication and caching.
- **Manual unit handling:** Even when using astroquery, the code converts units manually rather than using `astropy.units` or working with the returned Table.
- **Lack of caching:** Astroquery automatically caches downloaded files in a local directory. By using direct `requests`, the code loses this feature and re-downloads the same file on every call.

**Recommendations:**

- Replace manual `requests` calls in fetchers with appropriate astroquery modules:
  - Use `astroquery.sdss.SDSS` to fetch SDSS spectra; it can retrieve spectra by plate, MJD, fiber or object ID and returns an Astropy Spectrum.
  - Use `astroquery.mast` functions like `Observations.download_products` to fetch CALSPEC spectra; this will also provide metadata about the files.
  - Use `astroquery.eso` for ESO spectra.
  - For DOIs and Zenodo, `astroquery.esa.iso` or `astroquery.utils.tap.TAPService` could query the Zenodo API more robustly.
- When using astroquery, operate on the returned Astropy Table with units and convert to nm using `.to(u.nm)` rather than manual scaling.
- Configure astroquery’s cache directory to persist downloaded files between sessions.

## requests

`requests` is an HTTP library built for human beings.[^9] It provides features like connection pooling, streaming downloads and timeouts.

**Current usage:** Many fetchers directly call `requests.get` to download FITS files from remote servers (e.g., Zenodo, ESO, MAST).

**Issues:**

- **No timeout specification:** Several calls to `requests.get` lack explicit timeouts (e.g., `fetchers/doi.py`, `fetchers/eso.py`, `fetchers/mast.py`). According to requests documentation, specifying a timeout is essential to avoid hanging on slow or unresponsive connections.[^9]
- **No retry or session reuse:** Creating a new connection for each request is inefficient; using a `requests.Session` or leveraging astroquery’s session management would enable connection pooling.
- **Bypassing astroquery caching:** As noted above, manual requests calls mean the application must implement its own caching and error handling.

**Recommendations:**

- Whenever using `requests`, always specify a timeout (e.g., `requests.get(url, timeout=30)`).[^9]
- Use `requests.Session` to reuse TCP connections and set default headers and timeouts.
- Consider using `requests-cache` to persist responses across sessions and avoid repeatedly downloading the same files.
- For astronomy archives, prefer astroquery modules over raw HTTP where possible.

## PyVO

`pyvo` is an Astropy-affiliated package that implements the International Virtual Observatory Alliance (IVOA) protocols (TAP, SIA, SSA, SCS, SLAP) and allows querying remote services in a uniform manner.[^10] In `tools/build_registry.py`, PyVO is optionally used to query the CARMENES DR1 dataset using an SCS service.

**Strengths:**

- When enabled, PyVO is used appropriately to query CARMENES DR1. It returns a VOTable which is converted to an Astropy Table.

**Issues:**

- PyVO is optional and only used for CARMENES; other services like VizieR or Simbad could also be accessed via PyVO for uniformity.
- Error handling is minimal; if PyVO is unavailable, the code silently skips CARMENES.

**Recommendations:**

- Expand PyVO usage to other services such as VizieR, MAST and ESO to unify VO protocol access.
- Wrap PyVO queries in `try`/`except` blocks that provide user-friendly error messages when services are unavailable.

## PyYAML

PyYAML provides a safe YAML parser for Python. It is used only in `build_registry.py` to load a roster file (`yaml.safe_load(Path(args.roster).read_text())`). This is appropriate; `safe_load` prevents execution of arbitrary tags and is recommended for untrusted input.

**Recommendation:** If YAML configuration files become more complex, consider using `dataclass` or `pydantic` models to validate the structure of the parsed YAML.

## Rich

Rich is a library for rendering rich text in the terminal with colours and formatting. It appears in the dependency list but is not used anywhere in the code.

**Recommendation:** If the project includes command-line tools (such as `build_registry.py`), consider using Rich to improve console output, display progress bars for downloads, and highlight warnings or errors. Otherwise, remove Rich from `requirements.txt` to reduce dependencies.

---

## General suggestions for improving reliability and reproducibility

1. Use Astropy and specutils abstractions: Adopt `astropy.table.QTable` and `specutils.Spectrum1D` for handling spectral data. These classes automatically preserve units, provide WCS transformations, and integrate with spectral-cube and pyspeckit. This will reduce the amount of custom code in `ingest_fits.py` and improve correctness.
2. Consolidate fetchers and use astroquery: Convert the multiple fetcher modules (`nist.py`, `doi.py`, `eso.py`, `sdss.py`, `mast.py`) into a unified interface that uses astroquery modules for the respective archives. This will provide built-in caching, consistent error handling and reduce code duplication.
3. Implement robust caching: Use Streamlit’s caching (`st.cache_data`) and astroquery’s local cache for remote data. For local ingestion, implement a file-level cache keyed by file contents (e.g., using a hash) so that the same FITS or ASCII file is not parsed repeatedly.
4. Add type hints and docstrings: Many functions lack type annotations and docstrings. Adding them will improve readability and enable static analysis tools.
5. Improve error handling and logging: Use logging to record warnings and errors. Provide user-friendly messages in the UI when an error occurs rather than silent failures. Consider using the Rich library to print colourful logs when running command-line scripts.
6. Optimise performance for large datasets: For event tables and high-resolution spectra, implement down-sampling (e.g., by computing median flux in bins using NumPy) for plotting. Use memory mapping (`memmap=True`) when opening large FITS files to reduce memory use.
7. Automate tests for ingestion edge cases: The existing tests cover many ingestion scenarios. Extend them to include invalid WCS, missing units, and extremely large files to catch regressions early.
8. Documentation: Provide user documentation for how to add new fetchers or support additional data formats. Include guidelines on writing YAML rosters and using the build registry.
9. Consider using Dask or AsyncIO for concurrency: Downloading multiple remote files can be slow; using Dask or asynchronous functions to parallelise downloads will improve responsiveness and make better use of network resources.
10. Review dependency list: Remove unused dependencies (e.g., Rich) and specify compatible version ranges in `requirements.txt`. Keeping dependencies minimal simplifies maintenance and reduces vulnerability surface.

---

## Conclusion

`spectra-app` showcases an ambitious attempt to build a unified platform for ingesting and exploring astronomical spectra. It leverages powerful libraries such as Streamlit, Plotly, NumPy, pandas, Astropy and astroquery. However, the current implementation often re-implements functionality already available in Astropy and astroquery, leading to complex code paths, manual unit handling and potential errors. By embracing the high-level abstractions provided by these libraries, introducing caching and asynchronous operations, and consolidating data fetchers, the application can become more reliable, easier to maintain and more performant. Integrating specutils for spectral data representation and making greater use of astroquery’s modules will streamline the codebase and align it with community best practices in astronomical data analysis.

---

[^1]: [st.cache_data - Streamlit Docs](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
[^2]: [Plotly Python Graphing Library](https://plotly.com/python/)
[^3]: [FITS File Handling (astropy.io.fits) — Astropy v7.2.dev587+gbf64e58a1](https://docs.astropy.org/en/latest/io/fits/index.html)
[^4]: [pandas - Python Data Analysis Library](https://pandas.pydata.org/)
[^5]: [Astropy](https://www.astropy.org/)
[^6]: [FITS File Handling (astropy.io.fits) — Astropy v7.2.dev587+gbf64e58a1](https://docs.astropy.org/en/latest/io/fits/index.html)
[^7]: [Units and Quantities (astropy.units) — Astropy v7.1.0](https://docs.astropy.org/en/stable/units/index.html)
[^8]: [Astroquery — astroquery v0.4.12.dev230](https://astroquery.readthedocs.io/en/latest/)
[^9]: [Requests: HTTP for Humans™ — Requests 2.32.5 documentation](https://requests.readthedocs.io/en/latest/)
[^10]: [PyVO — pyvo v1.8.dev34+g5f1e0ed97](https://pyvo.readthedocs.io/en/latest/)
