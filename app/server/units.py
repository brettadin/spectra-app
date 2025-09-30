from __future__ import annotations

from typing import Iterable

import numpy as np
from astropy import units as u
from astropy.units import Quantity


def _normalise_unit_string(unit: str) -> str:
    cleaned = unit.strip()
    if not cleaned:
        raise ValueError("Empty unit provided")

    replacements = {
        "Å": "angstrom",
        "Å": "angstrom",
        "å": "angstrom",
        "Ångström": "angstrom",
        "Ångstrom": "angstrom",
        "ångström": "angstrom",
        "ångstrom": "angstrom",
        "μ": "u",
        "µ": "u",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)

    return cleaned.casefold()


def _as_unit(unit: str | u.UnitBase | Quantity) -> u.UnitBase:
    if isinstance(unit, Quantity):
        return unit.unit
    if isinstance(unit, u.UnitBase):
        return unit
    try:
        normalised = _normalise_unit_string(str(unit))
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Unsupported wavelength unit: {unit}") from exc

    try:
        return u.Unit(normalised)
    except Exception as exc:  # pragma: no cover - astropy detail
        raise ValueError(f"Unsupported wavelength unit: {unit}") from exc


def to_nm(values: Iterable[float], unit: str | u.UnitBase | Quantity) -> Quantity:
    unit_obj = _as_unit(unit)
    quantity = u.Quantity(values, unit_obj)

    try:
        return quantity.to(u.nm)
    except u.UnitConversionError:
        if np.any(np.asarray(quantity.to_value(unit_obj)) == 0.0):
            raise ValueError("Cannot convert a zero wavenumber to wavelength")
        try:
            return quantity.to(u.nm, equivalencies=u.spectral())
        except Exception as exc:  # pragma: no cover - astropy detail
            raise ValueError(f"Unsupported wavelength unit: {unit}") from exc


def canonical_unit(unit: str | u.UnitBase | Quantity) -> str:
    parsed = _as_unit(unit)
    return parsed.to_string()
