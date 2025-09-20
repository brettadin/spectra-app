# PATCH_NOTES_v1.1.4c8

Date (UTC): 2025-09-20T01:53:18Z

## Summary
Stabilize starting the UI after recent merges by introducing **EntryHunter**, a dispatcher that calls the right entry function from `app.app_merged` and leaves breadcrumbs in `logs/ui_debug.log`. We removed the `runpy` fallback to avoid `sys.modules` warnings.

## Added
- `app/app_patched.py`: EntryHunter dispatcher.
- Logging to `logs/ui_debug.log`.
- `RUN_CMDS/Apply-v1.1.4c8-EntryHunter.ps1` one-step patch applier.

## Changed
- `app/version.json` to v1.1.4c8.

## How to apply
1. Unzip over `C:\Code\spectra-app\`.
2. Run: `RUN_CMDS\Apply-v1.1.4c8-EntryHunter.ps1`
3. Start: `RUN_CMDS\Start-Spectra-Patched.ps1`

## Env knobs
- `SPECTRA_APP_ENTRY`: set to your entry function name to bypass guessing.

## Known issues
- If `app_merged` builds the UI purely via side-effects with no callable, EntryHunter will show a stub message. In that case define a small `def main(): ...` and we’ll lock to it in v1.1.4c9.
