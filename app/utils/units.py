"""
Unit utilities with logging hooks.

- resolve_units: decide canonical units and factor to convert incoming wavelength array.
- to_wavenumber: convert wavelength array to cm^-1.
- LogSink: basic logger for unit-related transformations to feed into provenance.

Assumptions:
- Canonical wavelength unit in-app: nanometers (nm).
"""

from __future__ import annotations
from typing import Tuple, Sequence, Dict, Any, Optional
import numpy as np

CANONICAL = "nm"
SUPPORTED = {"nm", "Å", "um", "µm", "cm^-1"}

class LogSink:
    def __init__(self):
        self.events = []

    def add(self, op: str, **kwargs):
        self.events.append({"op": op, **kwargs})

    def to_list(self):
        return list(self.events)

def resolve_units(header_unit: Optional[str], guess_from_values: bool=False, wl: Optional[Sequence[float]]=None, sink: Optional[LogSink]=None) -> Tuple[str, float]:
    """
    Decide canonical unit and provide multiply factor to convert input wl -> nm.
    Returns: (canonical_unit, factor_to_nm)
    """
    u = (header_unit or "").strip()
    if u in {"nm", "nanometer", "nanometers"}:
        factor = 1.0
        unit = "nm"
    elif u in {"Å", "A", "Angstrom", "Angstroms", "angstrom", "angstroms"}:
        factor = 0.1  # 1 Å = 0.1 nm
        unit = "Å"
    elif u in {"um", "µm", "micrometer", "micrometers"}:
        factor = 1000.0  # 1 µm = 1000 nm
        unit = "µm"
    elif u in {"cm^-1", "wavenumber"}:
        # wavenumber to nm is context-specific; caller should use to_wavenumber/wl_from_wavenumber
        factor = None
        unit = "cm^-1"
    else:
        # Fallback: assume nm if numbers look like visible range
        unit = "nm"
        factor = 1.0

    if sink is not None:
        sink.add("unit_resolve", header=header_unit, decided=unit, factor_to_nm=factor)
    return unit, factor

def convert_wl_to_nm(wl: Sequence[float], unit: str, sink: Optional[LogSink]=None):
    wl = np.asarray(wl, dtype=float)
    if unit == "nm":
        out = wl
    elif unit == "Å":
        out = wl * 0.1
    elif unit in {"um", "µm"}:
        out = wl * 1000.0
    else:
        raise ValueError(f"Cannot convert from {unit} to nm directly.")
    if sink is not None:
        sink.add("unit_convert", from_unit=unit, to_unit="nm")
    return out

def to_wavenumber(wl_nm: Sequence[float]) -> np.ndarray:
    wl_nm = np.asarray(wl_nm, dtype=float)
    wl_cm = wl_nm * 1e-7  # nm to cm
    return 1.0 / wl_cm

def wl_from_wavenumber(nu_cm: Sequence[float]) -> np.ndarray:
    nu_cm = np.asarray(nu_cm, dtype=float)
    wl_cm = 1.0 / nu_cm
    wl_nm = wl_cm * 1e7
    return wl_nm
