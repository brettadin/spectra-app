# Plugin Development Guide

Spectra‑App is designed to be extensible through plugins.  This guide explains how to develop, package and register plugins for importers, transformers, exporters, machine‑learning models and similarity metrics.

## 1. Overview

Plugins are Python packages that adhere to specific interfaces and declare entry points in their `pyproject.toml` or `setup.py`.  The application discovers plugins at runtime by inspecting the `spectra_app.plugins` group.  Each plugin is isolated from the core code base, making it easy to add new functionality without modifying existing modules.

### Plugin Types

1. **Importer** – Loads spectra from a specific file format and returns a `Spectrum` object.
2. **Transformer** – Applies a mathematical or signal‑processing operation to a `Spectrum` and returns a new `Spectrum`.
3. **Exporter** – Saves spectra and manifests in a custom format (e.g. HDF5, PDF).
4. **ML Model** – Produces predictions (e.g. functional‑group identification) given a `Spectrum`.
5. **Similarity Metric** – Provides a distance function between two spectra for the similarity search.

## 2. Package Structure

Each plugin should be packaged as a standalone Python distribution with the following structure:

```
my_importer/
├── src/
│   └── my_importer/
│       ├── __init__.py
│       ├── plugin.py
│       ├── resources/…
│       └── …
├── pyproject.toml
└── README.md
```

The `pyproject.toml` (or `setup.py`) declares the plugin metadata and entry points.  For example, an importer plugin might include:

```toml
[project]
name = "my_importer"
version = "0.1.0"
description = "Importer for XYZ spectral format"
requires-python = ">=3.11"
dependencies = ["numpy", "spectra_app>=1.0.0"]

[project.entry-points."spectra_app.plugins"]
my_importer = "my_importer.plugin:XYZImporterPlugin"
```

## 3. Implementing an Importer

An importer plugin must implement the `Importer` protocol defined by Spectra‑App:

```python
from pathlib import Path
from typing import Tuple, Dict
from spectra_app.types import Spectrum, Importer

class XYZImporterPlugin(Importer):
    supported_extensions: Tuple[str, ...] = (".xyz",)

    def ingest(self, path: Path) -> Spectrum:
        # Read the file and parse wavelength and flux arrays
        # Perform unit detection and conversion to nm and canonical flux
        # Populate metadata with instrument details and units
        return Spectrum(
            id="uuid-1234",
            wavelength_nm=(…),
            flux=(…),
            metadata={"instrument": "XYZ", …},
            provenance=[{"importer": "XYZImporterPlugin", "timestamp": "2025-10-14T15:00:00Z"}]
        )

    def description(self) -> str:
        return "Importer for XYZ spectral format"
```

The `supported_extensions` tuple informs the application which file types the importer handles.  The `ingest()` method reads the file, performs necessary conversions (using `UnitsService` where appropriate) and returns a `Spectrum`.  Additional helper functions and resources (e.g. look‑up tables) can reside within the plugin package.

## 4. Implementing a Transformer

Transformers apply operations to existing spectra.  A transformer plugin must implement:

```python
from spectra_app.types import Spectrum
from typing import Dict

class SavitzkyGolaySmooth:
    name = "savitzky_golay"
    def apply(self, spectrum: Spectrum, *, window: int = 11, polyorder: int = 3) -> Spectrum:
        # perform smoothing on spectrum.flux using SciPy or custom code
        # build a new Spectrum with updated provenance
        …
```

The application will expose transformer plugins in the **Compare** panel or a dedicated **Transforms** panel.  The plugin should document its parameters and acceptable ranges in its README.

## 5. Implementing an Exporter

Exporters allow users to save data in formats beyond the built‑in CSV and JSON.  An exporter plugin must implement:

```python
from typing import Iterable
from spectra_app.types import Spectrum, Manifest

class NetCDFExporter:
    name = "netcdf"
    description = "Export spectra to netCDF"
    def export(self, spectra: Iterable[Spectrum], manifest: Manifest, path: Path) -> None:
        # write spectra and manifest into a netCDF file
        …
```

The application will list available exporters in the Export Wizard.

## 6. Implementing an ML Model

ML plugins produce predictions or annotations.  They must implement:

```python
from spectra_app.types import Spectrum
from typing import Dict

class FunctionalGroupClassifier:
    name = "ir_functional_groups_v3"
    version = "3.0.0"
    def predict(self, spectrum: Spectrum) -> Dict[str, any]:
        # run model and return predictions with confidence scores
        …

    def manifest(self) -> Dict[str, any]:
        return {
            "model": self.name,
            "version": self.version,
            "training_data": "NIST IR Database",
            "citations": [ … ],
            "licence": "MIT"
        }
```

The `predict()` method returns structured results (ranges, labels, scores).  The `manifest()` method provides provenance information that will be included in export manifests.  Models may load weights from files packaged within the plugin or downloaded at runtime.  Always document model training data and licence.

## 7. Implementing a Similarity Metric

Similarity plugins define a distance function between two spectra:

```python
from spectra_app.types import Spectrum

class PearsonCorrelation:
    name = "pearson_correlation"
    def distance(self, a: Spectrum, b: Spectrum) -> float:
        # compute 1 – correlation coefficient
        …
```

The SimilarityService will call `distance()` when ranking results.  Plugins should normalise inputs as needed and avoid mutating spectra.

## 8. Packaging and Distribution

Distribute plugins as Python packages on PyPI or via private repositories.  Each plugin should specify a minimum `spectra_app` version in its dependencies to ensure compatibility.  Users can install plugins with `pip install`.  The application’s plugin manager will detect newly installed plugins at startup or via a **Scan Plugins** button.

## 9. Testing Plugins

Provide unit tests within the plugin package.  Use the interfaces defined in `spectra_app.types` for type checking.  Test ingestion of sample files, correct outputs of transforms and exporters, and predicted labels of ML models.  Publish coverage reports where possible.

## 10. Security Considerations

Because plugins execute arbitrary code, review and sandboxing are important.  The application should isolate plugins in separate processes for operations that involve untrusted code (e.g. ML inference with third‑party models).  Plugin metadata should state the licence, author and any external dependencies.  Users should review these details before enabling a plugin.

## 11. Conclusion

The plugin architecture allows Spectra‑App to evolve organically as new data formats, analysis techniques and models emerge.  Clear interfaces, entry‑point registration and comprehensive documentation will help maintainers and third‑party developers extend the application safely and effectively.