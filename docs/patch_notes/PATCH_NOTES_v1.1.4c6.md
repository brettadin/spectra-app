# PATCH_NOTES_v1.1.4c6 — Run app_merged as __main__
Date (UTC): 2025-09-20T01:39:16.600186Z

## Summary
- Update `app/app_patched.py` to execute `app.app_merged` **as a script** using `runpy.run_module(..., run_name="__main__")`.
- Ensures code guarded by `if __name__ == "__main__":` runs, which avoids a blank UI when the module only renders under that guard.
- Still logs to `logs/ui_debug.log` and shows an in-UI error with traceback on failure.

## Verification
1. Apply script: `RUN_CMDS/Apply-v1.1.4c6-RunAsMain.ps1`
2. Start app: `RUN_CMDS/Start-Spectra-Patched.ps1`
3. `logs/ui_debug.log` should contain `=== BOOT:` and then `=== RUN_OK:` if the page rendered successfully.
