# PATCH_NOTES v1.1.2b — Versioning & Patch Visibility
Date: 2025-09-19T20:30:37Z

## Summary
- Introduced `app/version.json` and loader `app/_version.py` to centralize versioning.
- Surfaced version and one-line summary in the UI and exports.
- Watermarked Plotly figures with the version string so screenshots are self-identifying.
- Added `scripts/print_version.py` for CI and human sanity.
- Established the dual-location rule for patch notes (root summary + docs/patches longform).

## Verification
```powershell
cd C:\Code\spectra-app
# 1) Version prints
.\.venv\Scripts\python -m scripts.print_version
# 2) Files present
Get-ChildItem -Recurse -Depth 3 -Include version.json, PATCHLOG.txt, PATCH_NOTES_*.md, AI_HANDOFF_PROMPT_*.txt | Select-Object FullName
# 3) UI shows badge, export PNG has version watermark
.\.venv\Scripts\streamlit run app\ui\main.py
```
