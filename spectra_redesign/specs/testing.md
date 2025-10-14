# Testing Strategy

A comprehensive testing strategy is essential to ensure that the redesigned Spectra‑App is robust, reliable and accurate.  The following plan covers unit tests, integration tests, golden‑image tests, performance checks and continuous integration.

## 1. Unit Tests

Unit tests validate individual functions and classes in isolation.  They reside in the `tests/` directory and are executed with `pytest`.

### 1.1 Units Service

* **Round‑trip conversions:** Verify that converting nm → µm → nm returns the original array, nm → cm⁻¹ → nm returns the original array, and transmittance → A₁₀ → transmittance returns the original fractional values within machine precision.
* **Error conditions:** Ensure that unsupported units raise `UnitError` and that missing path length or mole fraction for α conversions raises informative exceptions.
* **No mutation:** Confirm that conversion functions do not mutate input arrays.

### 1.2 Ingesters

* **CSV ingestion:** Test ingestion of valid CSV files with and without headers.  Validate that column mapping is inferred correctly and can be overridden.
* **JCAMP‑DX ingestion:** Provide sample JCAMP files and verify that arrays and units match reference values.
* **Error handling:** Provide malformed files and ensure that ingestion raises descriptive `IngestError` exceptions.

### 1.3 Math Service

* **Resampling:** Test that `resample_to_common_grid()` aligns spectra correctly and throws an error when wavelength ranges do not overlap.
* **Subtraction and ratio:** Verify that subtraction of identical spectra yields zero within tolerance, ratio masks near‑zero denominators and uses epsilon only as fallback.
* **Normalization:** Confirm that normalised difference yields results within expected ranges.

### 1.4 Overlay Manager

* **Duplicate detection:** Test that ingesting the same file twice (with identical content) does not create duplicate entries and that renaming one does not affect the other.
* **Reordering:** Validate that drag‑and‑drop reordering updates the internal order and that signals are emitted to update the UI.

### 1.5 Plugin Loader

* **Discovery:** Ensure that plugins declared via entry points are discovered and instantiated.
* **Validation:** Verify that plugins missing required attributes raise clear errors and are not loaded.

## 2. Integration Tests

Integration tests simulate user workflows through the service layer without involving the GUI.  For example:

1. Ingest two spectra (CSV and JCAMP).
2. Compute their difference and ratio.
3. Invoke the functional‑group predictor on one spectrum.
4. Export the result and validate that the manifest matches expected keys and values.

Mocks or stubs are used to avoid network calls (e.g. to NIST).  A small test dataset (see `samples/`) with known outputs is included.

## 3. Golden‑Image Tests

Visual regressions in charts are detected using golden‑image testing.  The procedure is:

1. Render a spectrum or overlay using the PlotWidget.
2. Capture the resulting image as a PNG.
3. Compare the image against a baseline golden image using perceptual hashing or pixel difference with a tolerance.

If differences exceed a threshold, the test fails.  Golden images are stored in `tests/golden_images/`.  When legitimate UI changes occur, update the baseline images intentionally.

## 4. Performance Tests

Performance benchmarks measure ingestion time, rendering time and ML inference time for datasets of varying sizes (e.g. 10 k, 100 k, 1 M points).  Use `pytest-benchmark` to record timings and set acceptable thresholds.  Detect regressions across versions.

## 5. Continuous Integration

All tests run automatically on every pull request and push via a CI service (GitHub Actions, Azure Pipelines or similar).  The CI workflow includes:

1. Linting and formatting checks (using `ruff` and `black`).
2. Type checking with `mypy` or `pyright`.
3. Unit and integration tests with coverage reporting.
4. Golden‑image tests (enabled only on platforms with display support; otherwise skip).
5. Packaging the application into an installer and running a minimal smoke test to ensure it launches and the main window appears.

Failures at any stage block merges until resolved.  Test reports and coverage summaries are published as artefacts.

## 6. Sample Data for Tests

The `samples/` directory provides small spectra for testing:

- `sample1.csv`: A small CSV with 1 000 points in nm and %T.
- `sample2.jdx`: A JCAMP‑DX file with matching nm and absorbance.
- `sample3.fits`: A FITS file with a 2 000‑point spectrum.

Each sample includes a checksum and a minimal manifest.  Tests verify that ingestion and conversions produce the expected arrays.

## 7. Manual Testing and User Studies

Automated tests should be complemented with manual usability testing.  Recruit beta testers (e.g. peers in the research group) to use the application with their own datasets and report issues.  Collect feedback on the UI, performance and accuracy.  Record observations in the knowledge log and incorporate fixes.

## 8. Summary

This testing strategy combines unit, integration, visual, performance and user tests to ensure the new Spectra‑App meets its design goals.  Strict CI enforcement and sample datasets will prevent regressions and guarantee that all unit and conversion logic remains accurate.