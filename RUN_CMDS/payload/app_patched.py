# SmartEntry dispatcher (v1.1.4c9)
from __future__ import annotations
import os, sys, importlib, runpy, types, traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG = LOG_DIR / "ui_debug.log"

def _log(line: str) -> None:
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            fh.write(f"{ts} {line}\n")
    except Exception:
        pass

def _find_entry(m: types.ModuleType):
    preferred = os.getenv("SPECTRA_APP_ENTRY", "").strip()
    if preferred:
        for name in (preferred, preferred.lower(), preferred.upper()):
            fn = getattr(m, name, None)
            if callable(fn):
                return name, fn
    for name in ("render","main","ui","entry","app","run"):
        fn = getattr(m, name, None)
        if callable(fn):
            return name, fn
    return None, None

def _safe_import(module_name: str) -> types.ModuleType:
    _log(f"IMPORT {module_name}")
    return importlib.import_module(module_name)

def _run_module_as_main(module_name: str):
    _log(f"RUN_MODULE_AS_MAIN {module_name}")
    sys.modules.pop(module_name, None)
    return runpy.run_module(module_name, run_name="__main__", alter_sys=True)

def main():
    _log("=== SmartEntry boot ===")
    mod_name = "app.app_merged"
    try:
        m = _safe_import(mod_name)
        name, fn = _find_entry(m)
        if fn:
            _log(f"CALL {mod_name}.{name}()")
            return fn()
        else:
            _log("NO_EXPLICIT_ENTRY -> fallback to run_module")
            return _run_module_as_main(mod_name)
    except SystemExit as e:
        _log(f"SYSTEM_EXIT {e.code}")
        raise
    except Exception as e:
        _log("EXC " + repr(e))
        traceback.print_exc()
        import streamlit as st
        st.error("SmartEntry failed: " + repr(e))
        st.caption("See logs/ui_debug.log for details.")

if __name__ == "__main__":
    main()
else:
    main()
