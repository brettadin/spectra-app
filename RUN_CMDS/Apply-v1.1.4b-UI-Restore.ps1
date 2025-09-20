# Apply-v1.1.4b-UI-Restore.ps1
Param()

$ErrorActionPreference = "Stop"
$root = "C:\Code\spectra-app"

# Backup
$target = Join-Path $root "app\app_patched.py"
$backup = "$target.bak.v1.1.4b"
if (Test-Path $target) { Copy-Item -LiteralPath $target -Destination $backup -Force }

# Write new entry
Set-Content -LiteralPath $target -Value @'
# app/app_patched.py — v1.1.4b entry (UI restore)
# Load the full, feature-complete UI from app.app_merged with safety.
import streamlit as st
import importlib

def _run():
    try:
        m = importlib.import_module("app.app_merged")
        importlib.reload(m)  # ensure fresh on each rerun
    except Exception as e:
        st.error("The UI crashed during render.")
        st.exception(e)
        st.stop()

_run()

'@ -Encoding UTF8 -NoNewline
Write-Host "Updated entry -> app.app_merged (safe reload)"

# Drop notes
$notesPath = Join-Path $root "docs\patches\PATCH_NOTES_v1.1.4b.md"
$brainsPath = Join-Path $root "docs\brains\v1.1.4b brains.md"
New-Item -ItemType Directory -Force -Path (Split-Path $notesPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $brainsPath) | Out-Null

Set-Content -LiteralPath $notesPath -Value @'
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

'@ -Encoding UTF8 -NoNewline

Set-Content -LiteralPath $brainsPath -Value @'
# Brains — v1.1.4b: Entry Realignment and UI Restore

**Intent:** Keep the UI contract intact while avoiding refactors during recovery.

**Action:** Point `app/app_patched.py` at `app.app_merged` (the feature‑complete UI) and wrap with a safe reloader so any exceptions render on‑screen.

**Why:** The thin `app.ui.main` in v1.1.4x lacked critical controls after a nested zip overwrite. The merged module already implements:
- Sidebar: Examples, Display mode, Display units, Duplicate scope, Export
- Tabs: Overlay, Differential, Docs
- Provenance/session logs and duplicate ledger
- Example ingest with CSVs

**Repro/verify:** See patch notes v1.1.4b.

**Next:** Once stable, we can gradually port sections back into `app.ui.main` behind parity checks, then flip entry to `app.ui.main` again.

'@ -Encoding UTF8 -NoNewline

# Purge bytecode so reload is guaranteed
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"

Write-Host "Apply complete."
