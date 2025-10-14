# Spectra Redesign Project

This repository provides the starting point for the complete rewrite of the
Spectra‑App into a modern, modular Windows desktop application.  The goal of
this effort is to retain all existing features while addressing legacy
limitations such as messy unit conversions, brittle Streamlit UI logic and
unstructured knowledge logs.  Everything in this tree has been designed to
enable future agents to extend the program without losing historical
context.

## Structure

- **reports/** – Results of the code audit and planning phase.  These documents
  catalogue the current system, enumerate bugs, normalise historical logs,
  map feature parity and outline risks and milestones.
- **specs/** – Technical specifications for the new application.  These cover
  architecture decisions, system design, unit and provenance schemas, UI
  contract, testing strategy, packaging and plugin development guidelines.
- **docs/** – End‑user and developer documentation, including a consolidated
  knowledge log (see `docs/history/KNOWLEDGE_LOG.md`).
- **samples/** – Sample datasets and corresponding provenance manifests used to
  drive tests and serve as templates for new data imports.
- **app/** – The skeleton of the new PySide6‑based application.  This
  includes service classes for units, provenance and data import, a simple
  main window and stubs for future functionality.
- **tests/** – Initial test suite verifying critical functionality.  Tests
  currently cover unit conversions and manifest hashing; new tests should be
  added as modules are implemented.

## Getting Started

1. Install the Python dependencies.  A `pyproject.toml` or `requirements.txt`
   will be added once the implementation phase begins, but to run the
   skeleton you need at least:

   ```bash
   python -m pip install PySide6 numpy
   ```

2. Navigate to the `app` directory and run the main module:

   ```bash
   python -m app.main
   ```

   This will launch a minimal window that demonstrates the basic
   application structure.  Future iterations will populate the UI with tabs
   and controls as described in the specifications.

3. Explore the `samples` folder to see an example dataset (`sample_spectrum.csv`)
   and its associated provenance manifest (`sample_manifest.json`).  The
   manifest was generated using the `ProvenanceService` class defined in
   `app/services/provenance_service.py`.  Use this as a template when
   ingesting your own data during development.

4. Run the tests using `pytest` to confirm that core services behave as
   expected:

   ```bash
   python -m pip install pytest
   pytest -q
   ```

## Contributing

See `docs/architecture.md` and `docs/plugin_dev_guide.md` for guidance on
extending the system.  Before implementing new features, refer to the
feature parity matrix in `reports/feature_parity_matrix.md` to ensure that
existing capabilities remain intact.  All changes should be accompanied by
updated documentation and tests.
