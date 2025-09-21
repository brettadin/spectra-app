# PATCH_NOTES_v1.1.3e
Date: 2025-09-19T22:30:31.919893Z

## Summary
- Idempotent **unit toggling** from canonical nm baseline.
- **CSV/TXT ingest hardening**: metadata/header skip, delimiter sniffing, numeric coercion.
- **Duplicate scope** control (Global | Session only | Off), "Ingest anyway" override, session purge.
- **Version badge** restored (top-right).
- **Provenance/unit logs drawer** for session visibility.

## Acceptance
- Unit cycle nm→Å→µm→cm⁻¹→nm preserves correct numeric axes.
- CSV with leading "Date:" or non-numeric lines ingests without crash (rows skipped).
- After refresh, re-upload once: behavior matches selected dedupe scope. Override works and records provenance notes.
- Badge visible. Logs drawer shows events.
