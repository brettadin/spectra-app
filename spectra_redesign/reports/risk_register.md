# Risk Register and Mitigation Plan

This document captures the primary risks identified for the Spectra‑App redesign project and proposes mitigation strategies.  It should be reviewed regularly and updated as the project evolves.

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **1** | **Feature regression** – essential capabilities may be lost during the transition from Streamlit to a desktop framework. | Medium | High | Compile a comprehensive feature parity matrix (see `reports/feature_parity_matrix.md`) and implement automated regression tests that exercise ingest, overlay, differential, similarity and ML functions.  Use acceptance criteria for each milestone. |
| **2** | **Unit conversion errors** – incorrect conversions could produce misleading results, undermining trust. | High | High | Design a canonical units service with thorough unit tests and golden‑value checks.  Enforce idempotent conversions; never mutate source data. |
| **3** | **Poor performance on large datasets** – interactive plotting and ML predictions may lag when loading large or high‑resolution spectra. | Medium | Medium | Implement down‑sampling tiers and progressive loading.  Use efficient numerical libraries (NumPy, Numba) and multi‑threading for heavy calculations.  Cache results where appropriate. |
| **4** | **Dependency management** – third‑party libraries may introduce vulnerabilities or licencing issues. | Medium | Medium | Audit all dependencies, pin versions in `requirements.txt`, and monitor CVEs.  Prefer well‑maintained libraries with permissive licences.  Document licences in the `About` dialog. |
| **5** | **Data provenance gaps** – missing or incomplete provenance could undermine reproducibility. | Low | High | Define a manifest schema capturing source files, checksums, units, transforms and citations.  Require that every export include a manifest.  Provide UI prompts when metadata is missing. |
| **6** | **Privacy and API key leakage** – storing or logging credentials used for external providers could expose sensitive information. | Low | Medium | Store API keys in encrypted configuration files outside source control.  Mask credentials in logs.  Provide an encrypted secrets manager for plugin developers. |
| **7** | **User learning curve** – moving from a simple web UI to a more complex desktop application may confuse existing users. | Medium | Low | Provide thorough documentation, onboarding tutorials and tooltips.  Preserve familiar workflow patterns (e.g. overlay first, then analysis) while improving navigation. |
| **8** | **Packaging and distribution challenges** – creating a seamless Windows installer may be difficult, and unsigned binaries could trigger warnings. | High | Medium | Evaluate packaging tools (PyInstaller, Tauri Bundler, MSIX).  Allocate time for code‑signing and testing on multiple Windows versions. |
| **9** | **Scope creep** – the desire to add new features (e.g. exoplanet composition predictions) could delay delivery. | Medium | Medium | Adhere to the initial scope and milestone plan.  Defer non‑essential features to post‑1.0 releases.  Use a backlog with prioritisation. |
| **10** | **AI/agent misalignment** – the AI assistant and application may fall out of sync, causing redundant work. | Low | Medium | Implement a consistent knowledge log accessible both to the app and the AI agent.  Use stable APIs and structured messages for AI ↔ app communication. |

## Review Schedule

The risk register should be reviewed at the end of each sprint (weekly).  New risks should be added as they are discovered, and the mitigation strategies should be updated based on the project’s progress.