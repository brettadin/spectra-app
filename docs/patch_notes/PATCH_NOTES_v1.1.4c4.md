# PATCH_NOTES_v1.1.4c4 — Fix app_patched.py indentation & guard
Date (UTC): 2025-09-20T01:30:28.550505Z

## Summary
- Replace `app/app_patched.py` with a clean, **indented correctly** safe entry.
- Keeps the import guard behavior: logs import failures to `logs/ui_debug.log` and surfaces a friendly Streamlit error.
- No changes to `app_merged.py` or other modules.

## Why
The previous import-guard insertion left a malformed `try:` block, causing:
```
IndentationError: expected an indented block after 'try'
```
Streamlit aborted before any UI could render, and no log was written.

## Verification
1. Apply this patch: `RUN_CMDS/Apply-v1.1.4c4-Fix-AppPatched.ps1`
2. Start the app: `RUN_CMDS/Start-Spectra-Patched.ps1`
3. If import succeeds, full UI appears. If it fails, check `logs/ui_debug.log` and read the on-screen traceback.
