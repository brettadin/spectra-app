param()
Set-Location C:\Code\spectra-app
$env:PYTHONUTF8=1
.\.venv\Scripts\python -m streamlit run app\app_merged.py --server.headless true
