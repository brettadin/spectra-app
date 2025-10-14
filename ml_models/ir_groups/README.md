# IR classifier assets

This directory contains the functional-group classifier assets used by Spectra App:

- `linear_surrogate.json.gz.b64` — a gzipped/base64 JSON payload encoding a
  lightweight linear surrogate (37 outputs × 600-point grid) derived from the
  shared correlation-band metadata so FTIR classification works offline.
- `optimal_thresholds.json` — per-label probability thresholds seeded from the
  rule-based fallback constants.

Deployments can replace the surrogate by fetching the published TensorFlow
weights and thresholds referenced in `scripts/fetch_ir_model.py`. The classifier
also accepts the upstream `0_model_extended.h5` and `optimal_thresholds.pkl`
artifacts when present.
