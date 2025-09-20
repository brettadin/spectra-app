
Param()

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path $root -Parent
$dest = Join-Path $proj 'app\app_patched.py'
$src  = Join-Path $root '..\app\app_patched.py'
$verjson = Join-Path $root '..\app\version.json'

if (-not (Test-Path $src)) { Write-Error "Missing app\app_patched.py next to this script."; exit 1 }
if (-not (Test-Path $verjson)) { Write-Error "Missing app\version.json next to this script."; exit 1 }

if (Test-Path $dest) {
  Copy-Item $dest "$dest.bak.v1.1.4c8" -Force
}
Copy-Item $src $dest -Force
Copy-Item (Join-Path $root '..\app\version.json') (Join-Path $proj 'app\version.json') -Force

$logs = Join-Path $proj 'logs'
if (-not (Test-Path $logs)) { New-Item -ItemType Directory -Path $logs | Out-Null }

Get-ChildItem -Path $proj -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Applied EntryHunter v1.1.4c8 to $dest"
