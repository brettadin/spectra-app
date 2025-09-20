# Apply-v1.1.4b-ProvenanceShim.ps1
Param()

$ErrorActionPreference = "Stop"
$root = "C:\Code\spectra-app"
$target = Join-Path $root "app\utils\provenance.py"
$backup = "$target.bak.v1.1.4b"

if (!(Test-Path $target)) {
  throw "Target not found: $target"
}

# Backup once
if (!(Test-Path $backup)) { Copy-Item -LiteralPath $target -Destination $backup -Force }

# Read file
$txt = Get-Content -LiteralPath $target -Raw -Encoding UTF8

# If append_provenance already exists, do nothing
if ($txt -match 'def\s+append_provenance\s*\(') {
  Write-Host "append_provenance already present; no changes."
}
else {
  # Append the clean shim block
  $shim = @'
# ===== v1.1.4b SHIM: append_provenance (auto-appended) =====
# Some UI modules import `append_provenance` from app.utils.provenance.
# In v1.1.4x the canonical merger lives in app.server.provenance:merge_trace_provenance.
try:
    from app.server.provenance import merge_trace_provenance as _merge
except Exception:
    _merge = None

def append_provenance(manifest: dict, trace_id: str, prov: dict) -> dict:
    """Compatibility shim. Merges `prov` into manifest['traces'][trace_id]['fetch_provenance'].
    If server merger exists, delegate to it; otherwise perform a minimal local merge.
    Return the updated manifest (for chaining)."""
    if manifest is None:
        manifest = {}
    if _merge is not None:
        return _merge(manifest, trace_id, prov or {})
    # local merge
    traces = manifest.setdefault("traces", {})
    entry = traces.setdefault(str(trace_id), {})
    entry.setdefault("fetch_provenance", {}).update(prov or {})
    return manifest
# ===== end shim =====

'@
  $out = $txt.TrimEnd() + "`r`n`r`n" + $shim
  Set-Content -LiteralPath $target -Value $out -Encoding UTF8 -NoNewline
  Write-Host "Appended append_provenance shim to $target"
}

# Purge __pycache__ so the module is reloaded
Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Purged __pycache__"
