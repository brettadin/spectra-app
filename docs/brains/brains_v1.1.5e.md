# Brains — v1.1.5e
_Last updated (UTC): 2025-09-22T12:00:00Z_

## Purpose
This log documents the corrective release for **Spectra App v1.1.5e**. The
primary goal is to stabilise the CSV/TXT/FITS ingestion pipeline that debuted in
v1.1.5b by fixing the native resolution estimator and refreshing continuity
artifacts after the provenance/export overhaul.

## Canonical Continuity Sources
- `docs/brains/brains_v1.1.5e.md` (this document)
- `docs/brains/brains_INDEX.md` (version table)
- `docs/brains/ai_handoff.md` (guardrails)
- `docs/PATCH_NOTES/v1.1.5e.txt` (paired patch notes)
- `app/server/ingestion_pipeline.py`, `PATCHLOG.txt`, `app/version.json`

## Non-Breakable Invariants
1. **Unit provenance** — All ingestion conversions must emit provenance events
   per stage. Do not bypass `ConversionLog` when touching the pipeline.
2. **Resolution safety** — The native resolution estimator cannot divide by zero
   or mis-handle duplicate wavelength samples. Always filter invalid diffs
   before computing medians.
3. **Continuity sync** — `PATCHLOG.txt`, `docs/brains/*`, `docs/PATCH_NOTES/*`,
   and `app/version.json` must reference the same semantic version.

## v1.1.5e Scope
- Hardened `_estimate_resolution` so ingestion handles duplicate or unsorted
  wavelengths without raising shape mismatches when calculating resolving power.
- Applied the new helper across ASCII and FITS ingestion paths so every segment
  records a sane `resolution_native` when possible.
- Advanced continuity docs (brains index, patch log, version metadata) to keep
  the provenance trail aligned with the ingestion fix.

## Implementation Notes
- `_estimate_resolution` sorts finite wavelength samples, filters out zero or
  negative deltas, and only computes medians on valid ratios. This avoids the
  `ValueError` triggered when `np.diff` lost elements during zero-delta masking.
- ASCII uploads inherit metadata from header comments (`key: value`) while FITS
  metadata is extracted from standard keywords. Both call
  `_estimate_resolution` after wavelength conversions.
- Export manifests continue to capture per-trace provenance; no schema changes
  were required for this patch.

## Verification
- `pytest`
- Manual ingestion smoke test: upload a FITS lamp file with repeated wavelengths
  and confirm the UI no longer shows ingestion errors while metadata lists a
  finite resolution or gracefully omits it when unavailable.

## Follow-up
- Extend ingestion unit tests to cover ASCII/FITS inputs with repeated samples
  so `_estimate_resolution` stays guarded.
- Evaluate computing resolution from header dispersion values when the spectral
  axis uses logarithmic spacing to reduce noise in the median estimator.
