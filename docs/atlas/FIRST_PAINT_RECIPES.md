# FIRST_PAINT_RECIPES (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:37:40Z  
**Author:** v1.1.4

## Minimal banner
- Title `Spectra`.
- Top-right badge reading `app/version.json`.
- A caption like “Booting UI…” so the app never appears frozen.

## Why first paint matters
- Streamlit’s import/execute cycle can swallow exceptions early; users seeing a banner confirms the runner engaged and the UI didn’t die silently.
- It gives room for slow modules to load without a blank page.
