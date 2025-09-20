# Start the patched Spectra App (v1.1.4)
param()
Set-Location C:\Code\spectra-app
$env:PYTHONUTF8=1
.\.venv\Scripts\python -m streamlit run app\app_patched.py --server.headless true
