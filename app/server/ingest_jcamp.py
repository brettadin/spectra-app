"""JCAMP-DX spectrum ingestion helpers."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence

import numpy as np
from astropy import units as u

from app.server.ingest_ascii import (
    _normalise_axis,
    _normalise_flux_unit,
    checksum_bytes,
)
from app.utils.downsample import build_downsample_tiers
from .units import to_nm


_NUMBER_PATTERN = re.compile(r"[-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?")


def _parse_float(value: str) -> Optional[float]:
    try:
        cleaned = value.strip().replace(",", "")
        return float(cleaned.replace("D", "E").replace("d", "e"))
    except Exception:
        return None


def _parse_int(value: str) -> Optional[int]:
    parsed = _parse_float(value)
    if parsed is None:
        return None
    try:
        return int(round(parsed))
    except Exception:
        return None


def _normalise_metadata_key(key: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
    return cleaned


def _normalise_wavelength_unit(unit: Optional[str]) -> str:
    if not unit:
        return "nm"
    cleaned = unit.strip()
    if not cleaned:
        return "nm"
    folded = cleaned.lower()
    # Common JCAMP spellings.
    if folded in {"micrometers", "micrometer", "micron", "microns", "µm"}:
        return "micrometer"
    if folded in {"nanometers", "nanometer", "nm"}:
        return "nm"
    normalized = folded.replace(" ", "")
    if normalized in {"1/cm", "cm-1", "cm^-1", "1cm-1", "1percm"}:
        return "cm-1"
    if normalized.endswith("cm-1") or "percm" in normalized:
        return "cm-1"
    if normalized.endswith("um"):
        return "micrometer"
    if normalized.endswith("angstroem"):
        return "angstrom"
    if "angstrom" in normalized:
        return "angstrom"
    return cleaned


def _tokenise_numbers(line: str) -> List[float]:
    matches = _NUMBER_PATTERN.findall(line)
    numbers: List[float] = []
    for match in matches:
        try:
            numbers.append(float(match.replace("D", "E").replace("d", "e")))
        except Exception:
            continue
    return numbers


def _is_uncertainty_unit(unit: Optional[str]) -> bool:
    if not unit:
        return False
    lowered = unit.lower()
    return any(token in lowered for token in ("uncert", "error", "sigma", "stdev", "std", "noise"))


def _estimate_delta(
    lines: Sequence[List[float]],
    x_factor: float,
    reported_delta: Optional[float],
    first_x: Optional[float],
    last_x: Optional[float],
    npoints: Optional[int],
) -> Optional[float]:
    if reported_delta is not None:
        return reported_delta * x_factor
    if (
        first_x is not None
        and last_x is not None
        and npoints is not None
        and npoints > 1
    ):
        return ((last_x - first_x) * x_factor) / (npoints - 1)
    return None


def _collect_number_lines(raw_lines: Sequence[str]) -> List[List[float]]:
    parsed: List[List[float]] = []
    for raw in raw_lines:
        numbers = _tokenise_numbers(raw)
        if numbers:
            parsed.append(numbers)
    return parsed


def parse_jcamp(payload: bytes, filename: Optional[str] = None) -> Dict[str, object]:
    """Parse a JCAMP-DX spectrum payload into a normalised overlay structure."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        text = payload.decode("latin-1", errors="replace")

    lines = text.replace("\r", "\n").splitlines()

    metadata: Dict[str, object] = {}
    provenance: Dict[str, object] = {
        "format": "jcamp",
        "checksum": checksum_bytes(payload),
    }
    if filename:
        provenance["filename"] = filename

    context: Dict[str, object] = {
        "x_units": None,
        "y_units": None,
        "x_factor": 1.0,
        "y_factor": 1.0,
        "delta": None,
        "first_x": None,
        "last_x": None,
        "npoints": None,
    }

    title: Optional[str] = None
    names: List[str] = []
    data_type: Optional[str] = None
    data_sections: List[Dict[str, object]] = []
    active_section: Optional[Dict[str, object]] = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("$$"):
            continue
        if line.startswith("##"):
            fragment = line[2:]
            if "=" in fragment:
                key, value = fragment.split("=", 1)
            else:
                key, value = fragment, ""
            key_clean = key.strip()
            value_clean = value.strip()
            upper = key_clean.upper()

            if upper in {"XYDATA", "XYPOINTS"}:
                section = {
                    "kind": upper,
                    "format": value_clean.upper(),
                    "lines": [],
                    "context": context.copy(),
                }
                data_sections.append(section)
                active_section = section
                continue

            active_section = None

            if upper == "TITLE":
                if value_clean:
                    title = value_clean
                    metadata.setdefault("title", value_clean)
            elif upper == "NAMES":
                candidates = [
                    part.strip()
                    for part in re.split(r"[;,]", value_clean)
                    if part.strip()
                ]
                if candidates:
                    names = candidates
                    metadata.setdefault("names", candidates)
                    metadata.setdefault("target", candidates[0])
            elif upper == "DATA TYPE":
                if value_clean:
                    data_type = value_clean
                    metadata.setdefault("data_type", value_clean)
            elif upper == "JCAMP-DX":
                if value_clean:
                    provenance["jcamp_dx"] = value_clean
            elif upper == "XUNITS":
                if value_clean:
                    context["x_units"] = value_clean
                    metadata.setdefault("reported_wavelength_unit", value_clean)
            elif upper == "YUNITS":
                if value_clean:
                    context["y_units"] = value_clean
                    metadata.setdefault("reported_flux_unit", value_clean)
            elif upper == "XFACTOR":
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["x_factor"] = parsed
            elif upper == "YFACTOR":
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["y_factor"] = parsed
            elif upper == "FIRSTX":
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["first_x"] = parsed
            elif upper == "LASTX":
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["last_x"] = parsed
            elif upper == "NPOINTS":
                parsed = _parse_int(value_clean)
                if parsed is not None:
                    context["npoints"] = parsed
                    metadata.setdefault("reported_points", parsed)
            elif upper == "DELTAX":
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["delta"] = parsed
            elif upper == "END":
                # terminator marker — nothing to record
                continue
            else:
                normalised = _normalise_metadata_key(key_clean)
                if normalised and value_clean:
                    metadata.setdefault(normalised, value_clean)
            continue

        if active_section is not None:
            active_section["lines"].append(line)

    if not data_sections:
        raise ValueError("JCAMP payload does not contain XYDATA or XYPOINTS sections")

    preferred_section = next(
        (
            section
            for section in data_sections
            if not _is_uncertainty_unit(section["context"].get("y_units"))
        ),
        data_sections[0],
    )

    section_lines = _collect_number_lines(preferred_section["lines"])
    if not section_lines:
        raise ValueError("JCAMP payload does not contain numeric samples")

    section_context = preferred_section["context"]
    x_factor = float(section_context.get("x_factor") or 1.0)
    y_factor = float(section_context.get("y_factor") or 1.0)
    delta_raw = section_context.get("delta")
    first_x = section_context.get("first_x")
    last_x = section_context.get("last_x")
    npoints = section_context.get("npoints")
    delta = _estimate_delta(section_lines, x_factor, delta_raw, first_x, last_x, npoints)

    x_values: List[float] = []
    y_values: List[float] = []

    format_token = preferred_section.get("format", "").upper()
    use_delta = "++" in format_token and delta is not None

    if use_delta:
        for numbers in section_lines:
            base = numbers[0] * x_factor
            samples = numbers[1:]
            if not samples:
                continue
            for index, sample in enumerate(samples):
                x_values.append(base + index * delta)
                y_values.append(sample * y_factor)
    else:
        for numbers in section_lines:
            if len(numbers) < 2:
                continue
            paired = numbers
            if len(paired) % 2 != 0:
                paired = paired[:-1]
            iterator = iter(paired)
            for x_raw, y_raw in zip(iterator, iterator):
                x_values.append(x_raw * x_factor)
                y_values.append(y_raw * y_factor)

    if not x_values or not y_values:
        raise ValueError("JCAMP payload did not produce any spectral samples")

    wavelength_array = np.asarray(x_values, dtype=float)
    flux_array = np.asarray(y_values, dtype=float)
    finite = np.isfinite(wavelength_array) & np.isfinite(flux_array)
    wavelength_array = wavelength_array[finite]
    flux_array = flux_array[finite]

    if wavelength_array.size == 0 or flux_array.size == 0:
        raise ValueError("JCAMP payload only contained non-finite samples")

    reported_unit = section_context.get("x_units")
    resolved_unit = _normalise_wavelength_unit(str(reported_unit) if reported_unit else None)
    try:
        wavelength_quantity, canonical_unit = to_nm(wavelength_array, resolved_unit)
    except ValueError:
        wavelength_quantity, canonical_unit = to_nm(wavelength_array, "nm")

    wavelength_nm = np.asarray(wavelength_quantity.to_value(u.nm), dtype=float)

    flux_unit_label = section_context.get("y_units") or metadata.get("reported_flux_unit")
    flux_unit, flux_kind = _normalise_flux_unit(str(flux_unit_label) if flux_unit_label else None)

    metadata.setdefault("flux_unit", flux_unit)
    metadata.setdefault("wavelength_range_nm", [
        float(np.nanmin(wavelength_nm)),
        float(np.nanmax(wavelength_nm)),
    ])
    metadata.setdefault(
        "data_wavelength_range_nm",
        metadata.get("wavelength_range_nm"),
    )
    metadata.setdefault(
        "wavelength_effective_range_nm",
        metadata.get("wavelength_range_nm"),
    )
    metadata.setdefault("original_wavelength_unit", canonical_unit)
    metadata.setdefault("points", int(wavelength_nm.size))

    provenance_units: Dict[str, object] = {"wavelength_converted_to": "nm", "flux_unit": flux_unit}
    if reported_unit:
        provenance_units["wavelength_reported"] = reported_unit
    provenance_units["wavelength_original"] = canonical_unit
    if flux_unit_label:
        provenance_units["flux_input"] = flux_unit_label
    provenance["units"] = provenance_units
    provenance["samples"] = int(wavelength_nm.size)
    provenance["section_kind"] = preferred_section.get("kind")
    provenance["format_hint"] = preferred_section.get("format")

    axis = (
        _normalise_axis(flux_unit_label)
        or _normalise_axis(data_type)
        or "emission"
    )

    tiers = build_downsample_tiers(wavelength_nm, flux_array, strategy="lttb")

    label_hint = next((candidate for candidate in [names[0] if names else None, title]), None)

    payload: Dict[str, object] = {
        "label_hint": label_hint,
        "wavelength_nm": wavelength_nm.tolist(),
        "wavelength": {"values": wavelength_nm.tolist(), "unit": "nm"},
        "wavelength_quantity": wavelength_quantity,
        "flux": flux_array.tolist(),
        "flux_unit": flux_unit,
        "flux_kind": flux_kind,
        "metadata": metadata,
        "provenance": provenance,
        "axis": axis,
        "kind": "spectrum",
        "downsample": {
            int(level): {
                "wavelength_nm": list(result.wavelength_nm),
                "flux": list(result.flux),
            }
            for level, result in tiers.items()
        },
    }

    return payload


__all__ = ["parse_jcamp"]
