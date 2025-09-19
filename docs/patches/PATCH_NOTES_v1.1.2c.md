# PATCH_NOTES_v1.1.2c — Final Pre-Handoff Prep
Date: 2025-09-19T20:49:35Z

## Summary
- Version bumped to v1.1.2c; version badge and watermark already wired in UI/exports.
- Dual-location patch notes policy reinforced: short log at root, longform here.
- Runners stabilized: Start-Spectra.ps1, Clean-Install.ps1, Verify-Project.ps1, start_spectra.cmd.
- Handoff and brains continuity: added v1.1.2c-specific files and guidance.

## Contents changed
- `app/version.json`
- `PATCHLOG.txt` (append this entry)
- `docs/patches/PATCH_NOTES_v1.1.2c.md`
- `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.2c.txt`
- `docs/brains/v1.1.2c brains.txt`
- `RUN_CMDS/Verify-Project.ps1` (stricter checks)

## Verification
```powershell
cd C:\Code\spectra-app
# Version should print v1.1.2c
.\.venv\Scripts\python -m scripts.print_version

# Validate structure (includes brains + ai_handoff check)
.\RUN_CMDS\Verify-Project.ps1

# Launch UI and export a PNG to see the version watermark
.\RUN_CMDS\Start-Spectra.ps1
```
