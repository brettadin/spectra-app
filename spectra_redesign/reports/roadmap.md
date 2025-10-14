# Project Roadmap and Milestones

This roadmap outlines a four‑week plan for the redesign of Spectra‑App into a standalone Windows desktop application.  Each week includes a set of milestones with acceptance criteria.  Adjustments may be necessary based on actual progress and resource availability.

## Week 1 – Discovery and Architecture

**Objectives:**

1. Complete a full audit of the existing codebase (see `reports/repo_audit.md`).
2. Define the functional requirements and compile the feature parity matrix.
3. Evaluate desktop UI frameworks (PySide6/Qt, Tauri with Python backend, .NET MAUI) and prepare a decision matrix.
4. Choose the technology stack and draft the high‑level architecture.
5. Draft the units and provenance specifications.

**Acceptance criteria:**

- A complete audit report with identified issues and initial remediation strategies.
- A decision matrix with pros/cons, performance considerations and packaging implications for at least three UI frameworks.
- A preliminary architecture diagram showing modules, data flow and plugin boundaries.
- Draft specifications for canonical units, conversion rules and manifest schema.

## Week 2 – Skeleton Implementation and Unit Service

**Objectives:**

1. Set up the project scaffold using the chosen UI framework.
2. Implement the canonical units service with conversions for wavelength (nm, µm, Å, cm⁻¹) and flux (transmittance, absorbance, absorption coefficient).
3. Create a basic UI shell with tabs (Data, Compare, Functional Groups, Similarity, History) and navigation.
4. Integrate the units service into the UI shell; allow users to toggle display units.
5. Write initial unit tests covering the conversions and UI shell instantiation.

**Acceptance criteria:**

- The project builds and runs a minimal desktop window on Windows.
- Users can open the Data tab and switch wavelength units without mutating underlying data.
- Unit tests for the units service pass in continuous integration.

## Week 3 – Data Ingestion and Core Operations

**Objectives:**

1. Implement the data ingest module supporting CSV and JCAMP‑DX as initial formats.
2. Design a plugin interface for importers and write at least one additional importer (e.g. FITS).
3. Develop the overlay manager component: display imported spectra, manage trace list, allow renaming and hiding.
4. Implement differential operations (subtract, ratio) using the unified resample function with masking of near‑zero denominators.
5. Integrate the differential operations into the Compare tab.

**Acceptance criteria:**

- Users can drag and drop sample datasets and see them listed in the overlay manager.
- The Compare tab allows selecting two spectra and computing their difference or ratio.  Results are plotted correctly with masked spikes and suppressed trivial results.
- Importers are decoupled modules with clear interfaces and unit tests.

## Week 4 – ML Integration, Export and Documentation

**Objectives:**

1. Implement the functional‑group identification plugin (using the existing IR classifier) and display results in the Functional Groups tab.
2. Add similarity search functionality using a local dataset as a prototype.
3. Implement the export wizard that packages selected spectra, derived data, plots and a manifest conforming to the provenance schema.
4. Finalise documentation: architecture spec, plugin development guide, units and provenance spec, UI contract and testing guide.
5. Prepare the Windows build using the chosen packaging tool and conduct smoke tests on Windows 10 and 11.

**Acceptance criteria:**

- The functional‑group classifier runs on a sample spectrum and overlays predicted bands.
- The Similarity tab returns a ranked list when searching against the sample dataset.
- The export wizard produces a ZIP containing a manifest and PNG plot that open correctly.
- Comprehensive documentation is complete and cross‑linked; the README explains how to run and build the application.
- The Windows installer installs and runs without errors on test machines.

## Post‑1.0 Tasks (Future Work)

After the 1.0 release, future milestones may include:

- Adding support for additional data formats (netCDF, HDF5), remote telescopic archives and user‑definable plugins.
- Integrating machine‑learning models for exoplanet composition prediction.
- Implementing dark/light theme switching and accessibility improvements.
- Extending the knowledge log to support natural‑language queries.