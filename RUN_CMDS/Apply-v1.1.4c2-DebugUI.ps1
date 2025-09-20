
# Apply-v1.1.4c2-DebugUI.ps1
Param()

$ErrorActionPreference = "Stop"
$root   = "C:\Code\spectra-app"
$target = Join-Path $root "app\app_merged.py"
$backup = "$target.bak.v1.1.4c2"

if (!(Test-Path $target)) { throw "Target not found: $target" }
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $target -Destination $backup -Force }

$txt = Get-Content -LiteralPath $target -Raw -Encoding UTF8

# Remove any previous v1.1.4c2 debug wrapper then insert ours
$pattern = '(?s)# ===== v1\.1\.4c2 UI DEBUG WRAPPER .*?===== end debug wrapper ====='
if ([Text.RegularExpressions.Regex]::IsMatch($txt, $pattern)) {
    $txt = [Text.RegularExpressions.Regex]::Replace($txt, $pattern, '')
}

# Find first import block end (block of consecutive import/from lines)
$match = [Text.RegularExpressions.Regex]::Match($txt, '(?ms)^(?:from\s+\S+\s+import\s+.*\n|import\s+\S+.*\n)+')
if ($match.Success) {
    $idx = $match.Index + $match.Length
    $txt = $txt.Insert($idx, "`r`n" + @'

# ===== v1.1.4c2 UI DEBUG WRAPPER (auto-insert) =====
# Catches exceptions during the main render and writes a full traceback
# to logs/ui_debug.log, then shows a friendly error in the Streamlit UI.
import os, traceback, datetime
try:
    import streamlit as st
except Exception:
    st = None

_log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "ui_debug.log")

def _write_log(exc):
    with open(_log_path, "a", encoding="utf8") as _f:
        _f.write("=== UI DEBUG TRACE: " + datetime.datetime.utcnow().isoformat() + " ===\n")
        traceback.print_exc(file=_f)
        _f.write("\n\n")

def _safe_run(fn):
    try:
        fn()
    except Exception as e:
        _write_log(e)
        try:
            if st is not None:
                st.error("UI crashed during render. A diagnostic traceback was written to: " + _log_path)
                with st.expander("Show last traceback (truncated):"):
                    with open(_log_path, "r", encoding="utf8") as _f:
                        data = _f.read()
                        st.code(data[-10000:])
        except Exception:
            pass

try:
    if "main" in globals() and callable(globals().get("main")):
        _orig_main = globals().get("main")
        globals()["main"] = lambda : _safe_run(_orig_main)
except Exception:
    pass
# ===== end debug wrapper =====

'@ + "`r`n")
} else {
    $txt = $txt.TrimEnd() + "`r`n`r`n" + @'

# ===== v1.1.4c2 UI DEBUG WRAPPER (auto-insert) =====
# Catches exceptions during the main render and writes a full traceback
# to logs/ui_debug.log, then shows a friendly error in the Streamlit UI.
import os, traceback, datetime
try:
    import streamlit as st
except Exception:
    st = None

_log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "ui_debug.log")

def _write_log(exc):
    with open(_log_path, "a", encoding="utf8") as _f:
        _f.write("=== UI DEBUG TRACE: " + datetime.datetime.utcnow().isoformat() + " ===\n")
        traceback.print_exc(file=_f)
        _f.write("\n\n")

def _safe_run(fn):
    try:
        fn()
    except Exception as e:
        _write_log(e)
        try:
            if st is not None:
                st.error("UI crashed during render. A diagnostic traceback was written to: " + _log_path)
                with st.expander("Show last traceback (truncated):"):
                    with open(_log_path, "r", encoding="utf8") as _f:
                        data = _f.read()
                        st.code(data[-10000:])
        except Exception:
            pass

try:
    if "main" in globals() and callable(globals().get("main")):
        _orig_main = globals().get("main")
        globals()["main"] = lambda : _safe_run(_orig_main)
except Exception:
    pass
# ===== end debug wrapper =====

'@
}

Set-Content -LiteralPath $target -Value $txt -Encoding UTF8 -NoNewline
Write-Host "Injected v1.1.4c2 debug wrapper into $target (backup at $backup)"

Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
