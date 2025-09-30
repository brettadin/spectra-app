# AI Handoff Prompt — v1.2.0b

## Snapshot
- Version: v1.2.0b (REF 1.2.0b-A01, 1.2.0b-D01)
- Focus: Accept FITS time-series tables, propagate time-axis metadata through the overlay/UI layers, and refresh continuity docs/tests.

## Completed in this patch
1. `_extract_table_data` and `_ingest_table_hdu` detect TIME-labelled columns plus BJD/MJD/second units, bypass the spectral-only guard, and surface `axis_kind="time"` with canonical time units + provenance (`time_converted_to`, `time_original_unit`).
2. `parse_fits` emits a `time` payload alongside `wavelength`, attaches `time_range` metadata, and records the new axis info in provenance so downstream consumers know how the axis was derived.
3. Overlay plotting/metadata (`app/ui/main.py`) now branches on `trace.axis_kind`, labels the x-axis `Time (...)`, and reports “Axis range” using the reported time unit. UI regression tests cover the new formatting.

## Outstanding priorities
- Extend ASCII ingestion to mirror the time-axis detection so CSV light curves land in the same codepath.
- Evaluate whether image HDUs with temporal WCS metadata require the same treatment (currently only table HDUs trigger the time pathway).
- Continue the v1.2 roadmap (SIMBAD resolver, ingestion consolidation, provenance enrichment, caching, export audits) after the time-series groundwork.

## Suggested next steps
- Add user-facing unit toggles for time-series traces (seconds/minutes/hours) while preserving canonical storage in days.
- Expand regression coverage with real mission light curves (e.g., TESS, Kepler) to validate provenance and plotting at scale.
- Revisit the documentation search tooling gap noted in prior releases so AGENTS.md requirements become actionable.
