from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
from astropy import units as u
from astropy.units import Quantity
from astropy.units import imperial
from astropy.units import UnitScaleError


def _as_unit(unit: str | u.UnitBase | Quantity) -> u.UnitBase:
    """Coerce user input into an ``astropy`` unit instance."""

    if isinstance(unit, Quantity):
        return unit.unit
    if isinstance(unit, u.UnitBase):
        return unit
    text = str(unit).strip()
    if not text:
        raise ValueError("Empty unit provided")
    lowered = text.lower()
    if lowered == "nm":
        return u.nm
    try:
        parsed = u.Unit(text)
        if parsed == u.nmi and lowered == "nm":
            return u.nm
        return parsed
    except Exception:
        with imperial.enable():
            try:
                return u.Unit(text)
            except Exception:
                pass
        try:
            return u.Unit(lowered)
        except Exception as exc:  # pragma: no cover - astropy specific
            with imperial.enable():
                try:
                    return u.Unit(lowered)
                except Exception as imperial_exc:
                    raise ValueError(f"Unsupported wavelength unit: {unit}") from imperial_exc


def resolve_unit(unit: str | u.UnitBase | Quantity) -> Tuple[u.UnitBase, str]:
    """Return a parsed unit and its canonical string label."""

    parsed = _as_unit(unit)
    try:
        canonical = parsed.to_string(format="fits")
    except UnitScaleError:
        canonical = parsed.to_string()
    return parsed, canonical


def quantity_from(
    values: Iterable[float], unit: str | u.UnitBase | Quantity
) -> Tuple[Quantity, str]:
    """Return a quantity constructed from ``values`` and its canonical unit."""

    parsed_unit, canonical = resolve_unit(unit)
    try:
        quantity = u.Quantity(values, parsed_unit, copy=False)
    except ValueError:
        quantity = u.Quantity(values, parsed_unit)
    return quantity, canonical


def to_nm(
    values: Iterable[float], unit: str | u.UnitBase | Quantity
) -> Tuple[Quantity, str]:
    """Convert the provided values into nanometres and return the canonical unit."""

    quantity, canonical = quantity_from(values, unit)

    try:
        converted = quantity.to(u.nm)
    except u.UnitConversionError:
        if quantity.unit.is_equivalent(u.m**-1) and np.any(
            np.asarray(quantity.value) == 0.0
        ):
            raise ValueError("Cannot convert a zero wavenumber to wavelength")
        try:
            converted = quantity.to(u.nm, equivalencies=u.spectral())
        except Exception as exc:  # pragma: no cover - astropy specific
            raise ValueError(f"Unsupported wavelength unit: {unit}") from exc

    return converted, canonical


def canonical_unit(unit: str | u.UnitBase | Quantity) -> str:
    """Return the canonical string representation for a unit value."""

    return resolve_unit(unit)[1]
