# Developer & AI Maintainer Guide

This section keeps implementers aligned with the contracts enforced by v1.1.5b. Read this before modifying ingestion, plotting, or export behaviour.

## Continuity Obligations
- Update **brains**, **AI handoff bridge**, **patch notes**, and **Atlas** pages together.
- Maintain `docs/brains/brains_INDEX.md` so the current version points to the latest files.
- Run `.\RUN_CMDS\Verify-Project.ps1` (or `pytest`) before committing.

## Code Architecture
- `app/server/ingestion_pipeline.py`
  - Entry point: `ingest_uploaded_file()`.
  - Produces `ProcessedSpectrum` objects with `provenance` records.
  - Handles duplicate detection via SHA-256 hashing.
- `app/utils/units.py`
  - Converts wavelengths and fluxes.
  - Exposes provenance helpers `record_conversion()` and `format_units()`.
- `app/ui/main.py`
  - Streamlit layout, upload widgets, legend toggles, metadata cards.
  - Defines Plotly figure with dual y-axes and axis labelling.
- `app/export_manifest.py`
  - `build_manifest()` collates traces, continuity metadata, and plot state.

## Adding New Features
1. Extend data classes in `ingestion_pipeline.py` if more metadata is required. Always add regression tests.
2. Surface new toggles or displays in `main.py`. Update `docs/atlas` and screenshot-based QA if applicable.
3. Expand manifests carefully—downstream consumers rely on key names. Document additions in patch notes.
4. Avoid breaking F_ν/F_λ conversions; add unit tests for any new conversion pathways.

## Testing Checklist
- `pytest`
- `python scripts/print_version.py`
- Manual smoke: upload FITS, CSV, and TXT samples; toggle emission/absorption; export manifest.

## Documentation Workflow
- Write or revise Atlas pages in Markdown (this folder). These files are embedded directly into the in-app Docs tab.
- Link back to code modules so future maintainers can trace behaviour.
- When retiring a feature, archive the relevant Atlas page under `docs/patches/` instead of deleting it outright.

## Release Process
1. Bump the patch version in `PATCHLOG.txt`.
2. Create a patch notes file under `docs/PATCH_NOTES/`.
3. Update the brains log and index.
4. Ensure `scripts/print_version.py` reflects the new version when run.
5. Merge via a reviewed PR that passes CI.

Staying disciplined keeps the app reproducible for astronomers and maintainable for future agents.
