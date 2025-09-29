# Patch Notes — v1.1.9

## Highlights
- Overlay buttons in the Target catalog now use unique keys and queue spectra with labels so Streamlit does not raise duplicate-key exceptions.
- Ledger lock interacts with a dedicated `duplicate_ledger_lock` session flag; the checkbox never mutates its widget key and confirmation flows persist state safely.
- The ingest queue processes remote spectra immediately by downloading content and handing it to the existing local ingest pipeline, surfacing success or failure in the UI.
- Local ingest now rejects metadata-style tables with fewer than three samples so Target catalog overlays no longer produce misleading single-point plots.

## Follow-up
- Monitor overlay ingestion warnings during the next release candidate; capture failure URLs for regression tests.
- Continue prepping for Plotly width API updates by keeping layout helpers isolated in `app/ui/main.py`.

## Continuity
- Updated `CHANGELOG.md`, `docs/handoffs.md`, `docs/brains/brains_v1.1.9.md`, `PATCHLOG.txt`, and `app/version.json` to v1.1.9.
