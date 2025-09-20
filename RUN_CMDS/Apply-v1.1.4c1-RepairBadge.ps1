
# Apply-v1.1.4c1-RepairBadge.ps1
Param()

$ErrorActionPreference = "Stop"
$root   = "C:\Code\spectra-app"
$target = Join-Path $root "app\app_merged.py"
$backup = "$target.bak.v1.1.4c1"

if (!(Test-Path $target)) { throw "Target not found: $target" }
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $target -Destination $backup -Force }

# Load file
$txt = Get-Content -LiteralPath $target -Raw -Encoding UTF8

# 1) If a malformed 'passtry:' token exists, repair it.
$txt = $txt -replace 'passtry:', "pass`r`ntry:"

# 2) Remove any previously injected badge block (by the unique css marker) to avoid duplicates
$pattern = '(?s)from\s+app\._version\s+import\s+get_version_info\s+as\s+_vinfo.*?position:fixed;top:12px;right:28px.*?except\s+Exception:\s*?\n\s*?pass\s*?#?\s*?-{3,}\s*end version badge\s*-{0,}'
$txt = [System.Text.RegularExpressions.Regex]::Replace($txt, $pattern, '', 'IgnoreCase')

# 3) Ensure we have a Streamlit import at the top (do not duplicate)
if ($txt -notmatch '(?m)^\s*import\s+streamlit\s+as\s+st\s*$') {
  $txt = $txt -replace '(?m)^', "import streamlit as st`r`n", 1
}

# 4) Ensure we have a single clean badge injected right after imports.
# We'll place it after the first block of imports.
$importsEnd = [regex]::Match($txt, '(?ms)^(?:from\s+\S+\s+import\s+.*\n|import\s+\S+.*\n)+')
if ($importsEnd.Success) {
  $start = $importsEnd.Index + $importsEnd.Length
  $txt = $txt.Insert($start, "`r`n" + @'
from app._version import get_version_info as _vinfo

# --- version badge (fixed position, non-interactive) ---
try:
    _vi = _vinfo()
    _v_ver = _vi.get("version", "v?")
    _v_dt  = _vi.get("date_utc", "")
    import streamlit as st  # safe if already imported above
    st.markdown(
        f"<div style='position:fixed;top:12px;right:28px;opacity:.85;padding:2px 8px;border:1px solid #444;border-radius:12px;font-size:12px;'>"
        f"{_v_ver} • {_v_dt}"
        "</div>",
        unsafe_allow_html=True,
    )
except Exception:
    pass
# --- end version badge ---

'@ + "`r`n")
} else {
  # Fallback: prepend
  $txt = @'
from app._version import get_version_info as _vinfo

# --- version badge (fixed position, non-interactive) ---
try:
    _vi = _vinfo()
    _v_ver = _vi.get("version", "v?")
    _v_dt  = _vi.get("date_utc", "")
    import streamlit as st  # safe if already imported above
    st.markdown(
        f"<div style='position:fixed;top:12px;right:28px;opacity:.85;padding:2px 8px;border:1px solid #444;border-radius:12px;font-size:12px;'>"
        f"{_v_ver} • {_v_dt}"
        "</div>",
        unsafe_allow_html=True,
    )
except Exception:
    pass
# --- end version badge ---

'@ + $txt
}

# Save
Set-Content -LiteralPath $target -Value $txt -Encoding UTF8 -NoNewline
Write-Host "Repaired version badge injection in $target"

# Purge caches
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
