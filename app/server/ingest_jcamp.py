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
from .ir_units import IRMeta, to_A10
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


def infer_step(line_start_values: List[float], deltax: float) -> float:
    if len(line_start_values) > 1 and line_start_values[1] < line_start_values[0]:
        return -abs(float(deltax))
    return abs(float(deltax))


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
        "first_y": None,
        "path_length_m": None,
        "mole_fraction": None,
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
            elif upper == "FIRSTY":
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["first_y"] = parsed
                    metadata.setdefault("reported_first_y", parsed)
            elif upper in {"PATHLENGTH", "PATH LENGTH", "PATH_LENGTH"}:
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["path_length_m"] = parsed
                    metadata.setdefault("path_length_reported_m", parsed)
            elif upper in {"MOLEFRACTION", "MOLE FRACTION", "MOLE_FRACTION", "MOLFRAC"}:
                parsed = _parse_float(value_clean)
                if parsed is not None:
                    context["mole_fraction"] = parsed
                    metadata.setdefault("mole_fraction_reported", parsed)
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
    raw_y_values: List[float] = []

    format_token = preferred_section.get("format", "").upper()
    use_delta = "++" in format_token and delta is not None

    line_start_values = [
        numbers[0] * x_factor
        for numbers in section_lines
        if numbers
    ]

    step: Optional[float] = None
    if use_delta:
        step = infer_step(line_start_values, float(delta)) if delta is not None else 0.0
        for numbers in section_lines:
            base = numbers[0] * x_factor
            samples = numbers[1:]
            if not samples:
                continue
            for index, sample in enumerate(samples):
                x_values.append(base + index * (step or 0.0))
                raw_y_values.append(sample)
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
                raw_y_values.append(y_raw)

    if not x_values or not raw_y_values:
        raise ValueError("JCAMP payload did not produce any spectral samples")

    wavelength_array = np.asarray(x_values, dtype=float)
    raw_flux_array = np.asarray(raw_y_values, dtype=float)
    scaled_flux_array = raw_flux_array * y_factor
    finite = np.isfinite(wavelength_array) & np.isfinite(scaled_flux_array)
    wavelength_array = wavelength_array[finite]
    raw_flux_array = raw_flux_array[finite]
    scaled_flux_array = scaled_flux_array[finite]

    if wavelength_array.size == 0 or scaled_flux_array.size == 0:
        raise ValueError("JCAMP payload only contained non-finite samples")

    reported_unit = section_context.get("x_units")
    resolved_unit = _normalise_wavelength_unit(str(reported_unit) if reported_unit else None)
    try:
        wavelength_quantity, canonical_unit = to_nm(wavelength_array, resolved_unit)
    except ValueError:
        wavelength_quantity, canonical_unit = to_nm(wavelength_array, "nm")

    wavelength_nm = np.asarray(wavelength_quantity.to_value(u.nm), dtype=float)

    flux_unit_label = section_context.get("y_units") or metadata.get("reported_flux_unit")
    path_length = section_context.get("path_length_m")
    mole_fraction = section_context.get("mole_fraction")
    first_y_reported = section_context.get("first_y")

    def _scale_header(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value) * float(x_factor)
        except Exception:
            return None

    reported_first_x = _scale_header(section_context.get("first_x"))
    reported_last_x = _scale_header(section_context.get("last_x"))
    delta_value = float(delta) if delta is not None else None
    inferred_step = float(step) if step is not None else None

    first_scaled_values = [float(value) for value in scaled_flux_array[:3].tolist()]
    first_scaled_y = float(scaled_flux_array[0]) if scaled_flux_array.size else None
    verified = True
    verification_warning: Optional[str] = None
    if first_y_reported is not None and first_scaled_y is not None:
        try:
            denominator = max(1.0, abs(float(first_y_reported)))
            delta_first = abs(first_scaled_y - float(first_y_reported)) / denominator
            if delta_first >= 1e-3:
                verified = False
                verification_warning = (
                    "FIRSTY header differs from scaled sample"
                    f" ({first_y_reported} vs {first_scaled_y})"
                )
        except Exception:
            verified = False
            verification_warning = "Unable to verify FIRSTY header against scaled sample."

    ir_meta = IRMeta(
        yunits=str(flux_unit_label or ""),
        yfactor=float(y_factor or 1.0),
        path_m=float(path_length) if path_length is not None else None,
        mole_fraction=float(mole_fraction) if mole_fraction is not None else None,
    )

    final_flux_array = np.asarray(scaled_flux_array, dtype=float)
    flux_unit_output = str(flux_unit_label or "arb")
    flux_kind = "absolute"
    conversion_state = "raw"
    conversion_error: Optional[str] = None
    conversion_details: Optional[Dict[str, object]] = None
    needs_parameters = False

    try:
        converted_flux, conversion_details = to_A10(raw_flux_array, ir_meta)
    except ValueError as exc:
        message = str(exc)
        if "Unsupported YUNITS" in message:
            raise
        conversion_error = message
        if "Need path length" in message:
            needs_parameters = True
            conversion_state = "pending"
        else:
            conversion_state = "error"
    else:
        final_flux_array = np.asarray(converted_flux, dtype=float)
        flux_unit_output = "Absorbance (A10)"
        flux_kind = "relative"
        conversion_state = "converted"

    x_descending = bool(
        wavelength_nm.size >= 2 and float(wavelength_nm[0]) > float(wavelength_nm[-1])
    )

    ir_details: Dict[str, object] = {
        "YUNITS": flux_unit_label,
        "YFACTOR": float(y_factor),
        "FIRSTX": reported_first_x,
        "LASTX": reported_last_x,
        "DELTAX": delta_value,
        "inferred_step": inferred_step,
        "first_scaled_y_values": first_scaled_values,
        "conversion_from": conversion_details.get("from") if conversion_details else None,
        "firsty_reported": first_y_reported,
        "firsty_verified": verified,
        "path_m": ir_meta.path_m,
        "mole_fraction": ir_meta.mole_fraction,
    }

    flux_unit, flux_kind_normalised = _normalise_flux_unit(
        str(flux_unit_output) if flux_unit_output else None
    )
    flux_kind = flux_kind_normalised

    metadata.setdefault("flux_unit", flux_unit)
    metadata["flux_unit"] = flux_unit
    metadata["flux_unit_output"] = flux_unit_output
    metadata["flux_unit_display"] = flux_unit_output
    if flux_unit_label and "flux_unit_input" not in metadata:
        metadata["flux_unit_input"] = flux_unit_label
    metadata["ir_sanity"] = ir_details
    metadata["ir_requires_parameters"] = needs_parameters
    metadata["ir_conversion_state"] = conversion_state
    metadata["ir_verified"] = bool(verified)
    metadata["ir_x_descending"] = x_descending
    metadata["wavelength_direction"] = "descending" if x_descending else "ascending"
    metadata["ir_path_m"] = ir_meta.path_m
    metadata["ir_mole_fraction"] = ir_meta.mole_fraction
    if verification_warning:
        metadata["ir_warning"] = verification_warning
    if conversion_error:
        metadata["ir_conversion_error"] = conversion_error

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

    provenance_units: Dict[str, object] = {
        "wavelength_converted_to": "nm",
        "flux_unit": flux_unit_output,
    }
    if reported_unit:
        provenance_units["wavelength_reported"] = reported_unit
    provenance_units["wavelength_original"] = canonical_unit
    if flux_unit_label:
        provenance_units["flux_input"] = flux_unit_label
    provenance_units["flux_output"] = flux_unit_output
    provenance["units"] = provenance_units
    provenance["samples"] = int(wavelength_nm.size)
    provenance["section_kind"] = preferred_section.get("kind")
    provenance["format_hint"] = preferred_section.get("format")

    if first_scaled_y is not None:
        verification_entry = {
            "reported": first_y_reported,
            "scaled": first_scaled_y,
            "match": verified,
        }
        provenance.setdefault("verifications", {})
        provenance["verifications"]["firsty"] = verification_entry

    ir_conversion_record: Dict[str, object] = {
        "status": conversion_state,
        "yunits_in": flux_unit_label,
        "yfactor": float(y_factor),
    }
    if ir_meta.path_m is not None:
        ir_conversion_record["path_m"] = ir_meta.path_m
    if ir_meta.mole_fraction is not None:
        ir_conversion_record["mole_fraction"] = ir_meta.mole_fraction
    if conversion_details:
        ir_conversion_record["details"] = conversion_details
    if conversion_error:
        ir_conversion_record["error"] = conversion_error
    if needs_parameters:
        ir_conversion_record["requires_parameters"] = True
    provenance["ir_conversion"] = ir_conversion_record

    axis = (
        _normalise_axis(flux_unit_output)
        or _normalise_axis(data_type)
        or "emission"
    )

    tiers = build_downsample_tiers(wavelength_nm, final_flux_array, strategy="lttb")

    extras: Dict[str, object] = {
        "ir_context": {
            "raw_y": raw_flux_array.tolist(),
            "y_factor": float(y_factor),
            "y_units": flux_unit_label,
            "path_m": ir_meta.path_m,
            "mole_fraction": ir_meta.mole_fraction,
            "conversion_state": conversion_state,
            "needs_parameters": needs_parameters,
            "conversion_details": conversion_details,
            "conversion_error": conversion_error,
            "first_scaled_y_values": first_scaled_values,
        },
        "ir_sanity": ir_details,
    }

    label_hint = next((candidate for candidate in [names[0] if names else None, title]), None)

    payload: Dict[str, object] = {
        "label_hint": label_hint,
        "wavelength_nm": wavelength_nm.tolist(),
        "wavelength": {"values": wavelength_nm.tolist(), "unit": "nm"},
        "wavelength_quantity": wavelength_quantity,
        "flux": final_flux_array.tolist(),
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
        "extras": extras,
    }

    return payload


__all__ = ["parse_jcamp"]
