# PATCH_NOTES_v1.1.4c3 — ImportGuard
Date (UTC): 2025-09-20T01:24:22.883585Z

Adds an idempotent import guard to app/app_patched.py that logs import failures for app.app_merged to logs/ui_debug.log and surfaces the traceback in the UI.
