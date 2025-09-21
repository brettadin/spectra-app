# Getting Started

This guide walks through setting up the Spectra App locally and reaching the main Streamlit workspace. The instructions mirror the automation shipped in `RUN_CMDS/` so Windows users can rely on the provided scripts, while macOS/Linux operators can adapt the manual steps.

## Prerequisites
- Python 3.10+
- Git
- PowerShell 7 (for Windows automation scripts)
- Optional: `kaleido` for PNG exports (installed automatically by the scripts)

## Fast Path (Windows)
1. Clone or update the repository at `C:\Code\spectra-app`.
2. Launch PowerShell and run:
   ```powershell
   .\RUN_CMDS\Clean-Install.ps1    # one-time or when dependencies drift
   .\RUN_CMDS\Start-Spectra.ps1    # starts Streamlit at http://localhost:8501
   ```
3. When prompted, Streamlit opens the UI in your browser. Use the **Docs** tab to access this Atlas from inside the app.

## Cross-Platform Manual Steps
These commands mirror the automation and can run on any OS:
```bash
cd spectra-app
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -U kaleido           # ensures PNG export support
streamlit run app/ui/main.py
```
The UI launches at <http://localhost:8501>.

## Verifying the Install
Before pushing changes or packaging an export, run the verification script:
```powershell
.\RUN_CMDS\Verify-Project.ps1
```
It checks continuity documents, provider directories, and basic tests. Linux/macOS users can reproduce the same coverage with:
```bash
pytest
python scripts/print_version.py
```

## Repository Landmarks
- `app/server/ingestion_pipeline.py` — normalises user data to SI units.
- `app/ui/main.py` — Streamlit entry point.
- `app/export_manifest.py` — builds PNG/CSV/manifest bundles.
- `docs/atlas/` — this documentation set (displayed in the in-app Docs tab).
- `docs/brains/` — continuity logs that **must** be updated with any behavioural change.

Keep the Atlas and brains log in sync; they are reviewed together during code review.
