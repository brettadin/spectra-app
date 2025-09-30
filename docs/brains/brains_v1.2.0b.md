# Brains — v1.2.0b

## Release focus
- **REF 1.2.0b-A01**: Extend FITS ingestion so table HDUs with time-like axes (TIME columns, BJD/MJD/second units) import as canonical time-series without tripping wavelength validation.
- **REF 1.2.0b-D01**: Update overlay plotting, metadata summaries, and regression coverage so time-series payloads surface their native units and ranges alongside flux.

## Implementation notes
- `_extract_table_data` now detects TIME columns via column labels, CTYPE hints, and unit tokens (BJD/MJD/seconds) before mapping them into a new `axis_kind="time"` pathway. Time axes keep their original unit string in provenance while normalising values to canonical Astropy units for plotting.
- `_ingest_table_hdu` and `parse_fits` surface the time axis details (`time_range`, `time_unit`, `time_original_unit`, provenance `time_converted_to`) and emit a `time` payload alongside the existing `wavelength` block so downstream consumers do not have to guess.
- UI changes teach the overlay renderer to branch on `trace.axis_kind`, label the x-axis as `Time (...)`, and update metadata tables so “Axis range” reflects either nm or the reported time unit. Additional regression coverage in `tests/ui/test_metadata_summary.py` ensures the new axis handling stays serialisable.

## Testing
- `pytest tests/server/test_ingest_fits.py::test_parse_fits_accepts_time_series_units`
- `pytest tests/ui/test_metadata_summary.py`

## Outstanding work
- Extend the time-series branch to cover image HDUs with temporal WCS keywords should we ingest cube formats later.
- Consider exposing a user-facing axis-unit toggle (seconds/minutes/hours) once more light-curve datasets land in the catalog.
- Revisit ASCII ingestion to mirror the FITS time-axis detection so CSV light curves ingest with consistent metadata.

## Continuity updates
- Version bumped to v1.2.0b with corresponding entries in `PATCHLOG.txt`, `docs/patch_notes/v1.2.0b.md`, `docs/PATCH_NOTES/v1.2.0b.txt`, `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.2.0b.md`, and `docs/ai_log/2025-09-30.md`.
