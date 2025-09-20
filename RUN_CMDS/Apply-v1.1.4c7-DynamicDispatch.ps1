
# Apply-v1.1.4c7-DynamicDispatch.ps1
Param()

$ErrorActionPreference = "Stop"
$root    = "C:\Code\spectra-app"
$target  = Join-Path $root "app\app_patched.py"
$backup  = "$target.bak.v1.1.4c7"

if (!(Test-Path $target)) { throw "Target not found: $target" }
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $target -Destination $backup -Force }

$body = @'
# app/app_patched.py — v1.1.4c7 (v1.1.4 line)
# Dynamic dispatcher: try common entrypoints on app.app_merged, then run as __main__.
# Logs everything to logs/ui_debug.log and shows a tiny banner so the page is never 100%% blank.

import os, sys, io, traceback, datetime, importlib, inspect, runpy
import streamlit as st

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "ui_debug.log")

def _log(tag, msg=""):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"=== {tag}: {datetime.datetime.utcnow().isoformat()}Z === {msg}\n")

def _log_exc(tag):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"=== {tag}: {datetime.datetime.utcnow().isoformat()}Z ===\n")
        traceback.print_exc(file=f)
        f.write("\n")

def _banner():
    # unobtrusive debug banner; remove later
    st.markdown(
        "<div style='position:fixed;bottom:6px;right:8px;opacity:.5;font-size:11px;'>"
        "v1.1.4c7 dispatcher active</div>",
        unsafe_allow_html=True,
    )

def _call_if_callable(fn):
    try:
        if fn is None:
            return False
        sig = None
        try:
            sig = inspect.signature(fn)
        except Exception:
            sig = None
        if sig and len(sig.parameters) == 0:
            fn()
            return True
        elif sig and len(sig.parameters) == 1:
            # pass Streamlit as a convenience
            fn(st)
            return True
        else:
            # try without args
            fn()
            return True
    except BaseException:
        _log_exc("ENTRY_CALL_FAIL")
        st.error(f"Entry function raised an exception. See log: {LOG_PATH}")
        with st.expander("Show traceback"):
            buf = io.StringIO()
            traceback.print_exc(file=buf)
            st.code(buf.getvalue())
        raise
    return False

def _run():
    _log("BOOT")
    _banner()

    # 1) Import module
    try:
        m = importlib.import_module("app.app_merged")
        importlib.reload(m)
        _log("IMPORTED", repr(m))
    except BaseException:
        _log_exc("IMPORT_FAIL")
        st.error(f"Import failure while loading UI module. See log: {LOG_PATH}")
        with st.expander("Show traceback"):
            buf = io.StringIO(); traceback.print_exc(file=buf); st.code(buf.getvalue())
        raise

    # 2) Try common entrypoint names
    tried = []
    for name in ["main", "render", "run", "app", "ui"]:
        fn = getattr(m, name, None)
        if callable(fn):
            tried.append(name)
            _log("TRY_ENTRY", name)
            if _call_if_callable(fn):
                _log("ENTRY_OK", name)

    # 3) Try App class with render()
    App = getattr(m, "App", None)
    if inspect.isclass(App):
        tried.append("App.render")
        try:
            inst = App()
            if hasattr(inst, "render") and callable(inst.render):
                _log("TRY_ENTRY", "App.render")
                _call_if_callable(inst.render)
                _log("ENTRY_OK", "App.render")
        except BaseException:
            _log_exc("APPCLASS_FAIL")
            st.error(f"App class failed to render. See log: {LOG_PATH}")
            with st.expander("Show traceback"):
                buf = io.StringIO(); traceback.print_exc(file=buf); st.code(buf.getvalue())
            raise

    # 4) Finally, run module as __main__ (to trigger if __name__ == "__main__")
    try:
        _log("RUN_AS_MAIN")
        runpy.run_module("app.app_merged", run_name="__main__")
        _log("RUN_AS_MAIN_OK")
    except BaseException:
        _log_exc("RUN_AS_MAIN_FAIL")
        st.error(f"Failure while executing UI script. See log: {LOG_PATH}")
        with st.expander("Show traceback"):
            buf = io.StringIO(); traceback.print_exc(file=buf); st.code(buf.getvalue())
        raise

_run()

'@

Set-Content -LiteralPath $target -Value $body -Encoding UTF8 -NoNewline
Write-Host "Replaced app_patched.py with v1.1.4c7 dynamic dispatcher (backup at $backup)"

# Purge caches to force fresh compile
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
