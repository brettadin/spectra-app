# System Design Specification

This specification describes the internal architecture of the redesigned Spectra‑App, focusing on module boundaries, data flow, event handling and extensibility mechanisms.  The goal is to support an extensible, testable and maintainable system while preserving existing functionality.

## 1. Module Boundaries

### 1.1 Presentation Layer (UI)

The UI is implemented with PySide6 and structured as a set of reusable widgets.  Key components include:

- **MainWindow** – Hosts the menu bar, toolbar, status bar and a `QTabWidget` containing the major panels.  Handles global actions such as opening files, exporting results and accessing settings.
- **DataTab** – Allows users to import spectra, view loaded datasets and change display units.  Contains:
  * **IngestWidget** – A drag‑and‑drop area that accepts files.  It uses signals to request ingestion by the service layer and displays a progress bar.
  * **SpectrumListView** – Shows all loaded spectra with options to rename, reorder, hide and delete traces.
- **CompareTab** – Provides differential operations.  It lets the user select two spectra and choose an operation (difference, ratio, normalised difference).  It displays the result in a chart widget.
- **FunctionalGroupsTab** – Communicates with the ML plugin to classify functional groups and overlays predicted bands on the chart.  Shows a table of predictions with confidence scores.
- **SimilarityTab** – Allows users to perform similarity searches against local or remote databases.  Displays ranked results and enables overlaying selected matches.
- **HistoryTab** – Displays the knowledge log.  Users can filter entries by date or tag and click to view details.
- **SettingsDialog** – Manages application preferences (e.g. default units, colour themes, plugin directories).  Accessible from the menu.

Each widget communicates with the service layer via Qt signals and slots.  The UI should never perform business logic directly; instead it packages user actions into requests sent to services.

### 1.2 Service Layer

The service layer consists of singleton or factory‑created classes providing core functionality:

- **IngestService** – Accepts file paths and plugin identifiers, loads the file via the appropriate importer and returns a `Spectrum` object.  Performs basic validation (e.g. that wavelength and flux arrays have equal length) and captures metadata.
- **UnitsService** – Stores canonical values for each spectrum and offers methods to convert wavelengths between nm, µm, Å and cm⁻¹ and flux between transmittance, absorbance and absorption coefficient.  Provides idempotent conversions and metadata provenance.
- **OverlayService** – Maintains a registry of loaded spectra keyed by a unique identifier (e.g. SHA‑256 of the raw file).  Implements adding, renaming, reordering and removing traces.  Exposes iterators for the UI to query current spectra.
- **MathService** – Performs operations on spectra: resampling to a common grid, subtracting, ratio calculations with masking, normalised difference and smoothing.  Returns a new `Spectrum` instance representing the derived data with updated provenance.
- **MLService** – Serves as a gateway to ML plugins.  Given a spectrum, it calls the selected ML model to obtain predictions (e.g. functional group ranges) and returns structured results.
- **SimilarityService** – Provides vectorisation, distance metrics and search functions against a specified dataset.  Can be extended with different metrics via plugins.
- **ExportService** – Generates manifests, saves plots and data into a specified directory or archive, and writes provenance files.
- **KnowledgeService** – Writes entries into `docs/history/KNOWLEDGE_LOG.md` and reads them for the history tab.

### 1.3 Data Layer

Data is represented as immutable **Spectrum** objects containing:

- `id`: unique identifier (e.g. UUID or hash)
- `wavelength_nm`: tuple of floats in canonical units
- `flux`: tuple of floats in canonical units
- `metadata`: dictionary capturing source information (file name, instrument, date, instrument settings)
- `provenance`: list of transformation records (see provenance spec)

Spectra are loaded via **Importer plugins**, each implementing an interface:

```python
class Importer(Protocol):
    supported_extensions: Tuple[str, ...]
    def ingest(self, path: Path) -> Spectrum: ...
```

Importers reside in the `plugins/importers/` directory and are discovered at runtime via entry points or scanning.  The Data Layer also caches previously loaded spectra to avoid re‑reading large files.

### 1.4 Plugins System

Plugins fall into several categories:

1. **Importers** – Provide `ingest()` functions for new file formats.  Each plugin defines `metadata` describing the format, required dependencies and units mapping.
2. **Transformers** – Perform operations on spectra beyond the built‑in MathService (e.g. smoothing, baseline correction).  Provide `apply(spectrum: Spectrum, **kwargs) -> Spectrum`.
3. **Exporters** – Optional modules that save data into non‑default formats (e.g. netCDF, HDF5, PDF reports).  Provide `export(spectra: Iterable[Spectrum], manifest: Manifest, path: Path) -> None`.
4. **ML Models** – Provide `predict(spectrum: Spectrum) -> MLResult` and a manifest describing model version, training data and licence.
5. **Similarity Metrics** – Provide `distance(a: Spectrum, b: Spectrum) -> float` and can be registered with the SimilarityService.

Plugins are packaged as Python distributions with entry points declared under the group `spectra_app.plugins`.  The application loads them at startup and exposes them in the settings.

## 2. Data Flow

1. **Import:** User drags a file onto the IngestWidget → IngestWidget emits a signal carrying the file path → MainWindow delegates to IngestService → IngestService selects the appropriate Importer → Importer reads the file, constructs a Spectrum object with canonical units → IngestService stores the Spectrum in the OverlayService and updates the KnowledgeService with an import entry → OverlayService emits a signal to notify the UI.

2. **Overlay & Display:** OverlayService maintains the list of spectra.  When the UI requests the overlay list, it uses UnitsService to obtain wavelength and flux arrays in the user’s selected units.  The PlotWidget receives these arrays and renders them.  The legend uses the `Spectrum`’s `metadata['label']` and fingerprint.

3. **Math Operations:** User selects two spectra and an operation in CompareTab → CompareTab emits a request to MathService → MathService retrieves canonical data from OverlayService, resamples both to a common grid and applies the chosen operation → MathService constructs a new Spectrum with provenance referencing both inputs and the operation parameters → The new Spectrum is returned to OverlayService and optionally added to the overlay list.

4. **ML Predictions:** User clicks “Identify functional groups” → FunctionalGroupsTab emits a request to MLService → MLService invokes the registered ML plugin → The plugin returns ranges and labels → FunctionalGroupsTab overlays shaded bands and displays a table.  The knowledge log records the model name and result summary.

5. **Similarity Search:** User selects a database and query spectrum → SimilarityTab emits a request to SimilarityService → SimilarityService vectorises the spectrum and compares it against pre‑computed vectors, returning a sorted list of matches → SimilarityTab displays results with similarity scores and metadata.  Users can overlay selected matches.

6. **Export:** User invokes Export Wizard → ExportService collects selected spectra and their provenance, generates a manifest (see provenance spec) and writes data and plots to disk → KnowledgeService records the export event with location, timestamp and checksum.

## 3. Event Model and Concurrency

PySide6’s signal/slot mechanism underpins the event model.  UI widgets emit signals (e.g. file selected, operation requested); service classes expose slots that receive these signals and perform actions.  Heavy or blocking operations (file reading, network requests, ML inference) are executed in background threads using Qt’s `QThreadPool` or Python’s `concurrent.futures.ThreadPoolExecutor`.  Results are communicated back to the UI via signals.

To ensure thread safety:

- Services emit results in the main thread by using `QObject.invokeMethod()` or `QMetaObject.invokeMethod()` with `Qt.QueuedConnection`.
- Spectrum objects are immutable after creation, avoiding race conditions.
- UnitsService caches conversions to reduce computation in repeated requests.

## 4. Extensibility and Dependency Injection

The application uses a lightweight dependency injection pattern: a `ServiceContainer` holds singletons for each service.  Widgets request services from the container during construction.  This design allows services to be replaced (e.g. for testing) and enables plugin injection.  The plugin loader registers additional services or extends existing ones by adding to a registry.

## 5. Error Handling and User Feedback

All service methods return either a result or raise a domain‑specific exception.  The UI catches exceptions and presents user‑friendly messages via modal dialogs or toast notifications.  Errors are logged to a rotating file (`logs/app.log`) with timestamps and stack traces.  When an error occurs, the KnowledgeService writes an entry to the knowledge log.

## 6. Logging and Knowledge Log

Every significant action (import, operation, prediction, export) triggers an entry in the knowledge log.  Entries are appended as Markdown with structured front‑matter including timestamp, user ID (if available), operation, inputs, outputs and a hash of the resulting `Spectrum` (for traceability).  The log is human‑readable and can be parsed by future AI agents.  The HistoryTab reads and filters these entries for display.

## 7. Summary

This system design isolates concerns across layers, utilises Qt’s robust signal/slot architecture for responsive interaction and implements a plugin framework to enable long‑term extensibility.  Coupled with the units and provenance specifications described elsewhere, this design supports accurate, reproducible and user‑friendly spectral analysis.