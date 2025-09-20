# v1.1.4 compatibility shim injector for app\utils\provenance.py
Param()

$ErrorActionPreference = "Stop"

$projRoot = "C:\Code\spectra-app"
$target = Join-Path $projRoot "app\utils\provenance.py"

if (!(Test-Path $target)) {
  throw "Target file not found: $target"
}

$original = Get-Content -LiteralPath $target -Raw -Encoding UTF8

if ($original -match "def\s+write_provenance\s*\(") {
  Write-Host "write_provenance already present. No changes made."
  exit 0
}

$shim = @"
# ===== v1.1.4 SHIM: write_provenance (auto-appended) =====
try:
    from app.server.provenance import merge_trace_provenance as _merge
except Exception as _e:
    _merge = None

def write_provenance(manifest: dict, trace_id: str, prov: dict) -> dict:
    \"\"\"Compatibility shim (v1.1.4). Preserves legacy import path
    app.utils.provenance.write_provenance by delegating to the unified
    server.provenance merger. Safe to keep alongside existing code.\"\"\"
    if _merge is not None:
        return _merge(manifest, trace_id, prov)
    traces = manifest.setdefault("traces", {})
    entry = traces.setdefault(trace_id, {})
    entry.setdefault("fetch_provenance", {}).update(prov or {})
    return manifest
# ===== end shim =====

"@

$updated = $original.TrimEnd() + "`r`n`r`n" + $shim

Set-Content -LiteralPath $target -Value $updated -Encoding UTF8 -NoNewline
Write-Host "Appended write_provenance shim to $target"
