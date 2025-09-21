**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 01 - MODELS SCHEMA (Deep)
This file documents every data model, field, validation rules, invariants, and usage examples for the server layer.

## Canonical Spectrum (detailed)
**File:** `app/server/models.py`

### Dataclass definition (recommended)
```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np

@dataclass(frozen=True)
class Spectrum:
    id: str                      # unique id, stable per import/session
    label: str                   # human friendly label
    x_nm: List[float]            # canonical wavelengths (nm) - strictly ascending
    y: List[float]               # flux/intensity values (same length as x_nm)
    meta: Dict[str, object] = field(default_factory=dict)  # instrument, target, units noted
    provenance_id: Optional[str] = None  # link into manifest['traces']
```
### Validation rules
- `x_nm` and `y` must be the same length (>1).
- `x_nm` must be strictly monotonically increasing (or validated/resampled).
- Values coerced to `float64` internally.
- NaNs removed with a warning; record `dropped_nans` in meta.
- `id` generation: prefer stable hash `sha1(target+source+timestamp)` but support user-provided ids.

### Methods recommended on model
- `to_dict()` - canonical serializable representation
- `view_x(unit)` - returns converted axis array (pure view)
- `slice_nm(min_nm, max_nm)` - returns new Spectrum with sliced arrays
- `resample_nm(grid_nm, method='linear')` - returns new Spectrum on grid_nm

### Why dataclass & immutability
- Immutability prevents accidental UI mutations and race conditions during reruns.
- Pure operations encourage functional transformations and simpler testing.

## TraceSet / Overlay manifest
**File:** `app/server/models.py` (same module)
Structure grouping multiple spectra for session export and overlays:
```python
@dataclass
class OverlayMeta:
    id: str
    label: str
    color: str
    visible: bool = True
    provenance_id: Optional[str] = None

@dataclass
class TraceSet:
    spectra: Dict[str, Spectrum] = field(default_factory=dict)
    overlays: List[OverlayMeta] = field(default_factory=list)
    active_trace: Optional[str] = None
```
### Invariants
- `overlays` ids must exist in `spectra` keys.
- `active_trace` must be None or a valid overlay id.

## Model migration notes
- Keep backward compatibility by supporting older keys in `meta` (e.g., `unit_hint`) and convert at construction time.
- Provide a utility `upgrade_manifest(old_manifest)` to normalize older formats to the new schema.

## Example usage
```python
s, prov = fetch_from_mast('Vega')
spec = Spectrum(id='s1', label='Vega MAST', x_nm=s['wavelength_nm'], y=s['flux'], meta={'source':'mast'})
traceset = TraceSet(spectra={'s1': spec}, overlays=[OverlayMeta(id='s1',label='Vega',color='auto-0')])
```
