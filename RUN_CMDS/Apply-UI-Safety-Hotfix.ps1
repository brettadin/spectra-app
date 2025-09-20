# Apply-UI-Safety-Hotfix.ps1 — v1.1.4
Param()

$ErrorActionPreference = "Stop"
$root = "C:\Code\spectra-app"

# Write guarded entry
$appPatched = Join-Path $root "app\app_patched.py"
Set-Content -LiteralPath $appPatched -Value @'
# app/app_patched.py — v1.1.4 UI safety loader
# Imports the full UI and surfaces exceptions as visible error panels instead of a blank page.

import streamlit as st

try:
    # Importing main builds the entire UI.
    from app.ui import main as _spectra_ui_main  # noqa: F401
except Exception as e:
    st.error("The UI crashed during render. See details below.")
    st.exception(e)
    st.stop()

'@ -Encoding UTF8 -NoNewline
Write-Host "Patched guarded entry: $appPatched"

# Write safe helpers
$safePy = Join-Path $root "app\ui\safe.py"
Set-Content -LiteralPath $safePy -Value @'
# app/ui/safe.py — v1.1.4
from pathlib import Path
import streamlit as st

def safe_ingest(func, *args, **kwargs):
    """Run an ingest call and surface any error instead of letting the page blank."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error("Example ingest failed.")
        st.exception(e)
        st.stop()

def safe_read_text(p: Path):
    """Read text safely; try utf-8, then latin-1. Raise FileNotFoundError for clear messaging."""
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1")

def read_version_caption(version_json_path: Path):
    """Read version.json and return a one-line caption string."""
    import json
    try:
        v = json.loads(version_json_path.read_text(encoding="utf-8")).get("version", "v?")
    except Exception:
        v = "v?"
    return f"Build: {v} — Idempotent unit toggling; CSV ingest hardening; duplicate scope+override; version badge; provenance drawer."

'@ -Encoding UTF8 -NoNewline
Write-Host "Added helpers: $safePy"

# Purge bytecode so Streamlit reloads modules
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"

Write-Host "UI Safety Hotfix applied."
