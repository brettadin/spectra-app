from __future__ import annotations

import hashlib
import math
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from .units import canonical_unit, to_nm


HEADER_ALIAS_MAP = {
    "instrument": "instrument",
    "instrume": "instrument",
    "spectrograph": "instrument",
    "spectrograph_name": "instrument",
    "spectro": "instrument",
    "detector": "detector",
    "telescope": "telescope",
    "telescop": "telescope",
    "facility": "telescope",
    "observatory": "telescope",
    "observatory_name": "telescope",
    "object": "target",
    "object_name": "target",
    "target": "target",
    "target_name": "target",
    "source": "source",
    "source_name": "source",
    "title": "title",
    "label": "title",
    "name": "title",
    "program": "program",
    "programme": "program",
    "proposal": "program",
    "prop_id": "program",
    "observer": "observer",
    "pi": "principal_investigator",
    "principal_investigator": "principal_investigator",
    "exptime": "exposure",
    "exposure": "exposure",
    "airmass": "airmass",
    "slit": "slit",
    "aperture": "aperture",
    "grating": "grating",
    "grism": "grating",
    "filter": "filter",
    "mode": "mode",
    "resolution": "resolution",
    "resolving_power": "resolution",
    "r": "resolution",
    "flux_unit": "flux_unit",
    "flux_units": "flux_unit",
    "fluxunits": "flux_unit",
    "fluxunit": "flux_unit",
    "bunit": "flux_unit",
    "unit_flux": "flux_unit",
    "wavelength_unit": "wavelength_unit",
    "waveunit": "wavelength_unit",
    "unit_wavelength": "wavelength_unit",
    "wavelength_units": "wavelength_unit",
    "xunit": "wavelength_unit",
    "xunits": "wavelength_unit",
    "axis": "axis",
    "specaxis": "axis",
    "spectrum_type": "axis",
    "range": "wavelength_range",
    "wavelength_range": "wavelength_range",
    "spectral_range": "wavelength_range",
    "wave_range": "wavelength_range",
    "coverage": "wavelength_range",
    "lambda_min": "wavelength_start",
    "lambda_max": "wavelength_end",
    "start": "wavelength_start",
    "end": "wavelength_end",
    "date_obs": "observation_date",
    "date-obs": "observation_date",
    "dateobs": "observation_date",
    "date": "observation_date",
    "observation_date": "observation_date",
    "utdate": "observation_date",
    "utc": "observation_date",
    "time": "observation_date",
    "mjd": "mjd",
    "observer_date": "observation_date",
}

UNIT_PATTERN = re.compile(r"\(([^)]+)\)|\[([^\]]+)\]")
RANGE_NUMERIC = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def checksum_bytes(content: bytes) -> str:
    """Return a stable SHA-256 digest for the provided payload."""

    return hashlib.sha256(content).hexdigest()


def _normalise_header_key(key: str) -> str:
    cleaned = key.strip().lower().replace("μ", "µ")
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def _split_header_line(line: str) -> Optional[Tuple[str, str]]:
    stripped = line.strip()
    if not stripped:
        return None
    stripped = stripped.lstrip("#").strip()
    if not stripped:
        return None
    for sep in (":", "=", "\t"):
        if sep in stripped:
            key, value = stripped.split(sep, 1)
            return key.strip(), value.strip()
    parts = stripped.split(None, 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None


def _extract_unit_hint(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    lowered = str(text).strip()
    if not lowered:
        return None
    lowered = lowered.replace("μ", "µ")
    candidates: List[str] = []
    for match in UNIT_PATTERN.findall(lowered):
        candidates.extend(filter(None, match))
    pieces = re.split(r"[\s_\-\/]+", lowered)
    candidates.extend(pieces)
    for candidate in candidates:
        norm = candidate.strip().lower()
        if not norm:
            continue
        if "angstrom" in norm or norm in {"å", "a", "ångström", "ångstrom"}:
            return "Å"
        if norm in {"nm", "nanometer", "nanometers"}:
            return "nm"
        if norm in {"um", "µm", "micron", "microns", "micrometer", "micrometers"}:
            return "µm"
        if "cm" in norm and "-1" in norm:
            return "cm^-1"
        if norm in {"cm^-1", "cm-1"}:
            return "cm^-1"
        if "wavenumber" in norm:
            return "cm^-1"
    return None


def _parse_range_value(value: str, default_unit: str) -> Optional[Tuple[float, float]]:
    numbers = [float(part) for part in RANGE_NUMERIC.findall(value)]
    if len(numbers) < 2:
        return None
    low, high = numbers[0], numbers[1]
    if math.isclose(low, high):
        return None
    unit = _extract_unit_hint(value) or default_unit
    try:
        converted = to_nm([low, high], unit)
    except Exception:
        converted = [low, high]
    low_nm, high_nm = float(min(converted)), float(max(converted))
    if not math.isfinite(low_nm) or not math.isfinite(high_nm):
        return None
    return low_nm, high_nm


def _collect_header_metadata(
    header_lines: Sequence[str],
) -> Tuple[Dict[str, object], Dict[str, str], List[str], Optional[str], Optional[str], Optional[str]]:
    metadata: Dict[str, object] = {}
    raw: Dict[str, str] = {}
    label_candidates: List[str] = []
    axis_hint: Optional[str] = None
    wavelength_unit_hint: Optional[str] = None
    flux_unit_hint: Optional[str] = None

    for line in header_lines:
        pair = _split_header_line(line)
        if not pair:
            continue
        key, value = pair
        value = value.strip().strip("'\"")
        norm_key = _normalise_header_key(key)
        if not norm_key:
            continue
        raw[norm_key] = value
        alias = HEADER_ALIAS_MAP.get(norm_key, norm_key)
        if alias == "instrument":
            metadata.setdefault("instrument", value)
        elif alias == "telescope":
            metadata.setdefault("telescope", value)
        elif alias == "target":
            metadata.setdefault("target", value)
            label_candidates.append(value)
        elif alias == "source":
            metadata.setdefault("source", value)
            label_candidates.append(value)
        elif alias == "title":
            metadata.setdefault("title", value)
            label_candidates.append(value)
        elif alias == "observation_date":
            metadata.setdefault("observation_date", value)
        elif alias == "flux_unit":
            metadata.setdefault("flux_unit", value)
            metadata.setdefault("reported_flux_unit", value)
            flux_unit_hint = flux_unit_hint or value
        elif alias == "wavelength_unit":
            metadata.setdefault("reported_wavelength_unit", value)
            wavelength_unit_hint = wavelength_unit_hint or _extract_unit_hint(value)
        elif alias == "axis":
            metadata.setdefault("axis", value)
            axis_hint = axis_hint or value
        elif alias == "wavelength_range":
            parsed = _parse_range_value(value, "nm")
            if parsed:
                metadata.setdefault("wavelength_effective_range_nm", list(parsed))
        elif alias == "wavelength_start":
            metadata.setdefault("wavelength_start", value)
        elif alias == "wavelength_end":
            metadata.setdefault("wavelength_end", value)
        else:
            metadata.setdefault(alias, value)

    return metadata, raw, label_candidates, axis_hint, wavelength_unit_hint, flux_unit_hint


def _detect_columns(df: pd.DataFrame) -> Tuple[str, str]:
    columns = list(df.columns)
    if len(columns) < 2:
        raise ValueError("Missing wavelength or flux column in ASCII data")

    wavelength = columns[0]
    flux = columns[1]
    for name in columns:
        label = str(name).lower()
        if any(keyword in label for keyword in ("wave", "lam", "freq", "wn")):
            wavelength = name
            break
    for name in columns:
        if name == wavelength:
            continue
        label = str(name).lower()
        if any(keyword in label for keyword in ("flux", "int", "power", "counts", "brightness")):
            flux = name
            break
    if wavelength == flux and len(columns) > 2:
        flux = next(col for col in columns if col != wavelength)
    return str(wavelength), str(flux)


def _extract_flux_unit_from_label(label: str) -> Optional[str]:
    matches = UNIT_PATTERN.findall(label)
    for match in matches:
        candidate = next((part for part in match if part), None)
        if candidate:
            cleaned = candidate.strip()
            if cleaned:
                return cleaned
    return None


def _normalise_flux_unit(unit: Optional[str]) -> Tuple[str, str]:
    if not unit:
        return "arb", "relative"
    cleaned = unit.strip()
    if not cleaned:
        return "arb", "relative"
    lowered = cleaned.lower()
    relative_tokens = {"arb", "arbitrary", "adu", "counts", "count", "relative", "norm"}
    if any(token in lowered for token in relative_tokens):
        return cleaned, "relative"
    return cleaned, "absolute"


def _normalise_axis(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lowered = value.strip().lower()
    if not lowered:
        return None
    if "abs" in lowered:
        return "absorption"
    if "trans" in lowered:
        return "transmission"
    if "reflec" in lowered:
        return "reflection"
    if "emiss" in lowered:
        return "emission"
    return value.strip()


def parse_ascii(
    dataframe: pd.DataFrame,
    *,
    content_bytes: bytes,
    header_lines: Sequence[str] | None = None,
    column_labels: Sequence[str] | None = None,
    delimiter: Optional[str] = None,
    filename: Optional[str] = None,
    assumed_unit: str = "nm",
    orientation: Optional[str] = None,
) -> Dict[str, object]:
    """Parse a CSV/TXT spectrum into the normalised overlay payload format."""

    header_lines = list(header_lines or [])
    column_labels = list(column_labels or list(dataframe.columns))

    metadata, raw_headers, label_candidates, axis_hint, header_unit_hint, header_flux_hint = _collect_header_metadata(
        header_lines
    )

    provenance: Dict[str, object] = {
        "format": "ascii",
        "checksum": checksum_bytes(content_bytes),
        "columns": list(column_labels),
    }
    if orientation:
        provenance["orientation"] = orientation
    if filename:
        provenance["filename"] = filename
    if delimiter:
        provenance["delimiter"] = delimiter
    if header_lines:
        provenance["header_lines"] = [line for line in header_lines if line.strip()]
    if raw_headers:
        provenance["header_fields"] = raw_headers

    wavelength_col, flux_col = _detect_columns(dataframe)
    provenance["column_mapping"] = {"wavelength": wavelength_col, "flux": flux_col}

    working = dataframe[[wavelength_col, flux_col]].copy()
    working[wavelength_col] = pd.to_numeric(working[wavelength_col], errors="coerce")
    working[flux_col] = pd.to_numeric(working[flux_col], errors="coerce")
    working = working.dropna()
    if working.empty:
        raise ValueError("No numeric spectral samples available in ASCII data")

    wavelength_label_unit = _extract_unit_hint(wavelength_col)
    wavelength_unit = header_unit_hint or wavelength_label_unit or assumed_unit
    provenance["unit_inference"] = {
        "header": header_unit_hint,
        "column": wavelength_label_unit,
        "assumed": assumed_unit,
    }

    reported_wavelength_unit = wavelength_unit
    try:
        wavelength_nm = to_nm(working[wavelength_col].tolist(), wavelength_unit)
    except ValueError:
        wavelength_nm = to_nm(working[wavelength_col].tolist(), assumed_unit)
        provenance.setdefault("unit_inference", {})["fallback"] = assumed_unit
        wavelength_unit = assumed_unit
    metadata.setdefault("reported_wavelength_unit", reported_wavelength_unit)

    flux_values = working[flux_col].tolist()
    flux_unit_label = header_flux_hint or metadata.get("flux_unit")
    label_flux_unit = _extract_flux_unit_from_label(flux_col)
    if label_flux_unit:
        flux_unit_label = label_flux_unit
    flux_unit, flux_kind = _normalise_flux_unit(flux_unit_label)
    metadata["flux_unit"] = flux_unit
    if flux_unit_label and not metadata.get("reported_flux_unit"):
        metadata["reported_flux_unit"] = flux_unit_label

    data_range = [float(min(wavelength_nm)), float(max(wavelength_nm))]
    metadata.setdefault("data_wavelength_range_nm", data_range)
    metadata.setdefault("wavelength_range_nm", data_range)
    metadata.setdefault(
        "wavelength_effective_range_nm",
        metadata.get("wavelength_range_nm", data_range),
    )
    try:
        metadata["original_wavelength_unit"] = canonical_unit(wavelength_unit)
    except ValueError:
        metadata["original_wavelength_unit"] = wavelength_unit
    metadata.setdefault("points", len(wavelength_nm))

    provenance_units: Dict[str, object] = {"wavelength_converted_to": "nm", "flux_unit": flux_unit}
    if wavelength_unit:
        provenance_units["wavelength_input"] = wavelength_unit
    if metadata.get("reported_wavelength_unit"):
        provenance_units["wavelength_reported"] = metadata["reported_wavelength_unit"]
    if metadata.get("original_wavelength_unit"):
        provenance_units["wavelength_original"] = metadata["original_wavelength_unit"]
    if flux_unit_label:
        provenance_units["flux_input"] = flux_unit_label
    provenance["units"] = provenance_units

    axis = _normalise_axis(axis_hint) or "emission"

    provenance["samples"] = len(wavelength_nm)
    provenance.setdefault("unit_inference", {})["resolved"] = wavelength_unit

    conversions: Dict[str, object] = {}
    original_unit = metadata.get("original_wavelength_unit")
    if original_unit and str(original_unit).lower() != "nm":
        conversions["wavelength_unit"] = {"from": original_unit, "to": "nm"}
    reported_flux = metadata.get("reported_flux_unit")
    if reported_flux and str(reported_flux) != flux_unit:
        conversions["flux_unit"] = {"from": reported_flux, "to": flux_unit}
    if conversions:
        provenance["conversions"] = conversions

    label_hint = next((candidate for candidate in label_candidates if candidate), None)

    return {
        "label_hint": label_hint,
        "wavelength_nm": [float(value) for value in wavelength_nm],
        "flux": [float(value) for value in flux_values],
        "flux_unit": flux_unit,
        "flux_kind": flux_kind,
        "metadata": metadata,
        "provenance": provenance,
        "axis": axis,
        "kind": "spectrum",
    }
