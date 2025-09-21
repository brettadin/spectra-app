# Brains — v1.1.5c
_Last updated (UTC): 2025-09-21T23:00:00Z_

## Purpose
This entry captures the follow-up continuity work for **Spectra App v1.1.5c**.
It hardens the overlay workspace after the v1.1.5b ingestion overhaul by fixing
Streamlit API deprecations, improving similarity diagnostics, and guarding
against missing wavelength metadata in downstream plots.

## Canonical Continuity Sources
- `docs/brains/brains_v1.1.5c.md` (this log)
- `docs/brains/brains_INDEX.md` (live continuity table)
- `docs/brains/ai_handoff.md` (bridge to the operative AI prompt)
- `docs/PATCH_NOTES/v1.1.5c.txt` (paired patch notes)
- `app/ui/main.py`, `app/similarity.py`, `app/similarity_panel.py`, `app/archive_ui.py` (modules changed in this patch)

## Non-Breakable Invariants
1. **Width API compliance** — all Streamlit tables/charts must use the new
   `width="stretch" | "content"` parameter in place of the deprecated
   `use_container_width` flag. Future UI edits must continue honouring this.
2. **Similarity aliasing** — duplicate trace labels are enumerated consistently
   (e.g. `He (example)`, `He (example) [2]`) so matrices remain arrow-friendly
   and users can map aliases back to their originals.
3. **Wavelength continuity** — every trace reaching the overlay plot maintains a
   `wavelength_m` column; when upstream payloads only provide `wavelength_nm`, the
   UI reconstructs metres before rendering so conversions stay unit-safe.

## v1.1.5c Scope
- Swap Streamlit layout calls to the new `width` argument in the overlay table,
  archive previews, similarity matrices, and line metadata tables.
- Deduplicate similarity matrix labels with alias captions so pyarrow export
  no longer fails when users load repeated lamp spectra.
- Add a defensive rebuild for the `wavelength_m` column during plotting to
  handle legacy payloads that only expose nanometre grids.

## Implementation Notes
- `app/similarity.py` now exposes `_unique_labels` to attach alias metadata to
  each metric frame; `app/similarity_panel.py` surfaces a caption summarising the
  aliases.
- `app/ui/main.py` rebuilds metres from nanometres when needed before converting
  to the selected display units, preventing viewport conversions from crashing.
- `app/archive_ui.py` mirrors the width migration so archive previews share the
  same layout contract as the overlay workspace.

## Documentation Updates
- Brains index now references this entry and the new patch notes (`v1.1.5c`).
- AI handoff bridge expectations advanced to v1.1.5c (see
  `docs/brains/ai_handoff.md`).

## Verification & Automation
- Run `.\RUN_CMDS\Verify-Project.ps1` or `pytest`.
- Manual QA: add duplicate-labelled overlays (e.g. multiple `He (example)`
  traces), confirm similarity matrices render with enumerated labels, and export
  manifests still reflect provenance.

## Runbook
```
.\RUN_CMDS\Start-Spectra.ps1    # launch UI
.\RUN_CMDS\Verify-Project.ps1   # regression suite
```
Linux/macOS equivalents follow `docs/atlas/getting-started.md`.

## Risks & Mitigations
- **Streamlit API drift** — Keep an eye on future layout changes; run the UI to
  ensure deprecation warnings disappear.
- **Alias confusion** — Aliases are captioned in the Similarity tab; maintain
  this messaging if you tweak the panel layout.
- **Legacy payloads** — The wavelength rebuild should catch missing metre grids,
  but add regression tests if new ingestion paths appear.

## Backlog
- Extend exporter metadata to include the alias map used in similarity matrices.
- Add automated tests for `_unique_labels` once the similarity module gains
  formal coverage.
