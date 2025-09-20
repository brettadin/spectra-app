
# Apply-v1.1.4c4-Fix-AppPatched.ps1
Param()

$ErrorActionPreference = "Stop"
$root    = "C:\Code\spectra-app"
$target  = Join-Path $root "app\app_patched.py"
$backup  = "$target.bak.v1.1.4c4"

if (!(Test-Path $target)) { throw "Target not found: $target" }
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $target -Destination $backup -Force }

$body = @'
# app/app_patched.py — v1.1.4c4 (v1.1.4 line)
# Minimal, safe entry that loads the full UI from app.app_merged.
# If import fails, write a traceback to logs/ui_debug.log and surface the error in Streamlit.

import importlib
import os
import traceback
import datetime
import io
import streamlit as st  # streamlit context is available under Streamlit runtime

def _run():
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "ui_debug.log")

    try:
        m = importlib.import_module("app.app_merged")
        importlib.reload(m)  # ensure fresh each rerun
    except Exception:
        # persist traceback to file
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("=== IMPORT FAILURE: " + datetime.datetime.utcnow().isoformat() + "Z ===\n")
            traceback.print_exc(file=f)
            f.write("\n\n")
        # show friendly UI error with traceback
        st.error(f"Import failure while loading UI module. See log: {log_path}")
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        with st.expander("Show traceback"):
            st.code(buf.getvalue())
        # re-raise to keep Streamlit error state consistent
        raise

_run()

'@

Set-Content -LiteralPath $target -Value $body -Encoding UTF8 -NoNewline
Write-Host "Replaced app_patched.py with v1.1.4c4 safe entry (backup at $backup)"

# Purge caches so the new entry is compiled fresh
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
