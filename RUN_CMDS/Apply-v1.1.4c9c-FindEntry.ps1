# Apply-v1.1.4c9c-FindEntry.ps1
# Robust SmartEntry that hunts for a real UI entrypoint and shows a version badge.
$ErrorActionPreference = 'Stop'

function NowUtc { (Get-Date).ToUniversalTime().ToString('s') + 'Z' }

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Resolve-Path (Join-Path $here '..') | Select-Object -ExpandProperty Path
$log  = Join-Path $proj 'logs\ui_debug.log'
$py   = Join-Path $proj 'app\app_patched.py'
$bak  = "$py.bak.v1.1.4c9c"

New-Item (Split-Path $log) -ItemType Directory -Force | Out-Null
"$(NowUtc) Applying v1.1.4c9c FindEntry" | Add-Content $log

Copy-Item $py $bak -Force

$smart = @'
# --- v1.1.4c9c SmartEntry (finder) ---
import importlib, inspect, os, pkgutil, runpy, sys, traceback, types, json, pathlib
from typing import List
LOG = pathlib.Path(__file__).resolve().parents[1] / "logs" / "ui_debug.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

def _ts(): 
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _log(line: str):
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{_ts()} {line}\n")
    except Exception:
        pass

def _list_callables(mod: types.ModuleType) -> List[str]:
    try:
        out = []
        for name, obj in vars(mod).items():
            if name.startswith("_"):
                continue
            if callable(obj):
                out.append(name)
        return sorted(out)
    except Exception as e:
        _log(f"LIST_CALLABLES_ERR: {e!r}")
        return []

def _try_call(mod, fn_name):
    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        return False
    try:
        _log(f"TRY_ENTRY {mod.__name__}.{fn_name}()")
        fn()
        _log(f"TRY_ENTRY_OK {mod.__name__}.{fn_name}()")
        return True
    except SystemExit as se:
        _log(f"TRY_ENTRY_SYS_EXIT {mod.__name__}.{fn_name} code={getattr(se, 'code', None)}")
        return True
    except Exception:
        _log(f"TRY_ENTRY_ERR {mod.__name__}.{fn_name} traceback:\n{traceback.format_exc()}")
        return False

def _version_str():
    # best-effort read of app/version.json
    try:
        ver = (pathlib.Path(__file__).resolve().parents[1] / "app" / "version.json")
        if ver.exists():
            data = json.loads(ver.read_text(encoding="utf-8"))
            return f"{data.get('version','')} · {data.get('built','')}"
    except Exception as e:
        _log(f"VERSION_READ_ERR: {e!r}")
    return ""

def _badge():
    try:
        import streamlit as st
        v = _version_str()
        tag = os.environ.get("SPECTRA_BADGE_TAG", "")
        text = ("v" + tag if tag else "") or v or "Spectra"
        if text:
            st.markdown(
                f"<div style='position:fixed;right:.75rem;bottom:.5rem;opacity:.75;font-size:.75rem;"
                f"padding:.25rem .5rem;border-radius:.4rem;background:#21323f;color:#dbe7f3'>"
                f"{text} dispatcher</div>", unsafe_allow_html=True
            )
    except Exception as e:
        _log(f"BADGE_ERR: {e!r}")

def _info_panel(msg: str):
    try:
        import streamlit as st
        st.markdown(
            f"<div style='margin:2rem auto;max-width:820px'>"
            f"<div style='background:#163447;border:1px solid #24485e;padding:1rem;"
            f"border-radius:.5rem;color:#cfe6f3'>{msg}</div></div>",
            unsafe_allow_html=True
        )
    except Exception as e:
        _log(f"PANEL_ERR: {e!r}")

def _run_module_as_main(modname: str):
    _log(f"RUN_MODULE_AS_MAIN {modname}")
    runpy.run_module(modname, run_name="__main__")

def _hunt_modules():
    # Order matters: most-likely first
    seeds = [
        "app.app_merged",
        "app.app",
        "app.ui.entry",
        "app.ui.app",
        "app.ui.overlay",
        "app.main",
        "app.ui",
    ]
    for name in seeds:
        try:
            m = importlib.import_module(name)
            yield m
        except Exception:
            _log(f"IMPORT_ERR {name}: {traceback.format_exc().splitlines()[-1] if True else ''}")
    # Broad scan of app.* for other potential UIs
    try:
        import app as pkg
        for modinfo in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            name = modinfo.name
            # keep it reasonable; skip obvious heavy/serverside or tests
            if any(s in name for s in (".server", ".fetcher", ".models", ".tests")):
                continue
            try:
                m = importlib.import_module(name)
                yield m
            except Exception:
                _log(f"IMPORT_SCAN_ERR {name}")
    except Exception as e:
        _log(f"PKG_SCAN_ERR: {e!r}")

def _main():
    _log("SmartEntry boot")
    _badge()

    # 1) Explicit "module:function" target takes precedence
    target = os.environ.get("SPECTRA_APP_TARGET", "").strip()
    if target and ":" in target:
        modname, fn = target.split(":", 1)
        try:
            m = importlib.import_module(modname)
            if _try_call(m, fn):
                return
        except Exception:
            _log(f"EXPLICIT_TARGET_ERR {target}: {traceback.format_exc()}")
        _info_panel(f"No luck calling <code>{target}</code>. See ui_debug.log.")
        return

    # 2) Function name via SPECTRA_APP_ENTRY on common modules
    env_entry = os.environ.get("SPECTRA_APP_ENTRY", "").strip()
    if env_entry:
        for m in _hunt_modules():
            if _try_call(m, env_entry):
                return
        _log(f"SPECTRA_APP_ENTRY={env_entry} not found/callable on scanned modules")

    # 3) Heuristic hunt across likely modules and function names
    candidates = ("render","main","app","run","start","entry","render_app","spectra_app","ui")
    tried_any = False
    for m in _hunt_modules():
        exports = _list_callables(m)
        if not exports:
            continue
        _log(f"EXPORTS {m.__name__} -> {exports}")
        for fn in candidates:
            if fn in exports:
                tried_any = True
                if _try_call(m, fn):
                    return

    # 4) Last resort: run app.app_merged as script
    if not tried_any:
        _log("NO_EXPLICIT_ENTRY -> fallback to run_module")
        _info_panel("No UI entrypoint detected yet. Loader is running module fallback…")
    _run_module_as_main("app.app_merged")

if __name__ == "__main__":
    _main()
# --- end SmartEntry ---
'@

Set-Content -LiteralPath $py -Value $smart -Encoding UTF8

# Clean caches
Get-ChildItem -Path $proj -Recurse -Directory -Filter '__pycache__' |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

"$(NowUtc) Installed v1.1.4c9c SmartEntry (backup at $bak)" | Add-Content $log
Write-Host "Installed v1.1.4c9c SmartEntry (backup at $bak)."
