from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

SPEED_OF_LIGHT = 299_792_458.0  # m s^-1


# ---------------------------------------------------------------------------
# Provenance helpers


@dataclass
class ConversionEvent:
    """Single provenance record describing a unit conversion."""

    stage: str
    original_unit: str
    target_unit: str
    formula: str
    context: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        payload = {
            "stage": self.stage,
            "from": self.original_unit,
            "to": self.target_unit,
            "formula": self.formula,
        }
        if self.context:
            payload["context"] = dict(self.context)
        return payload


class ConversionLog:
    """Collect provenance events during ingestion."""

    def __init__(self) -> None:
        self._events: List[ConversionEvent] = []

    def add(
        self,
        stage: str,
        original_unit: str,
        target_unit: str,
        formula: str,
        **context: object,
    ) -> None:
        self._events.append(
            ConversionEvent(
                stage=stage,
                original_unit=original_unit,
                target_unit=target_unit,
                formula=formula,
                context=context,
            )
        )

    def extend(self, events: Iterable[ConversionEvent]) -> None:
        for event in events:
            self._events.append(event)

    def to_records(self) -> List[Dict[str, object]]:
        return [event.as_dict() for event in self._events]

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return bool(self._events)


# Backwards compatible alias used by legacy code.
LogSink = ConversionLog


# ---------------------------------------------------------------------------
# Wavelength parsing & conversion


@dataclass(frozen=True)
class _WavelengthUnit:
    key: str
    kind: str  # 'length' or 'wavenumber'
    to_si: float  # multiply value in this unit by to_si to obtain SI base
    display: str


# Canonical definitions (aliases are populated below)
_LENGTH_UNITS: Dict[str, _WavelengthUnit] = {
    "m": _WavelengthUnit("m", "length", 1.0, "m"),
    "nm": _WavelengthUnit("nm", "length", 1e-9, "nm"),
    "um": _WavelengthUnit("µm", "length", 1e-6, "µm"),
    "µm": _WavelengthUnit("µm", "length", 1e-6, "µm"),
    "mm": _WavelengthUnit("mm", "length", 1e-3, "mm"),
    "cm": _WavelengthUnit("cm", "length", 1e-2, "cm"),
    "Å": _WavelengthUnit("Å", "length", 1e-10, "Å"),
    "ang": _WavelengthUnit("Å", "length", 1e-10, "Å"),
}
_WAVENUMBER_UNITS: Dict[str, _WavelengthUnit] = {
    "cm^-1": _WavelengthUnit("cm^-1", "wavenumber", 100.0, "cm⁻¹"),
    "cm-1": _WavelengthUnit("cm^-1", "wavenumber", 100.0, "cm⁻¹"),
    "1/cm": _WavelengthUnit("cm^-1", "wavenumber", 100.0, "cm⁻¹"),
    "m^-1": _WavelengthUnit("m^-1", "wavenumber", 1.0, "m⁻¹"),
}

# Populate alias map
_WAVELENGTH_ALIASES: Dict[str, _WavelengthUnit] = {}
for canonical in list(_LENGTH_UNITS.values()) + list(_WAVENUMBER_UNITS.values()):
    _WAVELENGTH_ALIASES[canonical.key.casefold()] = canonical

_ADDITIONAL_WAVELENGTH_ALIASES = {
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "micron": "µm",
    "microns": "µm",
    "micrometer": "µm",
    "micrometers": "µm",
    "micrometre": "µm",
    "micrometres": "µm",
    "angstrom": "Å",
    "ångström": "Å",
    "ångstrom": "Å",
    "a": "Å",
    "aa": "Å",
    "pm": "pm",
}
_LENGTH_UNITS["pm"] = _WavelengthUnit("pm", "length", 1e-12, "pm")
for alias, target in _ADDITIONAL_WAVELENGTH_ALIASES.items():
    if target in _LENGTH_UNITS:
        _WAVELENGTH_ALIASES[alias] = _LENGTH_UNITS[target]


def _resolve_wavelength_unit(unit: str | None) -> _WavelengthUnit:
    token = (unit or "m").strip()
    token = token.replace("μ", "µ")
    if not token:
        token = "m"
    lookup = token.casefold()
    if lookup in _WAVELENGTH_ALIASES:
        return _WAVELENGTH_ALIASES[lookup]
    if lookup in _WAVENUMBER_UNITS:
        return _WAVENUMBER_UNITS[lookup]
    raise ValueError(f"Unsupported wavelength unit: {unit}")


def detect_wavelength_unit(label: str | None) -> Optional[str]:
    """Infer a wavelength unit from a column label or FITS keyword."""

    if not label:
        return None
    cleaned = label.replace("μ", "µ")
    if "cm^-1" in cleaned or "cm-1" in cleaned or "1/cm" in cleaned:
        return "cm^-1"
    tokens = re.findall(r"[A-Za-zµÅ]+(?:-?\^?-?\d+)?", cleaned)
    for token in tokens:
        try:
            resolved = _resolve_wavelength_unit(token)
        except ValueError:
            continue
        if resolved.kind == "length":
            return resolved.display
    return None


def wavelength_to_m(
    values: Sequence[float],
    unit: str | None,
    log: Optional[ConversionLog] = None,
    stage: str = "wavelength",
) -> np.ndarray:
    info = _resolve_wavelength_unit(unit)
    arr = np.asarray(values, dtype=float)
    if info.kind == "wavenumber":
        sigma = arr * info.to_si
        with np.errstate(divide="ignore", invalid="ignore"):
            converted = np.where(sigma != 0.0, 1.0 / sigma, np.nan)
        formula = "λ = 1 / σ"
    else:
        converted = arr * info.to_si
        formula = "λ_m = λ_unit × factor"
    if log is not None:
        log.add(
            stage,
            original_unit=info.display,
            target_unit="m",
            formula=formula,
            factor=info.to_si,
        )
    return converted


def wavelength_from_m(values: Sequence[float], unit: str) -> np.ndarray:
    info = _resolve_wavelength_unit(unit)
    arr = np.asarray(values, dtype=float)
    if info.kind == "wavenumber":
        with np.errstate(divide="ignore", invalid="ignore"):
            sigma = np.where(arr != 0.0, 1.0 / arr, np.nan)
        return sigma / info.to_si
    return arr / info.to_si


# ---------------------------------------------------------------------------
# Flux parsing & conversion


@dataclass(frozen=True)
class _FluxUnit:
    key: str
    kind: str  # 'F_lambda', 'F_nu', 'dimensionless', 'counts'
    to_si: float
    display: str


_FLUX_UNIT_ALIASES: Dict[str, _FluxUnit] = {
    "w/m^2/m": _FluxUnit("W m⁻² m⁻¹", "F_lambda", 1.0, "W m⁻² m⁻¹"),
    "w/m^2/nm": _FluxUnit("W m⁻² nm⁻¹", "F_lambda", 1e9, "W m⁻² m⁻¹"),
    "w/m^2/um": _FluxUnit("W m⁻² µm⁻¹", "F_lambda", 1e6, "W m⁻² m⁻¹"),
    "w/m^2/µm": _FluxUnit("W m⁻² µm⁻¹", "F_lambda", 1e6, "W m⁻² m⁻¹"),
    "w/m^2/a": _FluxUnit("W m⁻² Å⁻¹", "F_lambda", 1e10, "W m⁻² m⁻¹"),
    "erg/s/cm^2/a": _FluxUnit("erg s⁻¹ cm⁻² Å⁻¹", "F_lambda", 1e7, "W m⁻² m⁻¹"),
    "erg/s/cm^2/nm": _FluxUnit("erg s⁻¹ cm⁻² nm⁻¹", "F_lambda", 1e6, "W m⁻² m⁻¹"),
    "erg/s/cm^2/cm": _FluxUnit("erg s⁻¹ cm⁻² cm⁻¹", "F_lambda", 1e5, "W m⁻² m⁻¹"),
    "erg/s/cm^2/m": _FluxUnit("erg s⁻¹ cm⁻² m⁻¹", "F_lambda", 1e3, "W m⁻² m⁻¹"),
    "jy": _FluxUnit("Jy", "F_nu", 1e-26, "W m⁻² Hz⁻¹"),
    "jansk": _FluxUnit("Jy", "F_nu", 1e-26, "W m⁻² Hz⁻¹"),
    "mjy": _FluxUnit("mJy", "F_nu", 1e-29, "W m⁻² Hz⁻¹"),
    "µjy": _FluxUnit("µJy", "F_nu", 1e-32, "W m⁻² Hz⁻¹"),
    "ujy": _FluxUnit("µJy", "F_nu", 1e-32, "W m⁻² Hz⁻¹"),
    "erg/s/cm^2/hz": _FluxUnit("erg s⁻¹ cm⁻² Hz⁻¹", "F_nu", 1e-3, "W m⁻² Hz⁻¹"),
    "counts": _FluxUnit("counts", "counts", 1.0, "counts"),
    "adu": _FluxUnit("ADU", "counts", 1.0, "ADU"),
    "dimensionless": _FluxUnit("unitless", "dimensionless", 1.0, "unitless"),
    "transmission": _FluxUnit("transmission", "dimensionless", 1.0, "transmission"),
}


def _normalise_flux_unit(text: str | None) -> Optional[_FluxUnit]:
    if not text:
        return None
    cleaned = text.strip().lower().replace("μ", "µ")
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace("per", "/")
    for key, unit in _FLUX_UNIT_ALIASES.items():
        if key in cleaned:
            return unit
    if cleaned in {"", "flux"}:
        return None
    return None


def detect_flux_unit(label: str | None) -> Optional[str]:
    if not label:
        return None
    # Look inside parentheses first.
    match = re.search(r"\(([^)]+)\)", label)
    if match:
        unit = _normalise_flux_unit(match.group(1))
        if unit:
            return unit.key
    tokens = re.findall(r"[A-Za-zµ/^-]+", label.replace("μ", "µ"))
    for token in tokens:
        unit = _normalise_flux_unit(token)
        if unit:
            return unit.key
    return None


def _resolve_flux_unit(unit: str | None) -> _FluxUnit:
    resolved = _normalise_flux_unit(unit)
    if resolved is not None:
        return resolved
    # Default to arbitrary F_lambda if unknown.
    return _FLUX_UNIT_ALIASES["w/m^2/m"]


def flux_to_f_lambda(
    values: Sequence[float],
    wavelength_m: Sequence[float],
    unit: str | None,
    log: Optional[ConversionLog] = None,
    stage: str = "flux",
) -> Tuple[np.ndarray, str, str]:
    info = _resolve_flux_unit(unit)
    arr = np.asarray(values, dtype=float)
    wl = np.asarray(wavelength_m, dtype=float)

    if info.kind == "F_lambda":
        converted = arr * info.to_si
        formula = "Fλ_SI = Fλ_unit × factor"
        target = "W m⁻² m⁻¹"
        flux_kind = "F_lambda"
    elif info.kind == "F_nu":
        spectral = arr * info.to_si
        with np.errstate(divide="ignore", invalid="ignore"):
            converted = np.where(wl > 0.0, spectral * (wl ** 2) / SPEED_OF_LIGHT, np.nan)
        formula = "Fλ = Fν × λ² / c"
        target = "W m⁻² m⁻¹"
        flux_kind = "F_lambda"
    elif info.kind == "dimensionless":
        converted = arr
        formula = "Dimensionless quantity (no conversion)"
        target = info.display
        flux_kind = "dimensionless"
    else:  # counts or unknown
        converted = arr
        formula = "Counts retained"
        target = info.display
        flux_kind = info.kind

    if log is not None:
        log.add(
            stage,
            original_unit=info.key,
            target_unit=target,
            formula=formula,
            factor=getattr(info, "to_si", 1.0),
        )
    return converted, target, flux_kind


def convert_uncertainty(
    uncertainty: Sequence[float] | None,
    wavelength_m: Sequence[float],
    original_unit: str | None,
    flux_kind: str,
    log: Optional[ConversionLog] = None,
) -> Optional[np.ndarray]:
    if uncertainty is None:
        return None
    arr = np.asarray(uncertainty, dtype=float)
    if flux_kind == "F_lambda":
        converted, _, _ = flux_to_f_lambda(arr, wavelength_m, original_unit, log, stage="uncertainty")
        return converted
    if log is not None and original_unit:
        log.add(
            "uncertainty",
            original_unit=original_unit,
            target_unit=original_unit,
            formula="Uncertainty left unchanged",
        )
    return arr


def infer_axis_assignment(values: Sequence[float], flux_kind: str) -> str:
    arr = np.asarray(values, dtype=float)
    finite = arr[np.isfinite(arr)]
    if flux_kind in {"dimensionless"}:
        return "absorption"
    if finite.size == 0:
        return "emission"
    if np.nanmedian(finite) < 0:
        return "absorption"
    negative_fraction = np.mean(finite < 0) if finite.size else 0.0
    if negative_fraction > 0.5:
        return "absorption"
    return "emission"


def format_flux_unit(unit: str) -> str:
    if not unit:
        return ""
    if unit in {"W m⁻² m⁻¹", "W/m^2/m"}:
        return "W m⁻² m⁻¹"
    return unit


def convert_wavelength_for_display(wavelength_m: Sequence[float], unit: str) -> Tuple[np.ndarray, str]:
    converted = wavelength_from_m(wavelength_m, unit)
    if unit == "Å":
        return converted, "Wavelength (Å)"
    if unit in {"µm", "um"}:
        return converted, "Wavelength (µm)"
    if unit in {"cm^-1", "cm⁻¹", "cm-1"}:
        return converted, "Wavenumber (cm⁻¹)"
    return converted, "Wavelength (nm)" if unit == "nm" else f"Wavelength ({unit})"


__all__ = [
    "ConversionEvent",
    "ConversionLog",
    "LogSink",
    "SPEED_OF_LIGHT",
    "detect_wavelength_unit",
    "wavelength_to_m",
    "wavelength_from_m",
    "detect_flux_unit",
    "flux_to_f_lambda",
    "convert_uncertainty",
    "infer_axis_assignment",
    "format_flux_unit",
    "convert_wavelength_for_display",
]
