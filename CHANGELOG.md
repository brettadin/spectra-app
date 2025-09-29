# Changelog

## v1.1.9 — 2025-09-28
- Fix: unique keys for Overlay buttons in Target catalog (no more StreamlitDuplicateElementKey).
- Fix: stop mutating widget session_state key `duplicate_ledger_lock_checkbox`; use model var `duplicate_ledger_lock`.
- Feature: wire ingest queue so Overlay buttons actually fetch and plot spectra.
- Chore: silence several deprecation paths; prep for Plotly width API changes.
- Fix: reject metadata-like tables with too few samples so overlay plots stay physically meaningful.
