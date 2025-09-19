@echo off
setlocal
cd /d C:\Code\spectra-app
set PYTHONPATH=C:\Code\spectra-app
if not exist .venv (
  python -m venv .venv
)
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -U kaleido
.\.venv\Scripts\python -m scripts.print_version
.\.venv\Scripts\streamlit run app\ui\main.py
