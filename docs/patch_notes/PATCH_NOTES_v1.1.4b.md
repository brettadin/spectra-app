# PATCH_NOTES_v1.1.4b
Date (UTC): 2025-09-20T00:44:16.152423Z

## Summary
- Restore full UI by pointing entry to the feature‑complete module `app.app_merged`.
- Adds safe reload wrapper so interaction errors render visibly instead of blanking the page.
- No changes to data logic or utils. Provenance shim remains in place.

## Why
A nested-folder import overwrote the streamlined entry to point at a thin `app.ui.main` that lacked:
- Sidebar controls (Display mode, Display units, Duplicate scope)
- Functional Differential UI
- Provenance/session logs expander
- Stable example ingest guards

`app.app_merged` already contains the canonical v1.1.3e UI contract and works with existing utils in v1.1.4b.

## Files touched
- `app/app_patched.py` (replace): safe loader importing `app.app_merged`

## Verification
1. Purge bytecode:
   ```powershell
   Get-ChildItem -Path 'C:\Code\spectra-app' -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
   ```
2. Start app:
   ```powershell
   C:\Code\spectra-app\RUN_CMDS\Start-Spectra-Patched.ps1
   ```
3. Confirm:
   - Sidebar shows Examples, Display mode, Display units, Duplicate scope, Export.
   - Overlay: uploader, duplicate banner with “Ingest anyway”, plot, provenance/session logs.
   - Differential: Trace A/B selects, operation, normalization, resample slider, compute + result trace.
   - Docs: markdown viewer renders files without blanking.

## Known issues
- This patch changes only the entry module. The new server fetchers remain stubs pending SDK wiring.
