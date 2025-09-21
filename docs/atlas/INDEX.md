# Spectra Atlas Documentation

Welcome to the living handbook for the Spectra App. The Atlas captures how to load, inspect, and export spectra in version **v1.1.5b**. Everything in this section mirrors the in-app “Docs” tab so you can reference the workflow without leaving the application.

## Quick Navigation
- [Getting Started](getting-started.md) — install prerequisites, launch the Streamlit UI, and orient yourself within the workspace.
- [Data Ingestion Pipeline](data-ingestion.md) — understand how wavelengths and fluxes are normalised, convolved, and rebinned before plotting.
- [Uploads & Built-in Sources](uploads-and-sources.md) — supported file formats, duplicate detection, and lamp/archive overlays.
- [Visualisation & Analysis](visualization.md) — plot controls, dual-axis behaviour, metadata panels, and comparison tools.
- [Exporting & Sharing](exporting-and-sharing.md) — capture what you see as PNG/CSV plus a provenance manifest.
- [Developer & AI Maintainer Guide](developer-guide.md) — architectural notes and guardrails for extending the app.

## How to Read This Atlas
Each article is self-contained and linked back to the relevant modules inside `app/`. Code snippets reference the canonical pipelines in `app/server/ingestion_pipeline.py`, `app/ui/main.py`, and `app/export_manifest.py`. When we introduce a transformation, we list:

1. **Input expectation** — the format and units the app accepts from users.
2. **Transformation** — the conversion or computation performed internally (with units and formulae).
3. **Output** — how the processed data appears in the UI and exports.

The documentation tracks only the behaviours that ship in v1.1.5b. Future releases must add new sections instead of rewriting these so historical behaviour remains auditable.

## Version Compatibility
- Current UI build: `app/ui/main.py` @ v1.1.5b
- Ingestion pipeline: `app/server/ingestion_pipeline.py`
- Export manifest: `app/export_manifest.py`
- Tests covering the contract: `tests/test_continuity.py`

If you change any of the modules above, update this Atlas alongside the brains log, patch notes, and AI handoff bridge to keep continuity intact.

## Feedback Loop
Found an inconsistency or planning a new feature? Start by updating `docs/brains/brains_v1.1.5b.md`, then revise the relevant Atlas pages. The Atlas should always mirror the actual behaviour users experience after running `streamlit run app/ui/main.py`.
