# Spectra App — Brains v1.1.9

## Context
- Dense solar atlas uploads (2.5M+ rows) previously failed because the ASCII parser relied on pandas `read_csv` with strict delimiters, exhausting memory on whitespace-delimited files and throwing field-count errors.
- The overlay visibility UI required a form submission, leading to the “double input” lag reported by users.
- Plot discontinuities (“sharp drop-offs”) were traced to concatenating chunked DataFrames without reconciling boundaries before downsampling.

## Decisions & fixes
- Introduced `parse_ascii_segments` which streams ASCII payloads (or zip archives of them) into numeric arrays, normalises units, computes auxiliary statistics, and pre-builds multi-tier downsample caches.
- Added `SpectrumCache` to persist chunked `.npz` payloads with a JSON index, enabling lazy retrieval and future viewport-driven refinements.
- Overlay traces now carry downsample tiers and a `sample` helper so the UI only renders ~12k points per trace; this removed the drop-off artifact by downsampling *after* global sorting/deduplication.
- The overlay table is powered by `st.data_editor` with live boolean checkboxes plus “Show all/Hide all” shortcuts—no more form submission lag.

## Follow-ups / caveats
- Auxiliary third-column values are stored on disk with summary stats, but the UI still ignores them; surface in metadata drawer if needed.
- Differential plots currently use the downsampled vectors; for ultra-fine comparisons consider hydrating full-resolution data on demand.
- Cache directories respect `SPECTRA_CACHE_DIR`; clean shutdown should purge test fixtures to avoid drift.
