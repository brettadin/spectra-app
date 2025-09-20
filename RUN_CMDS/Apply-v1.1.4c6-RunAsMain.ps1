
# Apply-v1.1.4c6-RunAsMain.ps1
Param()

$ErrorActionPreference = "Stop"
$root    = "C:\Code\spectra-app"
$target  = Join-Path $root "app\app_patched.py"
$backup  = "$target.bak.v1.1.4c6"

if (!(Test-Path $target)) { throw "Target not found: $target" }
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $target -Destination $backup -Force }

$body = @'
# app/app_patched.py — v1.1.4c6 (v1.1.4 line)
# Execute the full UI module *as a script* so code under __name__ == "__main__" runs.
# Log any failure to logs/ui_debug.log and surface an error in the UI.

import os, sys, io, traceback, datetime, runpy
import streamlit as st

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "ui_debug.log")

def _log(tag):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"=== {tag}: {datetime.datetime.utcnow().isoformat()}Z ===\n")

def _log_exc(tag):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"=== {tag}: {datetime.datetime.utcnow().isoformat()}Z ===\n")
        traceback.print_exc(file=f)
        f.write("\n")

def _show_error(msg):
    st.error(f"{msg}. See log: {LOG_PATH}")
    buf = io.StringIO()
    traceback.print_exc(file=buf)
    with st.expander("Show traceback"):
        st.code(buf.getvalue())

def _run():
    _log("BOOT")
    try:
        # Run the UI module as if it were the main Streamlit script.
        runpy.run_module("app.app_merged", run_name="__main__")
        _log("RUN_OK")
    except BaseException:
        _log_exc("RUN_FAIL")
        _show_error("Failure while executing UI script")
        raise

_run()

'@

Set-Content -LiteralPath $target -Value $body -Encoding UTF8 -NoNewline
Write-Host "Replaced app_patched.py with v1.1.4c6 (run as __main__) (backup at $backup)"

# Purge caches to force fresh compile
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
