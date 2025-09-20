
# Apply-v1.1.4c3-ImportGuard.ps1
Param()

$ErrorActionPreference = "Stop"
$root    = "C:\Code\spectra-app"
$patched = Join-Path $root "app\app_patched.py"
$backup  = "$patched.bak.v1.1.4c3"

if (!(Test-Path $patched)) { throw "Target not found: $patched" }
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $patched -Destination $backup -Force }

# Read file
$txt = Get-Content -LiteralPath $patched -Raw -Encoding UTF8

# Remove any previous 1.1.4c3 guard to stay idempotent
$pattern = '(?s)# ===== v1\.1\.4c3 IMPORT GUARD .*?===== end import guard ====='
if ([Text.RegularExpressions.Regex]::IsMatch($txt, $pattern)) {
  $txt = [Text.RegularExpressions.Regex]::Replace($txt, $pattern, '')
}

# Find the first occurrence of: m = importlib.import_module("app.app_merged")
$needle = 'm = importlib.import_module("app.app_merged")'
$idx = $txt.IndexOf($needle)
if ($idx -ge 0) {
  # Wrap the import in a try/except that logs to logs/ui_debug.log and shows st.error
  $guard = @'
# ===== v1.1.4c3 IMPORT GUARD (auto-insert) =====
import os, traceback, datetime
import streamlit as st
_log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "ui_debug.log")

try:
    m = importlib.import_module("app.app_merged")
except Exception:
    with open(_log_path, "a", encoding="utf8") as _f:
        _f.write("=== IMPORT FAILURE: " + datetime.datetime.utcnow().isoformat() + "Z ===\n")
        traceback.print_exc(file=_f)
        _f.write("\n\n")
    st.error(f"Import failure while loading app_merged. See log: {_log_path}")
    with st.expander("Show import traceback"):
        import io, sys
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        st.code(buf.getvalue())
    raise
# ===== end import guard =====
'@

  # Replace the single line import with the block
  $txt = $txt.Substring(0, $idx) + $guard + $txt.Substring($idx + $needle.Length)
}
else {
  # Fallback: just prepend the guard at the start if pattern not found
  $guard2 = @'
# ===== v1.1.4c3 IMPORT GUARD (auto-insert) =====
import os, traceback, datetime, importlib
import streamlit as st
_log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "ui_debug.log")

try:
    m = importlib.import_module("app.app_merged")
except Exception:
    with open(_log_path, "a", encoding="utf8") as _f:
        _f.write("=== IMPORT FAILURE (fallback): " + datetime.datetime.utcnow().isoformat() + "Z ===\n")
        traceback.print_exc(file=_f)
        _f.write("\n\n")
    st.error(f"Import failure while loading app_merged. See log: {_log_path}")
    with st.expander("Show import traceback"):
        import io
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        st.code(buf.getvalue())
    raise
# ===== end import guard =====
'@
  $txt = $guard2 + "`r`n" + $txt
}

# Save
Set-Content -LiteralPath $patched -Value $txt -Encoding UTF8 -NoNewline
Write-Host "Applied v1.1.4c3 ImportGuard to $patched (backup at $backup)"

# Purge caches
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
