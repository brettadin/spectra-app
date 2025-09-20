# Brains — v1.1.5a
_Last updated (UTC): 2025-09-21T00:00:00Z_

## Purpose
This entry documents the continuity contract for **Spectra App v1.1.5a**.
It captures why we restructured the brains/patch-note flow, how the export manifest references it, and where provider caches now live.
Treat this as the authoritative brief before any future patching.

## Canonical Continuity Sources
- `docs/brains/brains_v1.1.5a.md` (this file)
- `docs/brains/brains_INDEX.md` (table of live continuity assets)
- `docs/brains/ai_handoff.md` (bridge to current AI prompt)
- `docs/PATCH_NOTES/v1.1.5a.txt` (paired patch notes)
- `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.4.md` (latest prompt to extend)
- `data/providers/` (provider cache directories that must exist)

## Non‑Breakable Invariants
1. **Overlay/Differential/UI contract** remain exactly as in v1.1.4: overlays render, duplicate guard works, unit conversions round-trip, exports bundle PNG/CSV/manifest.
2. **Fetcher routing** (`app/server/fetch_archives.py`) keeps emitting normalized spectra and populating provenance.
3. **Provider caches** under `data/providers/<provider>/` must survive upgrades; deleting them breaks the verification script and future fetch patches.
4. **Continuity docs** are updated together: brains, AI handoff bridge, patch notes, and manifest references. Missing any of them fails automation.

## v1.1.5a Scope
Goal: formalize continuity metadata so every export and verification step points back to the brains/patch notes while reserving provider cache space.
- Introduce `docs/brains/brains_INDEX.md` and `docs/brains/ai_handoff.md` as the mandated template.
- Store patch notes at `docs/PATCH_NOTES/<version>.txt` and link them reciprocally with the brains log.
- Add provider cache directories: `data/providers/mast`, `data/providers/eso`, `data/providers/simbad`, `data/providers/nist`.
- Update the export manifest with a `continuity` block referencing brains, patch notes, AI handoff bridge, and provider directories.
- Extend `RUN_CMDS/Verify-Project.ps1` and tests so missing links or directories fail fast.

## Architecture & Implementation Notes
- New module `app.continuity` exposes `get_continuity_links()` and is the single source of truth for continuity paths.
- `app/export_manifest.py::build_manifest()` centralizes manifest assembly and injects the continuity block.
- `app/ui/main.py` now delegates manifest creation to the helper, guaranteeing exports always receive continuity metadata.
- Provider directories ship with `.gitkeep` files so Git tracks the paths and the verifier can assert their presence.

## Export Manifest — Continuity Block
`build_manifest()` appends:
```json
"continuity": {
  "version": "v1.1.5a",
  "brains": "docs/brains/brains_v1.1.5a.md",
  "patch_notes": "docs/PATCH_NOTES/v1.1.5a.txt",
  "ai_handoff_bridge": "docs/brains/ai_handoff.md",
  "index": "docs/brains/brains_INDEX.md",
  "provider_directories": [
    "data/providers/mast",
    "data/providers/eso",
    "data/providers/simbad",
    "data/providers/nist"
  ]
}
```
Every consumer must preserve these paths when re-serializing exports.

## Verification & Automation
- `RUN_CMDS/Verify-Project.ps1` now checks for the continuity files, validates the brains ↔ patch notes cross-links, and asserts provider directories exist.
- New pytest coverage exercises `get_continuity_links()` and `build_manifest()` to fail the build if references are removed or renamed.
- Keep `docs/brains/brains_INDEX.md` aligned with the current version; automation reads it to confirm coverage.

## Runbook (Windows)
```
C:\\Code\\spectra-app\\RUN_CMDS\\Verify-Project.ps1
C:\\Code\\spectra-app\\RUN_CMDS\\Verify-UI-Contract.ps1
pytest
```
Optional smoke:
```
python scripts\\fetch_samples.py
```

## Risks & Mitigations
- **Docs drift**: solve by editing brains + patch notes together and running the verifier/tests locally.
- **Provider caches deleted**: keep `.gitkeep` files and run the verifier in CI.
- **Manifest consumers ignore continuity block**: document the field in patch notes and UI release notes; tests enforce presence on export.

## Backlog
- Author `AI_HANDOFF_PROMPT_v1.1.5a.md` reflecting the new manifest contract.
- Expand provider directories with real cache recipes/examples.
- Extend the continuity table to surface patch dependencies automatically (scripted generation).
