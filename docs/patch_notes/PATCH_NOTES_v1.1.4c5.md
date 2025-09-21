# PATCH_NOTES_v1.1.4c5 — StrongGuard entry
Date (UTC): 2025-09-20T01:33:40.776519Z

## Summary
- Replace `app/app_patched.py` with a hardened entry that **always** writes to `logs/ui_debug.log`:
  - Catches **BaseException** (including `SystemExit`, `KeyboardInterrupt`, `SyntaxError`).
  - Installs a global `sys.excepthook` and wraps `sys.exit` to log before termination.
  - Logs a **BOOT marker** so we can confirm execution even if nothing else happens.
  - Calls `app.app_merged.main()` if present and logs any runtime failures.
  - Shows an in-UI error panel with traceback.

## Verification
1. Apply script: `RUN_CMDS/Apply-v1.1.4c5-StrongGuard.ps1`
2. Start app: `RUN_CMDS/Start-Spectra-Patched.ps1`
3. Check for `logs/ui_debug.log`. It should at least contain a `=== BOOT:` line.
