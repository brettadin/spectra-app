# Apply-v1.1.4c-UIKeys-VersionBadge.ps1
Param()

$ErrorActionPreference = "Stop"
$root = "C:\Code\spectra-app"
$target = Join-Path $root "app\app_merged.py"
$backup = "$target.bak.v1.1.4c"

if (!(Test-Path $target)) { throw "Target not found: $target" }
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $target -Destination $backup -Force }

# Load
$txt = Get-Content -LiteralPath $target -Raw -Encoding UTF8

# 1) Unique keys for example checkboxes
$txt = [Regex]::Replace($txt,
    'st\.sidebar\.checkbox\(\s*name\s*,\s*True\s*\)',
    'st.sidebar.checkbox(name, True, key=f"example_{name}")')

# 2) Keys for display mode radio
$txt = [Regex]::Replace($txt,
    'st\.sidebar\.radio\(\s*"Display mode"\s*,\s*\[[^\)]*?\]\s*,\s*index\s*=\s*\d+\s*\)',
    { param($m) $m.Value.TrimEnd(')') + ', key="display_mode")' })

# 3) Keys for display units selectbox
$txt = [Regex]::Replace($txt,
    'st\.sidebar\.selectbox\(\s*"Display units"\s*,\s*\[[^\)]*?\]\s*,\s*index\s*=\s*\d+\s*\)',
    { param($m) $m.Value.TrimEnd(')') + ', key="display_units")' })

# 4) Keys for duplicate scope radio
$txt = [Regex]::Replace($txt,
    'st\.sidebar\.radio\(\s*"Apply duplicate detection to"\s*,\s*\[[^\)]*?\]\s*,\s*index\s*=\s*\d+\s*\)',
    { param($m) $m.Value.TrimEnd(')') + ', key="dedupe_scope")' })

# 5) Version badge: ensure import + injected badge block after `import streamlit as st`
if ($txt -notmatch 'from\s+app\._version\s+import\s+get_version_info') {
  $txt = [Regex]::Replace($txt,
    '(?m)^(\s*import\s+streamlit\s+as\s+st\s*)$',
    "`$1`r`nfrom app._version import get_version_info as _vinfo")
}
if ($txt -notmatch 'position:fixed;top:12px;right:28px') {
  $badge = @'
try:
    _vi = _vinfo()
    st.markdown(
        f"<div style='position:fixed;top:12px;right:28px;opacity:.85;padding:2px 8px;border:1px solid #444;border-radius:12px;font-size:12px;'>"
        f"{_vi.get('version','v?')} • {_vi.get('date_utc','')}"
        "</div>",
        unsafe_allow_html=True,
    )
except Exception:
    pass
'@
  $txt = [Regex]::Replace($txt,
    '(?m)^(\s*def\s+[_a-zA-Z0-9]+\s*\(.*\)\s*:\s*)',
    "$1`r`n$badge", 1)  # insert after first def (top-level render entry) if present; else no-op
  if ($txt -notmatch 'position:fixed;top:12px;right:28px') {
    # Fallback: insert after the import line
    $txt = [Regex]::Replace($txt,
      '(?m)(from\s+app\._version\s+import\s+get_version_info\s+as\s+_vinfo\s*)$',
      "`$1`r`n$badge")
  }
}

# Save
Set-Content -LiteralPath $target -Value $txt -Encoding UTF8 -NoNewline
Write-Host "Patched widget keys and version badge in $target"

# Purge pyc
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
