# PATCH_NOTES_v1.1.2c — Final Ship Prep
[NOTE] This file is UTF-8 encoded. If PowerShell shows weird characters, it's a font issue.

Date: 2025-09-19T21:02:14Z

## Summary
- Repo finalized for shipping handoff.
- All docs normalized to UTF-8, no curly quotes/dash corruption.
- Root PATCHLOG.txt clarified as append-only mirror of docs/patches notes.
- Updated AI handoff prompt with clear rules and roadmap.
- Brains notes expanded with "state of repo" and do/don't lessons.

## Contents changed
- `app/version.json`
- `PATCHLOG.txt` (root short log)
- `docs/patches/PATCH_NOTES_v1.1.2c.md`
- `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.2c.txt`
- `docs/brains/v1.1.2c brains.txt`
- `RUN_CMDS/Verify-Project.ps1` (UTF-8 safe)

## Verification
```powershell
cd C:\Code\spectra-app
.\RUN_CMDS\Verify-Project.ps1
.\.venv\Scripts\python -m scripts.print_version   # expect v1.1.2c
.\RUN_CMDS\Start-Spectra.ps1                       # UI badge + export watermark
```

## Next Steps
- v1.1.3 should implement archive fetchers (MAST, ESO, SDSS, Simbad, IACOB, exoplanet archive).
- Enforce SHA-256 dedupe for uploads.
- Build dual-panel/offset-baseline overlays for emission+absorption.
- Unit toggles nm|Å|µm|cm⁻¹ with manifest logging.
- Differential workspace with alignment/normalization residuals.
- Add blackbody + line-list models with provenance.

