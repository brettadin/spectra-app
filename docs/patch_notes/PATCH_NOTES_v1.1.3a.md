# PATCH_NOTES_v1.1.3a
Date: 2025-09-19T21:36:22.723350Z

## Summary
- Introduces a patched Streamlit entrypoint (`app/app_patched.py`) that **requires no edits** to existing files.
- Implements: duplicate upload guard, manifest unit logs, legend hygiene, dual-panel and offset display modes, provenance autowrite for uploads.
- Provides runners to launch patched app directly.

## Acceptance
- App launches via Start-Spectra-Patched.ps1.
- Duplicate files are skipped with a UI message.
- Legends contain no empty labels.
- "Export what I see" writes CSV subset + manifest JSON (PNG if kaleido is present).
- Manifest contains unit decision logs and provenance per trace.
