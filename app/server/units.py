from __future__ import annotations

from typing import Callable, Iterable, List


def _normalise_lookup_key(unit: str) -> str:
    cleaned = unit.strip()
    if not cleaned:
        raise ValueError("Empty unit provided")
    return cleaned.casefold().replace("μ", "µ")


_UNIT_ALIASES: dict[str, str] = {
    "nm": "nm",
    "nanometer": "nm",
    "nanometers": "nm",
    "nanometre": "nm",
    "nanometres": "nm",
    "nan": "nm",
    "angstrom": "Å",
    "ångström": "Å",
    "ångstrom": "Å",
    "å": "Å",
    "a": "Å",
    "aa": "Å",
    "ang": "Å",
    "µm": "µm",
    "um": "µm",
    "micron": "µm",
    "microns": "µm",
    "micrometer": "µm",
    "micrometers": "µm",
    "micrometre": "µm",
    "micrometres": "µm",
    "millimeter": "mm",
    "millimetre": "mm",
    "millimeters": "mm",
    "millimetres": "mm",
    "mm": "mm",
    "centimeter": "cm",
    "centimetre": "cm",
    "centimeters": "cm",
    "centimetres": "cm",
    "cm": "cm",
    "meter": "m",
    "metre": "m",
    "meters": "m",
    "metres": "m",
    "m": "m",
    "pm": "pm",
    "picometer": "pm",
    "picometre": "pm",
    "picometers": "pm",
    "picometres": "pm",
    "in": "in",
    "inch": "in",
    "inches": "in",
    "cm^-1": "cm^-1",
    "cm-1": "cm^-1",
    "1/cm": "cm^-1",
    "cm**-1": "cm^-1",
    "wavenumber": "cm^-1",
    "spatialfrequency": "cm^-1",
}


def _canonicalise(unit: str) -> str:
    lookup = _normalise_lookup_key(unit)
    if lookup in _UNIT_ALIASES:
        return _UNIT_ALIASES[lookup]
    raise ValueError(f"Unsupported wavelength unit: {unit}")


_LINEAR_SCALE: dict[str, float] = {
    "nm": 1.0,
    "Å": 0.1,
    "µm": 1000.0,
    "mm": 1_000_000.0,
    "cm": 10_000_000.0,
    "m": 1_000_000_000.0,
    "pm": 0.001,
    "in": 25_400_000.0,
}


def _convert_linear(values: Iterable[float], scale: float) -> List[float]:
    return [float(value) * scale for value in values]


def _cm_to_nm(value: float) -> float:
    if value == 0:
        raise ValueError("Cannot convert a zero wavenumber to wavelength")
    return 1.0e7 / float(value)


_SPECIAL_CONVERTERS: dict[str, Callable[[Iterable[float]], List[float]]] = {
    "cm^-1": lambda vals: [_cm_to_nm(float(value)) for value in vals],
}


def to_nm(values: Iterable[float], unit: str) -> List[float]:
    canonical = canonical_unit(unit)
    if canonical in _LINEAR_SCALE:
        return _convert_linear(values, _LINEAR_SCALE[canonical])
    if canonical in _SPECIAL_CONVERTERS:
        converter = _SPECIAL_CONVERTERS[canonical]
        return converter(values)
    raise ValueError(f"Unsupported wavelength unit: {unit}")


def canonical_unit(unit: str) -> str:
    canonical = _canonicalise(unit)
    return canonical
