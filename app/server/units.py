from __future__ import annotations

from typing import Iterable

import numpy as np
from astropy import units as u
from astropy.units import Quantity


def _as_unit(unit: str | u.UnitBase | Quantity) -> u.UnitBase:
    """Coerce user input into an ``astropy`` unit instance."""

    if isinstance(unit, Quantity):
        return unit.unit
    if isinstance(unit, u.UnitBase):
        return unit
    text = str(unit).strip()
    if not text:
        raise ValueError("Empty unit provided")
    try:
        return u.Unit(text)
    except Exception:
        lowered = text.lower()
        try:
            return u.Unit(lowered)
        except Exception as exc:  # pragma: no cover - astropy specific
            raise ValueError(f"Unsupported wavelength unit: {unit}") from exc


def to_nm(values: Iterable[float], unit: str | u.UnitBase | Quantity) -> Quantity:
    """Convert the provided values into nanometres."""

    unit_obj = _as_unit(unit)
    try:
        quantity = u.Quantity(values, unit_obj, copy=False)
    except ValueError:
        quantity = u.Quantity(values, unit_obj)

    try:
        return quantity.to(u.nm)
    except u.UnitConversionError:
        if np.any(np.asarray(quantity.to_value(unit_obj)) == 0.0):
            raise ValueError("Cannot convert a zero wavenumber to wavelength")
        try:
            return quantity.to(u.nm, equivalencies=u.spectral())
        except Exception as exc:  # pragma: no cover - astropy specific
            raise ValueError(f"Unsupported wavelength unit: {unit}") from exc


def canonical_unit(unit: str | u.UnitBase | Quantity) -> str:
    """Return the canonical string representation for a unit value."""

    parsed = _as_unit(unit)
    return parsed.to_string(format="fits")
