# Nuke-and-pave the environment, then install
$ErrorActionPreference = "Stop"
Set-Location -Path "C:\Code\spectra-app"

# Remove venv and caches
if (Test-Path .\.venv) { Remove-Item -Recurse -Force .\.venv }
Get-ChildItem -Recurse -Include __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Recreate venv
python -m venv .venv

# Upgrade pip and install deps
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
# Image export helper
.\.venv\Scripts\pip install -U kaleido

# Print version to confirm
$env:PYTHONPATH="C:\Code\spectra-app"
.\.venv\Scripts\python -m scripts.print_version
Write-Host "Clean install complete."
