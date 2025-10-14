# Provenance and Citation Specification

To support reproducibility and scholarly rigour, every derived dataset and export must include a machine‑readable manifest capturing provenance, units and citations.  This specification defines the structure of the manifest and explains how the application uses it.

## 1. Overview

A manifest is a JSON document saved alongside exported data (e.g. as `manifest.json`) and embedded into package archives.  The manifest describes:

* **Source files** – The raw input files used to generate the export, including file names, sizes and checksums.
* **Acquisition metadata** – Instrument details, sample information, acquisition parameters and original units.
* **Transformations** – A chronological list of operations applied to the data, including mathematical operations, unit conversions, smoothing or normalisation, along with parameters and versions of the algorithms.
* **ML predictions** – If machine‑learning models were used (e.g. functional‑group classification), the model name, version, training dataset and citations.
* **Application version** – Version number and build date of Spectra‑App and the versions of libraries used.
* **Timestamp** – UTC timestamp when the export was created.
* **Citations** – References to datasets, instruments, algorithms or publications that underlie the data.

## 2. JSON Schema

Below is a simplified JSON schema (expressed informally) for the manifest:

```json
{
  "version": "1.0",
  "app": {
    "name": "SpectraApp",
    "version": "v1.2.1",
    "build_date": "2025-10-14T00:00:00Z",
    "git_commit": "abc123",
    "libraries": {
      "numpy": "1.26.2",
      "pyside6": "6.5.3",
      "…": "…"
    }
  },
  "timestamp_utc": "2025-10-14T15:23:45Z",
  "sources": [
    {
      "path": "sun_spectrum.csv",
      "size_bytes": 123456,
      "checksum_sha256": "<hash>",
      "units": {
        "wavelength": "nm",
        "flux": "%T"
      },
      "metadata": {
        "instrument": "Ocean Optics USB4000",
        "location": "Atlanta, GA",
        "acquired_utc": "2025-09-28T01:15:00Z",
        "resolution_nm": 0.5,
        "path_length_m": 0.01,
        "mole_fraction": null
      }
    },
    {
      "path": "nist_water.jdx",
      "size_bytes": 98765,
      "checksum_sha256": "<hash>"
    }
  ],
  "transforms": [
    {
      "name": "unit_conversion",
      "description": "Converted wavelength from nm to cm-1",
      "parameters": {
        "target_unit": "cm^-1"
      },
      "timestamp_utc": "2025-10-14T15:24:00Z"
    },
    {
      "name": "subtract",
      "description": "Subtracted sun_spectrum from nist_water",
      "parameters": {},
      "timestamp_utc": "2025-10-14T15:24:05Z"
    }
  ],
  "ml_predictions": [
    {
      "model": "ir_functional_groups_v2",
      "version": "2.0.0",
      "source": "ml_models/ir_groups",
      "training_data": "NIST IR Quantitative Database",
      "metrics": {
        "precision": 0.92,
        "recall": 0.88
      },
      "citations": [
        {
          "title": "Quantitative Infrared Spectroscopy",
          "doi": "10.1000/jxyz.2023.001",
          "authors": ["A. Researcher", "B. Scientist"],
          "year": 2023
        }
      ],
      "predictions": [
        {
          "functional_group": "Hydroxyl",
          "range_cm^-1": [3200, 3600],
          "confidence": 0.95
        },
        {
          "functional_group": "Carbonyl",
          "range_cm^-1": [1700, 1750],
          "confidence": 0.87
        }
      ]
    }
  ],
  "citations": [
    {
      "title": "Ocean Optics USB4000 Spectrometer User Manual",
      "url": "https://oceanoptics.com/manuals/usb4000/",
      "year": 2018
    },
    {
      "title": "NIST Quantitative Infrared Database",
      "doi": "10.18434/T4H595",
      "year": 2021
    }
  ]
}
```

Developers may extend this schema with additional fields, provided they maintain backward compatibility and preserve required core fields (`app`, `sources`, `transforms`, `timestamp_utc`).

## 3. Usage

* **Creation:** The ExportService generates a manifest when the user exports data.  It gathers information from the Data Layer (source spectra), the Service Layer (list of transformations and parameters), and the MLService (if predictions were made).
* **Embedding:** When exporting to formats like ZIP or HDF5, the manifest is included as `manifest.json`.  When exporting to plain text (e.g. CSV), the manifest is saved in the same directory and the file names cross‑reference each other.
* **Re‑ingestion:** The IngestService recognises JSON manifests.  When a manifest is ingested, the app reconstructs the derived spectra by loading the referenced sources and reapplying the recorded transforms.  This ensures reproducibility.
* **Citation display:** The UI displays a summary of citations included in the manifest and provides links to DOIs or URLs.  Users can add citations manually in the export wizard.

## 4. Citation and Licensing

The manifest must include citations for any external dataset, algorithm, model or instrument manual used to produce the export.  All third‑party licences (e.g. LGPL for Qt, MIT for Tauri) should be recorded in the `app.libraries` section.  If the export includes ML predictions, the manifest must state the model’s licence and training data.  These practices ensure transparency and academic integrity.