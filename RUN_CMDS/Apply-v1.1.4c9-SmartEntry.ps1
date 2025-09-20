param()
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSCommandPath
$proj = Split-Path -Parent $root

$logDir = Join-Path $proj "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
(Get-Date -AsUTC).ToString("s") + "Z Applying v1.1.4c9 SmartEntry" | Out-File (Join-Path $logDir "ui_debug.log") -Append

$dst = Join-Path $proj "app\app_patched.py"
$bak = "$dst.bak.v1.1.4c9"
if (Test-Path $dst) { Copy-Item $dst $bak -Force }

$src = Join-Path $root "payload\app_patched.py"
Copy-Item $src $dst -Force

Get-ChildItem -Path $proj -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Applied SmartEntry v1.1.4c9 to $dst"
