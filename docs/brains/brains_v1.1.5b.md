# Brains — v1.1.5b
_Last updated (UTC): 2025-09-21T02:00:00Z_

## Purpose
This entry documents the continuity contract for **Spectra App v1.1.5b**.
It focuses on the ingestion/unit normalisation improvements and the complete rewrite of the Atlas documentation now surfaced inside the app.

## Canonical Continuity Sources
- `docs/brains/brains_v1.1.5b.md` (this file)
- `docs/brains/brains_INDEX.md` (table of live continuity assets)
- `docs/brains/ai_handoff.md` (bridge to current AI prompt)
- `docs/PATCH_NOTES/v1.1.5b.txt` (paired patch notes)
- `docs/atlas/` (user & maintainer documentation displayed in-app)
- `app/server/ingestion_pipeline.py`, `app/utils/units.py`, `app/ui/main.py`, `app/export_manifest.py` (modules touched by v1.1.5b scope)

## Non-Breakable Invariants
1. **Unit provenance** — every wavelength/flux conversion records original units, canonical units, and formulae in the provenance log and export manifest.
2. **Duplicate detection** — uploaded files are hashed; identical content cannot be ingested twice in one session.
3. **Dual-axis semantics** — emission traces live on the left axis in `F_λ`; absorption/transmission traces live on the mirrored right axis with clear labelling.
4. **Atlas availability** — the docs in `docs/atlas/` must render within the in-app Docs tab. Links must remain relative and valid.
5. **Continuity sync** — brains log, Atlas, patch notes, and AI handoff references stay in lockstep for this version.

## v1.1.5b Scope
- Finalise SI-based ingestion and F_ν ↔ F_λ conversions (follow-up to v1.1.5a continuity work).
- Introduce a modular uploader for CSV, TXT, and FITS with segment awareness, metadata extraction, and duplicate prevention.
- Wire provenance logging into exports so PNG/CSV/JSON bundles describe every transformation.
- Rebuild the Atlas documentation set (`docs/atlas/`) into site-ready pages covering onboarding, ingestion, uploads, visualisation, exporting, and maintainer duties.
- Update brains index and patch notes to reference the new version and documentation structure.

## Implementation Notes
- `ingestion_pipeline.ProcessedSpectrum` now stores `provenance.steps` with conversion formulas for downstream export/manifest use.
- `app/ui/main.py` reads Atlas markdown files for the Docs tab; ensure new pages are linked in `docs/atlas/index.md`.
- `export_manifest.build_manifest()` attaches provenance blocks per trace plus a continuity section pointing to this brains log and patch notes.
- Atlas markdown assumes Plotly renders with SI metres internally—any change to axis units must update both the docs and provenance helpers.

## Documentation Updates
- Atlas reorganised into:
  - `index.md`
  - `getting-started.md`
  - `data-ingestion.md`
  - `uploads-and-sources.md`
  - `visualization.md`
  - `exporting-and-sharing.md`
  - `developer-guide.md`
- `docs/index.md` now links directly to the Atlas and brains index.
- Future docs must extend these files or archive them under `docs/patches/` rather than deleting sections.

## Verification & Automation
- Run `.\RUN_CMDS\Verify-Project.ps1` or `pytest` to confirm ingestion tests and continuity guards pass.
- Manual QA: upload representative FITS/CSV/TXT files, toggle emission/absorption axes, export manifest, and ensure provenance entries reflect the new conversions.

## Runbook
```
.\RUN_CMDS\Clean-Install.ps1    # optional refresh
.\RUN_CMDS\Start-Spectra.ps1    # launch UI
.\RUN_CMDS\Verify-Project.ps1   # pre-commit verification
```
Linux/macOS equivalents follow the commands in `docs/atlas/getting-started.md`.

## Risks & Mitigations
- **Docs drift** — Mitigate by editing brains + Atlas + patch notes in the same change set.
- **Unit regressions** — Guard with targeted unit tests and provenance assertions before merging.
- **Atlas broken in-app** — Always use relative links and run the UI to confirm the Docs tab renders the Markdown pages without missing assets.

## Backlog
- Add screenshots or GIFs of the Docs tab once the hosting pipeline can bundle images.
- Expand Atlas with troubleshooting for common FITS header issues.
- Expose a CLI tool that reads the export manifest and reconstructs Plotly figures for headless validation.
