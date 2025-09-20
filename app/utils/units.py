from __future__ import annotations
from typing import Sequence, Optional, Tuple
import numpy as np

class LogSink:
    def __init__(self):
        self.events = []
    def add(self, op: str, **kwargs):
        self.events.append({"op": op, **kwargs})
    def to_list(self):
        return list(self.events)

def resolve_units(header_unit: Optional[str]) -> Tuple[str, float | None]:
    u = (header_unit or "").strip()
    if u in {"nm", "nanometer", "nanometers"}: return "nm", 1.0
    if u in {"Å", "A", "Angstrom", "angstrom"}: return "Å", 0.1
    if u in {"um", "µm", "micrometer", "micrometers"}: return "µm", 1000.0
    if u in {"cm^-1", "wavenumber"}: return "cm^-1", None
    return "nm", 1.0

def convert_array_to_nm(wl: Sequence[float], unit: str, sink: Optional[LogSink]=None):
    wl = np.asarray(wl)
    if unit == "nm":
        out = wl.astype(float)
    elif unit in {"Å","A"}:
        out = wl.astype(float) * 0.1
    elif unit in {"um","µm"}:
        out = wl.astype(float) * 1000.0
    elif unit == "cm^-1":
        wl_cm = 1.0 / wl.astype(float)
        out = wl_cm * 1e7  # cm -> nm
    else:
        out = wl.astype(float)
    if sink is not None:
        sink.add("unit_convert_to_nm", from_unit=unit, to_unit="nm")
    return out

def convert_nm_to_display(wl_nm: Sequence[float], unit: str):
    x = np.asarray(wl_nm, dtype=float)
    if unit == "nm":
        return x
    if unit in {"Å","A"}:
        return x * 10.0
    if unit in {"um","µm"}:
        return x / 1000.0
    if unit == "cm^-1":
        wl_cm = x * 1e-7
        return 1.0 / wl_cm
    return x
