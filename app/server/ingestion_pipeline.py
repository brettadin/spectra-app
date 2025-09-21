from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from astropy.io import fits

from app.utils.units import (
    ConversionLog,
    convert_uncertainty,
    convert_wavelength_for_display,
    detect_flux_unit,
    detect_wavelength_unit,
    flux_to_f_lambda,
    infer_axis_assignment,
    wavelength_to_m,
)


def _convert_air_to_vacuum(wavelength_m: np.ndarray, log: ConversionLog) -> np.ndarray:
    lam_a = wavelength_m * 1e10
    sigma2 = (1e4 / np.where(lam_a != 0, lam_a, np.nan)) ** 2
    n = 1 + 0.0000834254 + 0.02406147 / (130 - sigma2) + 0.00015998 / (38.9 - sigma2)
    log.add(
        "wavelength_medium",
        original_unit="air",
        target_unit="vacuum",
        formula="λ_vac = λ_air × n(λ)",
    )
    return wavelength_m * n


def _maybe_air_to_vacuum_metadata(
    wavelength_m: np.ndarray,
    metadata: Mapping[str, object],
    log: ConversionLog,
) -> np.ndarray:
    medium = str(metadata.get("wavelength_medium") or metadata.get("medium") or "").lower()
    if "air" in medium:
        return _convert_air_to_vacuum(wavelength_m, log)
    return wavelength_m


def _estimate_resolution(wavelength_m: np.ndarray) -> Optional[float]:
    finite = np.asarray(wavelength_m, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < 2:
        return None
    sorted_wl = np.sort(finite)
    diffs = np.diff(sorted_wl)
    positive = diffs > 0
    if not np.any(positive):
        return None
    ratios = sorted_wl[1:][positive] / diffs[positive]
    ratios = ratios[np.isfinite(ratios) & (ratios > 0)]
    if ratios.size == 0:
        return None
    return float(np.median(ratios))


@dataclass
class SpectrumSegment:
    """Canonical internal representation of an ingested spectral segment."""

    label: str
    wavelength_m: np.ndarray
    flux: np.ndarray
    flux_unit: str
    flux_kind: str
    uncertainty: Optional[np.ndarray] = None
    metadata: Dict[str, object] = field(default_factory=dict)
    provenance: List[Dict[str, object]] = field(default_factory=list)
    provider: Optional[str] = None

    def as_payload(self) -> Dict[str, object]:
        wavelength_nm = self.wavelength_m * 1e9
        payload = {
            "label": self.label,
            "wavelength_m": self.wavelength_m.tolist(),
            "wavelength_nm": wavelength_nm.tolist(),
            "flux": self.flux.tolist(),
            "flux_unit": self.flux_unit,
            "flux_kind": self.flux_kind,
            "uncertainty": self.uncertainty.tolist() if self.uncertainty is not None else None,
            "metadata": dict(self.metadata),
            "provenance": list(self.provenance),
        }
        if self.provider:
            payload["provider"] = self.provider
        return payload


def checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_header_metadata(lines: Sequence[str]) -> Dict[str, object]:
    metadata: Dict[str, object] = {}
    for raw in lines:
        line = raw.strip().lstrip("#; ")
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            continue
        metadata[key.strip()] = value.strip()
    return metadata


def _find_numeric_start(lines: Sequence[str]) -> int:
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens = [token for token in re.split(r"[\s,;|]+", stripped) if token]
        numeric_tokens = 0
        for token in tokens[:3]:
            try:
                float(token)
            except ValueError:
                break
            else:
                numeric_tokens += 1
        if numeric_tokens >= 2:
            return idx
    return 0


def _decode_text_bytes(data: bytes) -> Tuple[List[str], str]:
    text = data.decode("utf-8", errors="ignore")
    lines = text.splitlines()
    return lines, text


def _resolve_column(columns: Sequence[str], fallback_index: int) -> Tuple[str, Optional[str]]:
    if not columns:
        return str(fallback_index), None
    for column in columns:
        lower = column.lower()
        if any(key in lower for key in ("wave", "lambda", "wl")):
            return column, detect_wavelength_unit(column)
    column = columns[min(fallback_index, len(columns) - 1)]
    return column, detect_wavelength_unit(column)


def _resolve_flux_column(columns: Sequence[str]) -> Tuple[str, Optional[str]]:
    if not columns:
        return "flux", None
    for column in columns:
        lower = column.lower()
        if any(key in lower for key in ("flux", "intensity", "fnu", "flam", "counts", "adu", "transmission")):
            return column, detect_flux_unit(column)
    column = columns[1 if len(columns) > 1 else 0]
    return column, detect_flux_unit(column)


def _resolve_uncertainty_column(columns: Sequence[str]) -> Optional[Tuple[str, Optional[str]]]:
    for column in columns:
        lower = column.lower()
        if any(key in lower for key in ("err", "sigma", "unc", "std")):
            return column, detect_flux_unit(column)
    return None


def ingest_ascii_bytes(name: str, data: bytes) -> Tuple[List[SpectrumSegment], Dict[str, object]]:
    lines, text = _decode_text_bytes(data)
    start = _find_numeric_start(lines)
    header_lines = lines[:start]
    metadata = _parse_header_metadata(header_lines)
    stream = io.StringIO("\n".join(lines[start:]))

    try:
        df = pd.read_csv(stream, comment="#", sep=None, engine="python")
    except Exception:
        stream.seek(0)
        df = pd.read_csv(stream, comment="#", sep=",", engine="python")

    df = df.dropna(axis=0, how="all")
    if df.empty or df.shape[1] < 2:
        raise ValueError("ASCII/CSV file must contain at least two columns (wavelength, flux).")

    if any(not isinstance(col, str) for col in df.columns):
        df.columns = [str(col) for col in df.columns]

    wavelength_column, wave_unit_hint = _resolve_column(df.columns.tolist(), 0)
    flux_column, flux_unit_hint = _resolve_flux_column(df.columns.tolist())
    unc_column = _resolve_uncertainty_column(df.columns.tolist())

    log = ConversionLog()
    wave_unit = metadata.get("wavelength_unit") or wave_unit_hint or "nm"
    wavelength_m = wavelength_to_m(df[wavelength_column].to_numpy(), wave_unit, log)
    wavelength_m = _maybe_air_to_vacuum_metadata(wavelength_m, metadata, log)

    flux_unit = metadata.get("flux_unit") or flux_unit_hint
    flux_si, flux_si_unit, flux_kind = flux_to_f_lambda(
        df[flux_column].to_numpy(),
        wavelength_m,
        flux_unit,
        log,
    )

    uncertainty = None
    uncertainty_unit = None
    if unc_column is not None:
        column, uncert_unit = unc_column
        uncertainty_unit = uncert_unit or flux_unit
        uncertainty = convert_uncertainty(df[column].to_numpy(), wavelength_m, uncertainty_unit, flux_kind, log)

    medium_value = metadata.get("wavelength_medium") or metadata.get("medium")

    metadata_out = {
        **metadata,
        "filename": name,
        "points": int(len(df)),
        "wavelength_unit_input": wave_unit,
        "flux_unit_input": flux_unit,
        "flux_unit_si": flux_si_unit,
        "wavelength_range_nm": [float(np.nanmin(wavelength_m) * 1e9), float(np.nanmax(wavelength_m) * 1e9)],
        "flux_kind": flux_kind,
    }
    if medium_value:
        metadata_out.setdefault("wavelength_medium_input", medium_value)
    metadata_out["wavelength_medium_internal"] = "vacuum"
    if uncertainty_unit:
        metadata_out["uncertainty_unit_input"] = uncertainty_unit

    resolution = _estimate_resolution(wavelength_m)
    if resolution is not None:
        metadata_out["resolution_native"] = resolution

    axis = infer_axis_assignment(flux_si, flux_kind)

    segment = SpectrumSegment(
        label=name,
        wavelength_m=wavelength_m,
        flux=flux_si,
        flux_unit=flux_si_unit,
        flux_kind=flux_kind,
        uncertainty=uncertainty,
        metadata={**metadata_out, "axis": axis},
        provenance=log.to_records(),
    )
    return [segment], metadata_out


def _extract_fits_metadata(header) -> Dict[str, object]:
    fields = {}
    for key in ("TELESCOP", "INSTRUME", "OBSERVER", "OBJECT", "DATE-OBS", "BUNIT", "SPECSYS", "CTYPE1", "CUNIT1"):
        if key in header:
            fields[key.lower()] = header[key]
    return fields


def _ensure_1d(array: np.ndarray) -> np.ndarray:
    if array.ndim == 1:
        return array
    if array.ndim == 0:
        return array.reshape(1)
    squeezed = np.squeeze(array)
    if squeezed.ndim != 1:
        raise ValueError("FITS data must be one-dimensional for spectral ingestion.")
    return squeezed


def _compute_wavelength_axis(header, size: int) -> Tuple[np.ndarray, str]:
    crval1 = header.get("CRVAL1")
    cdelt1 = header.get("CDELT1") or header.get("CD1_1")
    crpix1 = header.get("CRPIX1", 1.0)
    if crval1 is None or cdelt1 is None:
        raise ValueError("FITS header missing CRVAL1/CDELT1 for spectral axis.")
    try:
        crval1 = float(crval1)
        cdelt1 = float(cdelt1)
        crpix1 = float(crpix1)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid WCS keywords in FITS header.") from exc

    pix = np.arange(size, dtype=float)
    wavelength = crval1 + (pix - (crpix1 - 1.0)) * cdelt1
    unit = header.get("CUNIT1") or header.get("XUNIT") or "nm"
    return wavelength, unit


def _maybe_air_to_vacuum(wavelength_m: np.ndarray, header, log: ConversionLog) -> np.ndarray:
    medium = str(header.get("SPECSYS", "")).lower()
    ctype = str(header.get("CTYPE1", "")).lower()
    air_flag = "air" in medium or "wave-air" in ctype
    if not air_flag:
        return wavelength_m
    return _convert_air_to_vacuum(wavelength_m, log)


def ingest_fits_bytes(name: str, data: bytes) -> Tuple[List[SpectrumSegment], Dict[str, object]]:
    segments: List[SpectrumSegment] = []
    metadata_out: Dict[str, object] = {"filename": name}

    with fits.open(io.BytesIO(data)) as hdul:
        for index, hdu in enumerate(hdul):
            if not hasattr(hdu, "data") or hdu.data is None:
                continue
            try:
                flux = np.asarray(_ensure_1d(np.ma.getdata(hdu.data)), dtype=float)
            except ValueError:
                continue
            if flux.size == 0:
                continue
            header = hdu.header
            metadata_out.update(_extract_fits_metadata(header))

            log = ConversionLog()
            wavelength_axis, wavelength_unit = _compute_wavelength_axis(header, flux.size)
            wavelength_m = wavelength_to_m(wavelength_axis, wavelength_unit, log)
            wavelength_m = _maybe_air_to_vacuum(wavelength_m, header, log)

            flux_unit = header.get("BUNIT")
            flux_si, flux_si_unit, flux_kind = flux_to_f_lambda(flux, wavelength_m, flux_unit, log)

            uncertainty = None
            if "ERRS" in hdul:
                err_hdu = hdul["ERRS"]
                try:
                    uncertainty = np.asarray(_ensure_1d(np.ma.getdata(err_hdu.data)), dtype=float)
                except ValueError:
                    uncertainty = None
            uncertainty = convert_uncertainty(uncertainty, wavelength_m, flux_unit, flux_kind, log)

            meta_segment = {
                "filename": name,
                "hdu_index": index,
                "wavelength_unit_input": wavelength_unit,
                "flux_unit_input": flux_unit,
                "flux_unit_si": flux_si_unit,
                "points": int(flux.size),
                "axis": infer_axis_assignment(flux_si, flux_kind),
                "flux_kind": flux_kind,
                "wavelength_medium_internal": "vacuum",
                "wavelength_range_nm": [
                    float(np.nanmin(wavelength_m) * 1e9),
                    float(np.nanmax(wavelength_m) * 1e9),
                ],
            }
            resolution = _estimate_resolution(wavelength_m)
            if resolution is not None:
                meta_segment["resolution_native"] = resolution
            meta_segment.update(_extract_fits_metadata(header))

            segment = SpectrumSegment(
                label=f"{name} [HDU {index}]",
                wavelength_m=wavelength_m,
                flux=flux_si,
                flux_unit=flux_si_unit,
                flux_kind=flux_kind,
                uncertainty=uncertainty,
                metadata=meta_segment,
                provenance=log.to_records(),
            )
            segments.append(segment)

    if not segments:
        raise ValueError("No spectral segments found in FITS file.")

    return segments, metadata_out


def convert_for_display(segment: SpectrumSegment, display_unit: str) -> Tuple[np.ndarray, str]:
    return convert_wavelength_for_display(segment.wavelength_m, display_unit)


__all__ = [
    "SpectrumSegment",
    "checksum_bytes",
    "ingest_ascii_bytes",
    "ingest_fits_bytes",
    "convert_for_display",
]
