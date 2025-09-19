# Starts the Spectra UI reliably
param(
  [int]$Port = 8501
)
$ErrorActionPreference = "Stop"
Set-Location -Path "C:\Code\spectra-app"

$env:PYTHONPATH="C:\Code\spectra-app"
if (!(Test-Path .\.venv)) { python -m venv .venv }

.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
# Ensure PNG export works
.\.venv\Scripts\pip install -U kaleido

# Print version for the logs
.\.venv\Scripts\python -m scripts.print_version

# Launch UI
.\.venv\Scripts\streamlit run app\ui\main.py --server.port $Port
