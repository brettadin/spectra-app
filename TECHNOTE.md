# Solar spectrum ingestion technote

## File format assumptions
- Supports ASCII spectra with variable whitespace, optional third auxiliary column, and header comments prefixed with `#`.
- Automatically normalises wavelength units to nanometres and interprets third-column values as auxiliary metadata stored in the cache.
- Zipped archives (`.zip`) are expanded in-memory and all supported ASCII files inside are merged into a single, sorted spectrum.
- Blank rows and malformed lines after numeric data begins are skipped with counters captured in provenance.

## Unit handling
- Wavelength units are inferred from header hints; fall back to nanometres when no hint is present.
- Flux units are derived from header metadata or column labels, with relative units defaulting to `arb`.
- Provenance records all conversions from reported to canonical units; auxiliary column statistics are recorded when present.

## Caching & downsampling strategy
- Dense parses stream into double-precision arrays and build per-tier downsample sets (min/max envelope for coarse tiers, LTTB for fine tiers).
- Spectra are chunked in partitions of 500k samples and stored as compressed NumPy arrays under `data/cache/spectra/<sha256>/chunk_*.npz` with a JSON index.
- The UI only renders downsampled tiers (up to ~12k points per trace) chosen dynamically based on the active viewport, while full-resolution data remains in cache for exports and differential operations.
- Cache directories honour the `SPECTRA_CACHE_DIR` environment variable to simplify testing and sandboxing.

## Known caveats
- Auxiliary third-column values are preserved in cache files but not yet visualised in the UI.
- Differential viewports reuse downsampled vectors which may smooth very sharp features; exporting a view rehydrates the full-resolution data.
- When cache directories are pruned manually the app rebuilds tiers on next ingest; no automatic invalidation is triggered.
