# ENTRY_VERIFICATION_CHECKLIST (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:37:40Z  
**Author:** v1.1.4

- [ ] `app/app_merged.py` exports `render()` (verify from Python: list(callables)).
- [ ] The runner logs BOOT → IMPORT → EXPORTS → TRY_ENTRY_OK.
- [ ] Badge text equals `app/version.json`.
- [ ] Docs/Examples errors show inline, not as a blank page.
- [ ] Switching dedupe scope triggers a repaint and does not nuke the frame.
- [ ] `RUN_CMDS` scripts never use features missing on older PowerShell (e.g., `-AsUTC`).
