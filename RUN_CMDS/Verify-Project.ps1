# Verifies structure, key files, and basic imports; nonzero exit on failure
# Fixed: use temp .py file instead of Bash-style heredoc which PowerShell doesn't support.
$ErrorActionPreference = "Stop"
Set-Location -Path "C:\Code\spectra-app"

$required = @(
  "app\version.json",
  "app\ui\main.py",
  "PATCHLOG.txt",
  "docs\ai_handoff",
  "docs\patches",
  "docs\brains"
)

$missing = @()
foreach ($rel in $required) {
  if (!(Test-Path $rel)) { $missing += $rel }
}
if ($missing.Count -gt 0) {
  Write-Error ("Missing required paths:`n" + ($missing -join "`n"))
  exit 1
}

# Ensure venv exists
if (!(Test-Path .\.venv)) { python -m venv .venv }

$env:PYTHONPATH="C:\Code\spectra-app"

# Write a temporary Python file for the import sanity check
$tmpPy = New-TemporaryFile
@'
from app._version import get_version_info
vi = get_version_info()
assert isinstance(vi, dict) and "version" in vi, "version info missing"
print(f"OK version: {vi['version']} | {vi['date_utc']} | {vi['summary']}")
'@ | Out-File -Encoding UTF8 -FilePath $tmpPy.FullName -Force

# Run it
.\.venv\Scripts\python $tmpPy.FullName

# Clean up
Remove-Item $tmpPy.FullName -Force -ErrorAction SilentlyContinue

# Show longform notes if present
$ver = (Get-Content app\version.json | ConvertFrom-Json).version
$longform = "docs\patches\PATCH_NOTES_{0}.md" -f $ver
if (Test-Path $longform) {
  Write-Host "`n--- Longform notes for $ver ---`n"
  Get-Content $longform | Select-Object -First 20
} else {
  Write-Host "No longform notes for $ver (write them)."
}
# Brains note presence
$brains = "docs\brains\{0} brains.txt" -f $ver
if (Test-Path $brains) {
  Write-Host "`nBrains note found for $ver."
} else {
  Write-Host "No brains note for $ver (add it)."
}

Write-Host "`nVerification passed."
