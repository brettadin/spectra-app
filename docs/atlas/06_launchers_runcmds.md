# Spectra Atlas Foundation — 06 Launchers & RUN_CMDS Scripts

This document details the **launcher scripts** (mostly PowerShell `.ps1` files under `RUN_CMDS/`) that control how the Spectra App is patched, verified, and started.

---

## Purpose of RUN_CMDS
The `RUN_CMDS/` directory exists as an **operator-facing layer** on Windows to:
- Start the Streamlit app (`Start-Spectra-Patched.ps1`, `Start-Spectra-Merged.ps1`).
- Verify project health (`Verify-Project.ps1`, `Verify-UI-Contract.ps1`).
- Apply patch bundles (`Apply-vX.Y.Z-*.ps1`).
- Purge caches (`Clear-Cache.ps1`).

They act as a **bridge** between raw Python modules and reproducible patch management.

---

## Core Launchers

### `Start-Spectra-Patched.ps1`
- Entrypoint for normal runs.
- Calls into `app/app_patched.py`.
- Purges stale `__pycache__` before start to avoid bytecode conflicts.
- Environment variable `SPECTRA_APP_ENTRY` can override the entry function.

### `Start-Spectra-Merged.ps1`
- Similar to above, but targets `app/app_merged.py`.
- Used for integration testing after patch merges.

### `Verify-Project.ps1`
- Reads `app/version.json` to report the current build number and longform patch notes.
- Confirms consistency of:
  - version file,
  - docs/brains + patch notes,
  - UI contract presence.
- Often used just before handoff.

### `Verify-UI-Contract.ps1`
- Ensures mandatory UI components exist:
  - Sidebar: Examples, Display Mode, Display Units, Duplicate Scope.
  - Tabs: Overlay, Differential, Docs.
  - Version badge visible.
- Prevents regressions where UI elements were dropped during merges.

---

## Patch Application Scripts

Scripts named like `Apply-v1.1.4c5-StrongGuard.ps1`, `Apply-v1.1.4c8-EntryHunter.ps1`:
- Copy prepared Python patch files into `app/`.
- Backup the originals with `.bak.<version>` suffixes.
- Purge `__pycache__` after patching.
- Log the action to `logs/ui_debug.log` (if logging was wired).

**Known issues:**
- Unsigned scripts block execution unless run with `-ExecutionPolicy Bypass`.
- Some scripts accidentally **overwrote files with themselves**, producing IO errors.
- `Get-Date -AsUTC` parameter not supported in older PowerShell → broke patch scripts until replaced with `.ToUniversalTime()`.

---

## Problems Identified

1. **Duplication & Drift**
   - Too many scripts for slightly different patch operations → confusion and stale files.
   - Developers sometimes applied the wrong `Apply-...ps1` leading to missing features or double‑nested folders (`spectra-app\spectra-app`).

2. **ExecutionPolicy**
   - Default Windows PowerShell refused to run unsigned scripts.
   - Workaround: `PowerShell -ExecutionPolicy Bypass -File ...` or `Unblock-File`.

3. **Self-Overwriting**
   - Some patch scripts pointed `Copy-Item` to identical source/dest paths.
   - Result: “Cannot overwrite the item with itself.”

4. **Log Inconsistency**
   - Some scripts appended logs; others did not.
   - Debug logs (`ui_debug.log`) often missing or empty.

5. **SmartEntry & Import Guards**
   - Added progressively to `app_patched.py`.
   - But patch scripts sometimes layered multiple guards → bloat and fragile entry logic.

---

## Rationalization Plan

1. **Keep Only Four Runners**
   - `Start-Spectra.ps1` (normal)
   - `Start-Spectra-Debug.ps1` (with extended logging)
   - `Verify-Project.ps1`
   - `Verify-UI.ps1`

2. **Patch Bundles as Zips**
   - Instead of 10+ Apply scripts, ship one `Apply-Patch.ps1` with version arg:
     ```powershell
     .\Apply-Patch.ps1 -Version v1.1.4c8 -Zip spectra-app_v1.1.4c8.zip
     ```

3. **Centralized Logging**
   - All launchers should write to `logs/ui_debug.log` with UTC stamps.

4. **Clear Environment Handling**
   - Explicit support for `$env:SPECTRA_APP_ENTRY` override.
   - Always print chosen entry to logs.

5. **Signing & Policy**
   - Recommend code‑signing scripts for production use.
   - Or instruct developers to permanently set execution policy for local dev.

---

## Developer Obligations

- Always run `Verify-Project.ps1` after applying a patch.
- Never hand-edit patch scripts → only update via generated zips.
- Document changes in `docs/brains` and patch notes.
- Purge `__pycache__` before each run.

---

## Next Topic

**07 — Data ingestion & parsing (CSV, FITS, TXT)** → will describe header handling, unit detection, error cases, and provenance logging.

