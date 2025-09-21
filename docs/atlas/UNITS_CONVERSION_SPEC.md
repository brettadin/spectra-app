# UNITS_CONVERSION_SPEC (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:59:33Z  
**Author:** v1.1.4

Supported axes: nm, Å, µm, cm⁻¹ (wavenumber). Canonical storage is nm.

## Exact formulas
- Å to nm: `nm = Å / 10`
- µm to nm: `nm = µm * 1000`
- nm to cm⁻¹: `k = 1 / (λ_cm)` where `λ_cm = nm * 1e-7`; so `k = 1e7 / nm`

## Round-trip guarantees
- Cycling nm → Å → µm → cm⁻¹ → nm must return to original within FP tolerance (`1e-9` relative).
- Implement conversions as small pure functions with explicit unit tags.

## API
```python
from enum import Enum

class AxisUnit(Enum):
    NM = "nm"; ANG = "Å"; MICRON = "µm"; WAVENUM = "cm⁻¹"

def convert_x(values_nm, target: AxisUnit):
    ...
```

## UI behavior
- Toggle cycles through units without touching stored data.
- Selected unit persisted in `st.session_state['axis_unit']`.
- Plots re-render against the converted view, legends append unit suffix.
