# PATCH_NOTES_v1.1.4c7 — Dynamic dispatcher
Date (UTC): 2025-09-20T01:42:34.551104Z

## Summary
- Update `app/app_patched.py` with a dispatcher that:
  1. Imports `app.app_merged`.
  2. Tries `main`, `render`, `run`, `app`, `ui` functions.
  3. Tries `App.render()` if an `App` class exists.
  4. Runs the module as `__main__`.
- Writes detailed logs to `logs/ui_debug.log` for each step.
- Adds a tiny footer banner so the UI is never visually empty while we test.

## Verification
1. Apply the script `RUN_CMDS/Apply-v1.1.4c7-DynamicDispatch.ps1`.
2. Start the app; UI should now render or at least show the footer banner.
3. If it still blanks, `logs/ui_debug.log` will show which entrypoints were tried and which succeeded/failed.
