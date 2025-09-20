
$ErrorActionPreference = 'Stop'

$proj = Split-Path -Parent $PSScriptRoot
$py   = Join-Path $proj 'app\app_patched.py'
$bak  = "$py.bak.v1.1.4c9c"

# timestamp helper
function NowUtc() { (Get-Date).ToUniversalTime().ToString("s") + "Z" }

$log = Join-Path $proj 'logs\ui_debug.log'
New-Item (Split-Path $log) -ItemType Directory -Force | Out-Null

"$(NowUtc) Applying v1.1.4c9c EntryFix" | Add-Content $log

Copy-Item $py $bak -Force

$smart = @'
# --- v1.1.4c9c SmartEntry ---
import importlib, runpy, os, traceback, types, datetime, pathlib

LOG = pathlib.Path(__file__).resolve().parents[1] / "logs" / "ui_debug.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

def _ts(): return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _log(msg):
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{_ts()} {msg}\n")
    except Exception: pass

def _list_callables(mod):
    return [n for n,o in vars(mod).items() if callable(o) and not n.startswith("_")]

def _try(mod, fn):
    func = getattr(mod, fn, None)
    if callable(func):
        try:
            _log(f"TRY {fn}()")
            func()
            _log(f"OK {fn}()")
            return True
        except SystemExit as se:
            _log(f"EXIT {fn} code={getattr(se, 'code', None)}")
            return True
        except Exception:
            _log(f"ERR {fn}: {traceback.format_exc()}")
    return False

def main():
    _log("SmartEntry boot")
    modname = "app.app_merged"
    m = importlib.import_module(modname)

    env = os.environ.get("SPECTRA_APP_ENTRY")
    if env:
        _log(f"ENV SPECTRA_APP_ENTRY={env}")
        if _try(m, env): return

    candidates = ["render","main","app","ui","entry"]
    exports = _list_callables(m)
    _log(f"EXPORTS {exports}")

    for fn in candidates:
        if fn in exports and _try(m, fn): return

    _log("FALLBACK run_module")
    runpy.run_module(modname, run_name="__main__")

if __name__ == "__main__":
    main()
# --- end SmartEntry ---
'@

Set-Content -LiteralPath $py -Value $smart -Encoding UTF8

Get-ChildItem -Path $proj -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

"$(NowUtc) Applied v1.1.4c9c EntryFix -> $py (backup: $bak)" | Add-Content $log
