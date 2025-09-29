from __future__ import annotations

import hashlib
import io
import math
import re
from array import array
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from app.utils.downsample import build_downsample_tiers
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


LINEAR_SCALE_FACTORS = {
    "Å": 0.1,
    "µm": 1000.0,
    "mm": 1_000_000.0,
    "cm": 10_000_000.0,
    "m": 1_000_000_000.0,
    "pm": 0.001,
    "in": 25_400_000.0,
}


def checksum_bytes(content: bytes) -> str:
    """Return a stable SHA-256 digest for the provided payload."""

    return hashlib.sha256(content).hexdigest()


def _parse_numeric_token(token: str) -> Optional[float]:
    cleaned = token.strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace("D", "E").replace("d", "E")
    try:
        return float(cleaned)
    except ValueError:
        return None


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
    candidates.append(lowered)
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


def _convert_wavelengths_to_nm_array(values: np.ndarray, canonical_unit_name: str) -> np.ndarray:
    if values.size == 0:
        return np.asarray(values, dtype=float)
    canonical = canonical_unit(canonical_unit_name) if canonical_unit_name else "nm"
    base = np.asarray(values, dtype=float)
    if canonical == "nm":
        return base
    if canonical == "cm^-1":
        converted = np.full(base.shape, np.nan, dtype=float)
        nonzero = base != 0
        converted[nonzero] = 1.0e7 / base[nonzero]
        return converted
    factor = LINEAR_SCALE_FACTORS.get(canonical)
    if factor is not None:
        return base * factor
    return np.asarray(to_nm(base.tolist(), canonical), dtype=float)


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


def _series_summary(sample_count: int, metadata: Mapping[str, object], flux_unit: str) -> str:
    parts = [f"{sample_count} samples"]
    wavelength_range = metadata.get("wavelength_range_nm")
    if (
        isinstance(wavelength_range, (list, tuple))
        and len(wavelength_range) == 2
    ):
        try:
            low = float(wavelength_range[0])
            high = float(wavelength_range[1])
        except (TypeError, ValueError):  # pragma: no cover - defensive
            pass
        else:
            parts.append(f"{low:.2f}–{high:.2f} nm")
    if flux_unit:
        parts.append(f"Flux: {flux_unit}")
    instrument = metadata.get("instrument")
    if isinstance(instrument, str) and instrument.strip():
        parts.append(instrument.strip())
    observation = metadata.get("observation_date")
    if isinstance(observation, str) and observation.strip():
        parts.append(observation.strip())
    return " • ".join(parts)


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

    numeric = dataframe.copy()
    for column in numeric.columns:
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")

    working = numeric[[wavelength_col, flux_col]].dropna()
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
        wavelength_series = working[wavelength_col]
        wavelength_nm = to_nm(wavelength_series.tolist(), wavelength_unit)
    except ValueError:
        wavelength_series = working[wavelength_col]
        wavelength_nm = to_nm(wavelength_series.tolist(), assumed_unit)
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

    metadata["wavelength_range_nm"] = [float(min(wavelength_nm)), float(max(wavelength_nm))]
    metadata.setdefault("wavelength_effective_range_nm", metadata["wavelength_range_nm"])
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

    numeric_valid = numeric.loc[working.index].copy()
    numeric_valid["__wavelength_nm"] = list(float(value) for value in wavelength_nm)

    additional_traces: List[Dict[str, object]] = []
    for column in column_labels:
        if column in {wavelength_col, flux_col}:
            continue
        if column not in numeric_valid.columns:
            continue
        series = numeric_valid[column]
        if series is None:
            continue
        series_values = series.to_numpy(dtype=float, copy=False)
        finite_mask = np.isfinite(series_values)
        if int(np.count_nonzero(finite_mask)) < 3:
            continue
        indices = series.index[finite_mask]
        subset = numeric_valid.loc[indices, ["__wavelength_nm", column]]
        if subset.empty:
            continue
        wavelengths_extra = [float(value) for value in subset["__wavelength_nm"].tolist()]
        flux_extra = [float(value) for value in subset[column].tolist()]
        tiers = build_downsample_tiers(
            np.asarray(wavelengths_extra, dtype=float),
            np.asarray(flux_extra, dtype=float),

            strategy="lttb",

        )
        extra_metadata = dict(metadata)
        extra_metadata["points"] = len(wavelengths_extra)
        additional_traces.append(
            {
                "label": str(column),
                "wavelength_nm": wavelengths_extra,
                "flux": flux_extra,
                "flux_unit": flux_unit,
                "flux_kind": flux_kind,
                "axis": axis,
                "metadata": extra_metadata,
                "summary": _series_summary(len(wavelengths_extra), extra_metadata, flux_unit),
                "downsample": {
                    int(level): {
                        "wavelength_nm": list(result.wavelength_nm),
                        "flux": list(result.flux),
                    }
                    for level, result in tiers.items()
                },
            }
        )

    payload: Dict[str, object] = {
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

    if additional_traces:
        payload["additional_traces"] = additional_traces

    return payload


def parse_ascii_segments(
    segments: Sequence[Tuple[str, bytes]] | Iterable[Tuple[str, bytes]],
    *,
    root_filename: Optional[str] = None,
    chunk_size: int = 500_000,
    assumed_unit: str = "nm",
) -> Dict[str, object]:
    """Parse a collection of ASCII spectrum segments into a unified payload."""

    if isinstance(segments, Sequence):
        iterable = list(segments)
    else:
        iterable = list(segments)
    if not iterable:
        raise ValueError("No ASCII segments provided for parsing")

    checksum = hashlib.sha256()
    header_lines: List[str] = []
    total_samples = 0
    skipped_rows = 0
    segment_summaries: List[Dict[str, object]] = []

    wavelengths = array("d")
    flux_values = array("d")
    auxiliary = array("d")
    auxiliary_used = False

    for name, payload in iterable:
        checksum.update(payload)
        stream = io.BytesIO(payload)
        reader = io.TextIOWrapper(stream, encoding="utf-8", errors="ignore")
        segment_headers: List[str] = []
        segment_samples = 0
        data_started = False
        for raw in reader:
            stripped = raw.strip()
            if not stripped:
                continue
            tokens = stripped.split()
            if len(tokens) < 2:
                if not data_started:
                    segment_headers.append(raw.rstrip("\n"))
                else:
                    skipped_rows += 1
                continue
            first = _parse_numeric_token(tokens[0])
            second = _parse_numeric_token(tokens[1])
            if first is None or second is None:
                if not data_started:
                    segment_headers.append(raw.rstrip("\n"))
                else:
                    skipped_rows += 1
                continue
            data_started = True
            wavelengths.append(float(first))
            flux_values.append(float(second))
            third_value: Optional[float] = None
            if len(tokens) >= 3:
                third_value = _parse_numeric_token(tokens[2])
            if third_value is None:
                auxiliary.append(float("nan"))
            else:
                auxiliary.append(float(third_value))
                auxiliary_used = True
            segment_samples += 1
            total_samples += 1
        header_lines.extend(segment_headers)
        segment_summary = {
            "name": name,
            "samples": segment_samples,
            "header_lines": segment_headers,
        }
        segment_summaries.append(segment_summary)

    if not wavelengths:
        raise ValueError("No numeric samples detected across ASCII segments")

    wavelength_array = np.asarray(wavelengths, dtype=float)
    flux_array = np.asarray(flux_values, dtype=float)
    aux_array = np.asarray(auxiliary, dtype=float)

    metadata, raw_headers, label_candidates, axis_hint, header_unit_hint, header_flux_hint = _collect_header_metadata(
        header_lines
    )

    resolved_unit = header_unit_hint or assumed_unit
    unit_inference: Dict[str, object] = {"header": header_unit_hint, "assumed": assumed_unit}
    try:
        canonical_wavelength_unit = canonical_unit(resolved_unit)
    except ValueError:
        resolved_unit = assumed_unit
        canonical_wavelength_unit = canonical_unit(resolved_unit)
        unit_inference["fallback"] = assumed_unit

    if not metadata.get("reported_wavelength_unit"):
        metadata["reported_wavelength_unit"] = resolved_unit
    metadata.setdefault("original_wavelength_unit", canonical_wavelength_unit)

    wavelength_nm = _convert_wavelengths_to_nm_array(wavelength_array, canonical_wavelength_unit)

    finite_mask = np.isfinite(wavelength_nm) & np.isfinite(flux_array)
    dropped_nonfinite = int(finite_mask.size - int(np.count_nonzero(finite_mask)))
    if dropped_nonfinite:
        wavelength_nm = wavelength_nm[finite_mask]
        flux_array = flux_array[finite_mask]
        aux_array = aux_array[finite_mask]
    else:
        wavelength_nm = np.asarray(wavelength_nm, dtype=float)
        flux_array = np.asarray(flux_array, dtype=float)
        aux_array = np.asarray(aux_array, dtype=float)

    if wavelength_nm.size == 0:
        raise ValueError("No numeric samples available after unit normalisation")

    order = np.argsort(wavelength_nm, kind="mergesort")
    wavelength_nm = wavelength_nm[order]
    flux_array = flux_array[order]
    aux_array = aux_array[order]

    pre_unique_samples = int(wavelength_nm.size)
    wavelength_nm, unique_idx = np.unique(wavelength_nm, return_index=True)
    flux_array = flux_array[unique_idx]
    aux_array = aux_array[unique_idx]
    unique_samples = int(wavelength_nm.size)
    deduplicated_samples = max(pre_unique_samples - unique_samples, 0)

    auxiliary_used = bool(np.isfinite(aux_array).any())

    flux_unit_label = header_flux_hint or metadata.get("flux_unit")
    flux_unit, flux_kind = _normalise_flux_unit(flux_unit_label)
    metadata["flux_unit"] = flux_unit
    if flux_unit_label and not metadata.get("reported_flux_unit"):
        metadata["reported_flux_unit"] = flux_unit_label

    metadata["points"] = int(unique_samples)
    min_nm = float(np.nanmin(wavelength_nm))
    max_nm = float(np.nanmax(wavelength_nm))
    metadata["wavelength_range_nm"] = [min_nm, max_nm]
    metadata.setdefault("wavelength_effective_range_nm", [min_nm, max_nm])
    metadata.setdefault("data_wavelength_range_nm", [min_nm, max_nm])
    metadata.setdefault("dense_chunk_size", int(chunk_size))
    if root_filename:
        metadata.setdefault("filename", root_filename)
    metadata.setdefault("segments", [summary["name"] for summary in segment_summaries])

    provenance: Dict[str, object] = {
        "format": "ascii",
        "checksum": checksum.hexdigest(),
        "samples": int(unique_samples),
        "unit_inference": {**unit_inference, "resolved": resolved_unit},
        "segments": segment_summaries,
        "dense_parser": {
            "chunk_size": int(chunk_size),
            "segments": len(segment_summaries),
            "skipped_rows": int(skipped_rows),
            "total_rows": int(total_samples + skipped_rows),
            "unique_samples": int(unique_samples),
        },
    }
    dense_meta = provenance["dense_parser"]
    if dropped_nonfinite:
        dense_meta["dropped_nonfinite"] = int(dropped_nonfinite)
    if deduplicated_samples:
        dense_meta["deduplicated_samples"] = int(deduplicated_samples)
    if root_filename:
        provenance["filename"] = root_filename
    if raw_headers:
        provenance["header_fields"] = raw_headers
    if header_lines:
        provenance["header_lines"] = [line for line in header_lines if line.strip()]

    chunk_ranges: List[Dict[str, object]] = []
    if chunk_size > 0:
        for offset in range(0, wavelength_nm.size, chunk_size):
            end = min(offset + chunk_size, wavelength_nm.size)
            segment = wavelength_nm[offset:end]
            if segment.size == 0:
                continue
            chunk_ranges.append(
                {
                    "offset": int(offset),
                    "start_nm": float(segment[0]),
                    "end_nm": float(segment[-1]),
                    "samples": int(segment.size),
                }
            )
    provenance["chunks"] = list(chunk_ranges)

    conversions: Dict[str, object] = {}
    original_unit = metadata.get("original_wavelength_unit")
    if original_unit and str(original_unit).lower() != "nm":
        conversions["wavelength_unit"] = {"from": original_unit, "to": "nm"}
    reported_flux = metadata.get("reported_flux_unit")
    if reported_flux and str(reported_flux) != flux_unit:
        conversions["flux_unit"] = {"from": reported_flux, "to": flux_unit}
    if conversions:
        provenance["conversions"] = conversions

    provenance_units: Dict[str, object] = {"wavelength_converted_to": "nm", "flux_unit": flux_unit}
    if resolved_unit:
        provenance_units["wavelength_input"] = resolved_unit
    reported_unit = metadata.get("reported_wavelength_unit")
    if reported_unit:
        provenance_units["wavelength_reported"] = reported_unit
    original_unit = metadata.get("original_wavelength_unit")
    if original_unit:
        provenance_units["wavelength_original"] = original_unit
    if flux_unit_label:
        provenance_units["flux_input"] = flux_unit_label
    provenance["units"] = provenance_units

    axis = _normalise_axis(axis_hint) or "emission"
    label_hint = next((candidate for candidate in label_candidates if candidate), None)

    auxiliary_values: Optional[np.ndarray]
    if auxiliary_used:
        auxiliary_values = aux_array
        finite_aux = auxiliary_values[np.isfinite(auxiliary_values)]
        if finite_aux.size:
            metadata.setdefault(
                "auxiliary_statistics",
                {
                    "min": float(np.nanmin(finite_aux)),
                    "max": float(np.nanmax(finite_aux)),
                    "mean": float(np.nanmean(finite_aux)),
                    "samples": int(finite_aux.size),
                },
            )
    else:
        auxiliary_values = None

    tiers = build_downsample_tiers(wavelength_nm, flux_array, strategy="lttb")
    provenance["downsample_tiers"] = sorted(int(key) for key in tiers)

    payload = {
        "label_hint": label_hint,
        "wavelength_nm": [float(value) for value in wavelength_nm.tolist()],
        "flux": [float(value) for value in flux_array.tolist()],
        "auxiliary": [float(value) for value in auxiliary_values.tolist()] if auxiliary_values is not None else None,
        "flux_unit": flux_unit,
        "flux_kind": flux_kind,
        "metadata": metadata,
        "provenance": provenance,
        "axis": axis,
        "kind": "spectrum",
        "chunk_ranges": chunk_ranges,
        "downsample": {
            int(level): {
                "wavelength_nm": list(result.wavelength_nm),
                "flux": list(result.flux),
            }
            for level, result in tiers.items()
        },
    }
    return payload
