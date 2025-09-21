# 01_ARCHITECTURE_OVERVIEW (v1.1.4x)

**Goal:** describe the moving parts and who calls whom. Keep this file short and stable.

## Layers
- **Runner**: `app/app_patched.py` (small, logs, delegates)
- **UI Root**: `app/app_merged.py` exporting a callable (ideally `render()`)
- **UI Pages**: `app/ui/*` (entry, main, docs, examples, widgets)
- **Utils**: `app/utils/*` (provenance shim kept tiny)
- **Server**: `app/server/*` (provenance merger, models, future fetchers)
- **Launchers**: `RUN_CMDS/*.ps1` (idempotent, compatible with restricted policies)
- **Docs**: `docs/*` (brains, atlas, patch notes)
- **Logs**: `logs/ui_debug.log` (single pane of truth for UI dispatcher)

## Invariants
1. One callable entry (render) exists and is invoked by the runner.
2. First paint always happens; badge is always visible.
3. Handlers never blank the page; they render errors inline.
4. Scripts are idempotent and log one line per run.
5. Provenance is centralized in `server/provenance.py`.
