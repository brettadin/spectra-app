# Verify-Project.ps1 — UTF-8 safe version
# Run from C:\Code\spectra-app

$ErrorActionPreference = "Stop"
Set-Location -Path "C:\Code\spectra-app"

$required = @(
  "app\version.json",
  "app\ui\main.py",
  "PATCHLOG.txt",
  "docs\ai_handoff",
  "docs\patches",
  "docs\brains",
  "docs\PATCH_NOTES",
  "data\providers"
)

$missing = @()
foreach ($rel in $required) {
  if (!(Test-Path $rel)) { $missing += $rel }
}
if ($missing.Count -gt 0) {
  Write-Error ("Missing required paths:`n" + ($missing -join "`n"))
  exit 1
}

if (!(Test-Path .\.venv)) { python -m venv .venv }
$env:PYTHONPATH="C:\Code\spectra-app"

$tmpPy = New-TemporaryFile
@'
from app._version import get_version_info
vi = get_version_info()
assert isinstance(vi, dict) and "version" in vi, "version info missing"
print(f"OK version: {vi['version']} | {vi['date_utc']} | {vi['summary']}")
'@ | Out-File -Encoding UTF8 -FilePath $tmpPy.FullName -Force

.\.venv\Scripts\python $tmpPy.FullName
Remove-Item $tmpPy.FullName -Force -ErrorAction SilentlyContinue

$ver = (Get-Content app\version.json | ConvertFrom-Json).version
$brainsIndex = "docs\brains\brains_INDEX.md"
$brainsBridge = "docs\brains\ai_handoff.md"
$brainsFile = "docs\brains\brains_{0}.md" -f $ver
$patchNotes = "docs\PATCH_NOTES\{0}.txt" -f $ver
$providerDirs = @(
  "data\providers",
  "data\providers\mast",
  "data\providers\eso",
  "data\providers\simbad",
  "data\providers\nist"
)

$continuityMissing = @()
foreach ($path in @($brainsIndex, $brainsBridge, $brainsFile, $patchNotes) + $providerDirs) {
  if (!(Test-Path $path)) { $continuityMissing += $path }
}
if ($continuityMissing.Count -gt 0) {
  Write-Error ("Missing continuity assets:`n" + ($continuityMissing -join "`n"))
  exit 1
}

$brainsText = Get-Content $brainsFile -Raw
$patchText = Get-Content $patchNotes -Raw
$indexText = Get-Content $brainsIndex -Raw
$bridgeText = Get-Content $brainsBridge -Raw

$brainsLink = "docs/brains/brains_{0}.md" -f $ver
$patchLink = "docs/PATCH_NOTES/{0}.txt" -f $ver

if (-not $brainsText.Contains($patchLink)) {
  Write-Error "Brains file missing link to patch notes: $patchLink"
}
if (-not $patchText.Contains($brainsLink)) {
  Write-Error "Patch notes missing link back to brains: $brainsLink"
}
if (-not $indexText.Contains($brainsLink)) {
  Write-Error "Brains index missing current brains entry: $brainsLink"
}
if (-not $indexText.Contains($patchLink)) {
  Write-Error "Brains index missing current patch notes: $patchLink"
}
if (-not $bridgeText.Contains("docs/ai_handoff/")) {
  Write-Error "AI handoff bridge must reference docs/ai_handoff prompt."
}

Write-Host "`n--- Patch notes for $ver ---`n"
Get-Content $patchNotes | Select-Object -First 20

Write-Host "`n--- Brains for $ver ---`n"
Get-Content $brainsFile | Select-Object -First 20

Write-Host "`nVerification passed."
