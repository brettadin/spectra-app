# 06_DATA_MODEL_AND_UNITS (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:59:33Z  
**Author:** v1.1.4

Single source of truth for spectra and units so we stop converting nm to chaos.

---

## Spectrum model (canonical)
```python
class Spectrum:
    id: str                 # stable id for overlays/session
    label: str              # UI label
    x_nm: list[float]       # wavelength in nm (canonical)
    y: list[float]          # flux/arb units (unchanged by unit conversion)
    meta: dict              # instrument, target, etc.
    provenance_id: str|None # link into manifest['traces']
```

### Canonical rule
- Internally stored **only** in nanometers for X.
- All UI conversions are *views*, never rewrite `x_nm`.
- Export functions apply conversion at write time.

### Why nm
- Common across visible/near-IR; fewer float catastrophes than cm⁻¹.
- Easy round-tripping to Å and µm without precision crimes.

---

## Operations on Spectrum
- `view_x(target_unit)` → returns a numpy array converted from `x_nm`.
- `slice(min_nm, max_nm)` → returns a shallow copy with sliced arrays.
- `resample(new_grid_nm)` → linear/spline resampling on nm grid.
- `with_label(label)` → returns a new Spectrum with different label.

All operations are **pure**; no mutation of the original object.
