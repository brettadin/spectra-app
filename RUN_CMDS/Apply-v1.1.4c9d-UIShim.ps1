
Param(
  [string]$ProjectRoot = $(Resolve-Path (Join-Path $PSScriptRoot '..'))
)
$ErrorActionPreference = 'Stop'
function NowUtc { (Get-Date).ToUniversalTime().ToString('s') + 'Z' }

$log = Join-Path $ProjectRoot 'logs\ui_debug.log'
New-Item (Split-Path $log) -ItemType Directory -Force | Out-Null
"$(NowUtc) Apply-v1.1.4c9d-UIShim.ps1 ProjectRoot=$ProjectRoot" | Add-Content -LiteralPath $log

$payload = Join-Path $PSScriptRoot 'payload'
$entrySrc = Join-Path $payload 'entry.py'
$shimSrc  = Join-Path $payload 'merged_render_shim.txt'

# 1) Ensure app/ui/entry.py with render() exists
$uiDir = Join-Path $ProjectRoot 'app\ui'
$entryDest = Join-Path $uiDir 'entry.py'
New-Item $uiDir -ItemType Directory -Force | Out-Null

$writeEntry = $true
if (Test-Path $entryDest) {
  $cur = Get-Content -LiteralPath $entryDest -Raw -ErrorAction SilentlyContinue
  if ($cur -match '(?ms)^\s*def\s+render\s*\(') { $writeEntry = $false }
}
if ($writeEntry) {
  Copy-Item -LiteralPath $entrySrc -Destination $entryDest -Force
  "$(NowUtc) UIShim: wrote app\ui\entry.py" | Add-Content -LiteralPath $log
} else {
  "$(NowUtc) UIShim: app\ui\entry.py already has render(); noop" | Add-Content -LiteralPath $log
}

# 2) Append render() shim to app/app_merged.py so SmartEntry also finds it there
$merged = Join-Path $ProjectRoot 'app\app_merged.py'
if (-not (Test-Path $merged)) { throw "Not found: $merged" }
$bak = "$merged.bak.v1.1.4c9d"
Copy-Item -LiteralPath $merged -Destination $bak -Force
$src = Get-Content -LiteralPath $merged -Raw
if ($src -match '(?ms)^\s*def\s+render\s*\(') {
  "$(NowUtc) UIShim: app_merged already exports render(); noop" | Add-Content -LiteralPath $log
} else {
  $shim = Get-Content -LiteralPath $shimSrc -Raw
  $new = if ($src.TrimEnd().EndsWith([Environment]::NewLine)) { $src + $shim } else { $src + "`r`n" + $shim }
  Set-Content -LiteralPath $merged -Value $new -Encoding UTF8
  "$(NowUtc) UIShim: appended render() shim to app_merged.py; backup=$bak" | Add-Content -LiteralPath $log
}

# 3) Purge __pycache__
Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
"$(NowUtc) UIShim: purged __pycache__" | Add-Content -LiteralPath $log

Write-Host "v1.1.4c9d UIShim applied. Backup at $bak"
