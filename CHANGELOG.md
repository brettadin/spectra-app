# Changelog

## v1.2.1aa — 2025-10-28
- IR: normalize all inputs to decadic absorbance (A10) with provenance; require path length + mole fraction for coefficients.
- JCAMP: infer X direction from data; verify FIRSTY vs scaled first Y.
- UI: scientific tick/hover formatting; no SI-prefix letters.
- Streamlit: first-load redirect guarded; health endpoint added at ?health=1.

## v1.1.9 — 2025-09-28
- Fix: unique keys for Overlay buttons in Target catalog (no more StreamlitDuplicateElementKey).
- Fix: stop mutating widget session_state key `duplicate_ledger_lock_checkbox`; use model var `duplicate_ledger_lock`.
- Feature: wire ingest queue so Overlay buttons actually fetch and plot spectra.
- Chore: silence several deprecation paths; prep for Plotly width API changes.
- Fix: reject metadata-like tables with too few samples so overlay plots stay physically meaningful.

## v1.2.0 — 2025-09-30
- Fix: guard FITS table ingestion against non-positive wavenumbers and capture aggregate dropped-row counts in provenance (REF 1.2.0-A01).
- Docs: restore runtime package inventory at `docs/runtime.json` and roll continuity collateral for v1.2.0 (REF 1.2.0-C01).
