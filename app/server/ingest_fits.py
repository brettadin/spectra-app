from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from astropy.io import fits

from .ingest_ascii import checksum_bytes  # reuse checksum helper
from .units import to_nm


HeaderInput = Union[str, Path, bytes]


HEADER_METADATA_KEYS = {
    "OBJECT": "target",
    "TARGET": "target",
    "SOURCE": "source",
    "INSTRUME": "instrument",
    "TELESCOP": "telescope",
    "OBSERVAT": "telescope",
    "DATE-OBS": "observation_date",
    "DATE_OBS": "observation_date",
    "TIME-OBS": "observation_time",
    "MJD-OBS": "mjd",
    "EXPTIME": "exposure",
    "AIRMASS": "airmass",
    "PROPOSID": "program",
    "PROGRAM": "program",
    "OBSERVER": "observer",
    "PI": "principal_investigator",
    "RA_TARG": "target_ra",
    "DEC_TARG": "target_dec",
    "SPECSYS": "spectral_reference",
    "CTYPE1": "wavelength_axis_type",
    "CUNIT1": "reported_wavelength_unit",
    "BUNIT": "reported_flux_unit",
    "BUNIT1": "reported_flux_unit",
    "FLUXUNIT": "reported_flux_unit",
}


def _ensure_1d(array: np.ndarray) -> np.ndarray:
    """Return a 1-D view of the provided array or raise if ambiguous."""

    if array.ndim == 0:
        return array.reshape(1)

    squeezed = np.squeeze(array)
    if squeezed.ndim == 1:
        return squeezed

    raise ValueError(
        f"FITS data is not 1-dimensional; found shape {array.shape}. "
        "Provide a FITS HDU with 1-D data for spectral ingestion."
    )


def _mask_to_bool(mask, size: int) -> np.ndarray:
    if mask is np.ma.nomask or mask is False:
        return np.zeros(size, dtype=bool)
    arr = np.array(mask, dtype=bool).reshape(-1)
    if arr.size >= size:
        return arr[:size]
    padded = np.zeros(size, dtype=bool)
    padded[: arr.size] = arr
    return padded


def _detect_table_columns(names: Sequence[str]) -> Tuple[str, str]:
    if len(names) < 2:
        raise ValueError("FITS table must contain at least two columns for wavelength and flux")

    wavelength = names[0]
    flux = names[1]

    for name in names:
        label = name.lower()
        if any(token in label for token in ("wave", "lam", "freq", "wn")):
            wavelength = name
            break

    for name in names:
        if name == wavelength:
            continue
        label = name.lower()
        if any(token in label for token in ("flux", "int", "count", "power", "brightness")):
            flux = name
            break

    if wavelength == flux:
        for name in names:
            if name != wavelength:
                flux = name
                break

    return wavelength, flux


def _column_unit(hdu, index: int, default: Optional[str] = None) -> Optional[str]:
    try:
        unit = hdu.columns[index].unit
    except (AttributeError, IndexError, KeyError):  # pragma: no cover - defensive
        unit = None
    if unit:
        return str(unit)
    return hdu.header.get(f"TUNIT{index + 1}", default)


def _extract_table_data(
    hdu: Union[fits.BinTableHDU, fits.TableHDU]
) -> Tuple[np.ndarray, np.ndarray, str, Optional[str], Optional[str], Dict[str, object]]:
    data = hdu.data
    if data is None or len(data) == 0:
        raise ValueError("FITS table contains no rows for spectral ingestion.")

    column_names = [str(name) for name in (hdu.columns.names or []) if name]
    wavelength_col, flux_col = _detect_table_columns(column_names)

    wavelength_data = np.ma.array(data[wavelength_col])
    flux_data = np.ma.array(data[flux_col])

    wavelength_values = _ensure_1d(np.array(np.ma.getdata(wavelength_data), dtype=float))
    flux_values = _ensure_1d(np.array(np.ma.getdata(flux_data), dtype=float))

    size = min(wavelength_values.size, flux_values.size)
    wavelength_values = wavelength_values[:size]
    flux_values = flux_values[:size]

    wavelength_mask = _mask_to_bool(np.ma.getmaskarray(wavelength_data), size)
    flux_mask = _mask_to_bool(np.ma.getmaskarray(flux_data), size)

    valid = (~wavelength_mask) & (~flux_mask)
    valid &= np.isfinite(wavelength_values) & np.isfinite(flux_values)

    wavelength_values = wavelength_values[valid]
    flux_values = flux_values[valid]

    if wavelength_values.size == 0:
        raise ValueError("FITS table ingestion yielded no valid spectral samples.")

    column_index_map = {name: idx for idx, name in enumerate(column_names)}
    wave_idx = column_index_map[wavelength_col]
    flux_idx = column_index_map[flux_col]

    wavelength_unit_hint = (
        _column_unit(hdu, wave_idx)
        or hdu.header.get("CUNIT1")
        or hdu.header.get("XUNIT")
    )

    flux_unit_hint = (
        _column_unit(hdu, flux_idx)
        or hdu.header.get("BUNIT")
        or hdu.header.get("BUNIT1")
        or hdu.header.get("FLUXUNIT")
    )

    resolved_unit = _normalise_wavelength_unit(wavelength_unit_hint)
    try:
        wavelength_nm = np.array(to_nm(wavelength_values.tolist(), resolved_unit), dtype=float)
    except ValueError:
        wavelength_nm = np.array(to_nm(wavelength_values.tolist(), "nm"), dtype=float)
        resolved_unit = "nm"

    provenance: Dict[str, object] = {
        "table_columns": column_names,
        "column_mapping": {"wavelength": wavelength_col, "flux": flux_col},
        "column_units": {
            name: _column_unit(hdu, column_index_map[name])
            for name in column_names
        },
        "mask_applied": bool(wavelength_mask.any() or flux_mask.any()),
        "row_count": int(len(data)),
    }

    return (
        wavelength_nm,
        flux_values,
        resolved_unit,
        wavelength_unit_hint,
        flux_unit_hint,
        provenance,
    )
def _coerce_header_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="ignore")
        except Exception:
            return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _normalise_wavelength_unit(unit: Optional[str], default: str = "nm") -> str:
    if not unit:
        return default
    text = str(unit).strip()
    lowered = text.lower().replace("μ", "µ")
    if "angstrom" in lowered or lowered in {"a", "å", "ångström", "ångstrom"}:
        return "Å"
    if lowered in {"nm", "nanometer", "nanometers"}:
        return "nm"
    if lowered in {"um", "µm", "micron", "microns", "micrometer", "micrometers"}:
        return "µm"
    if "cm" in lowered and "-1" in lowered:
        return "cm^-1"
    if lowered in {"cm^-1", "cm-1"}:
        return "cm^-1"
    return text




def _normalise_flux_unit(unit: Optional[str]) -> Tuple[str, str]:
    if not unit:
        return "arb", "relative"
    cleaned = str(unit).strip()
    if not cleaned:
        return "arb", "relative"
    lowered = cleaned.lower()
    relative_tokens = {"arb", "arbitrary", "adu", "counts", "count", "relative", "norm"}
    if any(token in lowered for token in relative_tokens):
        return cleaned, "relative"
    return cleaned, "absolute"


def _compute_wavelengths(
    size: int,
    header,
) -> Tuple[np.ndarray, Dict[str, Optional[float]]]:
    crval1 = header.get("CRVAL1")
    cdelt1 = header.get("CDELT1", header.get("CD1_1"))
    crpix1 = header.get("CRPIX1", 1.0)
    missing = [
        key
        for key, value in (("CRVAL1", crval1), ("CDELT1", cdelt1))
        if value is None
    ]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(
            f"Missing WCS keyword(s) {joined} in FITS header for spectral axis."
        )

    try:
        crval1 = float(crval1)
        cdelt1 = float(cdelt1)
        crpix1 = float(crpix1)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid WCS keyword value in FITS header.") from exc

    pix = np.arange(size, dtype=float)
    wavelengths = crval1 + (pix - (crpix1 - 1.0)) * cdelt1
    meta = {
        "crval1": crval1,
        "cdelt1": cdelt1,
        "crpix1": crpix1,
    }
    return wavelengths, meta


def _open_hdul(
    content: HeaderInput,
    filename_hint: Optional[str] = None,
) -> Tuple[fits.HDUList, Optional[str], Optional[bytes]]:
    filename: Optional[str] = filename_hint
    payload: Optional[bytes] = None

    if isinstance(content, (str, Path)):
        path = Path(content)
        filename = path.name
        payload = path.read_bytes()
        hdul = fits.open(io.BytesIO(payload))
    elif isinstance(content, bytes):
        payload = content
        hdul = fits.open(io.BytesIO(content))
    else:
        raise TypeError("Unsupported FITS input; provide a path or bytes-like object.")

    return hdul, filename, payload


def _ingest_table_hdu(
    hdu: Union[fits.BinTableHDU, fits.TableHDU]
) -> Tuple[
    np.ndarray,
    np.ndarray,
    str,
    Optional[str],
    Optional[str],
    Dict[str, object],
    bool,
    str,
    Dict[str, object],
]:
    (
        wavelength_nm,
        flux_array,
        resolved_unit,
        reported_wavelength_unit,
        flux_unit_hint,
        table_provenance,
    ) = _extract_table_data(hdu)

    unit_inference = {
        "column": _coerce_header_value(reported_wavelength_unit)
        if reported_wavelength_unit
        else None,
        "resolved": resolved_unit,
    }

    mask_flag = bool(table_provenance.get("mask_applied", False))

    return (
        wavelength_nm,
        flux_array,
        resolved_unit,
        reported_wavelength_unit,
        flux_unit_hint,
        unit_inference,
        mask_flag,
        "table",
        table_provenance,
    )


def _ingest_image_hdu(
    hdu,
) -> Tuple[
    np.ndarray,
    np.ndarray,
    str,
    Optional[str],
    Optional[str],
    Dict[str, object],
    bool,
    str,
    Dict[str, object],
]:
    masked = np.ma.array(hdu.data)
    flux_array = _ensure_1d(np.array(np.ma.getdata(masked), dtype=float))
    mask_array = np.ma.getmaskarray(masked)
    if mask_array is np.ma.nomask or np.isscalar(mask_array):
        mask_flat = np.zeros_like(flux_array, dtype=bool)
    else:
        mask_flat = np.array(mask_array, dtype=bool).reshape(flux_array.shape)

    if flux_array.size == 0:
        raise ValueError("FITS data array is empty.")

    wavelengths_raw, wcs_meta = _compute_wavelengths(flux_array.size, hdu.header)
    resolved_unit = _normalise_wavelength_unit(
        hdu.header.get("CUNIT1") or hdu.header.get("XUNIT")
    )

    wavelength_nm = np.array(to_nm(wavelengths_raw.tolist(), resolved_unit), dtype=float)

    valid = (~mask_flat) & np.isfinite(flux_array) & np.isfinite(wavelength_nm)
    flux_array = flux_array[valid]
    wavelength_nm = wavelength_nm[valid]
    if flux_array.size == 0:
        raise ValueError("FITS ingestion yielded no valid samples after masking.")

    flux_unit_hint = (
        hdu.header.get("BUNIT")
        or hdu.header.get("BUNIT1")
        or hdu.header.get("FLUXUNIT")
    )
    unit_inference = {
        "header": _coerce_header_value(
            hdu.header.get("CUNIT1") or hdu.header.get("XUNIT")
        ),
        "resolved": resolved_unit,
    }
    mask_flag = bool(mask_flat.any())

    provenance_details = {"wcs": wcs_meta}
    reported_wavelength_unit = hdu.header.get("CUNIT1") or hdu.header.get("XUNIT")

    return (
        wavelength_nm,
        flux_array,
        resolved_unit,
        reported_wavelength_unit,
        flux_unit_hint,
        unit_inference,
        mask_flag,
        "image",
        provenance_details,
    )


def _gather_metadata(header, keys: Sequence[str]) -> Dict[str, object]:
    metadata: Dict[str, object] = {}
    for key in keys:
        value = header.get(key)
        if value is None:
            continue
        metadata[key] = _coerce_header_value(value)
    return metadata


def parse_fits(content: HeaderInput, *, filename: Optional[str] = None) -> Dict[str, object]:
    """Extract a spectrum from a FITS file into the normalised payload."""

    hdul, inferred_name, payload = _open_hdul(content, filename_hint=filename)
    try:
        selected: Optional[Tuple[int, object, Tuple[object, ...]]] = None
        errors: List[str] = []

        for idx, hdu in enumerate(hdul):
            if getattr(hdu, "data", None) is None:
                continue

            try:
                if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                    details = _ingest_table_hdu(hdu)
                else:
                    details = _ingest_image_hdu(hdu)
            except Exception as exc:  # pragma: no cover - defensive aggregation
                errors.append(f"HDU {idx} ({type(hdu).__name__}): {exc}")
                continue

            selected = (idx, hdu, details)
            break

        if selected is None:
            if errors:
                raise ValueError(
                    "Unable to ingest FITS content from any HDU. "
                    + "; ".join(errors)
                )
            raise ValueError("No array data found in FITS file.")

        data_index, data_hdu, details = selected

        (
            wavelength_nm,
            flux_array,
            resolved_unit,
            reported_wavelength_unit,
            flux_unit_hint,
            unit_inference,
            mask_flag,
            data_mode,
            provenance_details,
        ) = details

        header = data_hdu.header

        flux_unit, flux_kind = _normalise_flux_unit(flux_unit_hint)

        range_min = float(np.min(wavelength_nm))
        range_max = float(np.max(wavelength_nm))
        metadata: Dict[str, object] = {
            "wavelength_range_nm": [range_min, range_max],
            "wavelength_effective_range_nm": [range_min, range_max],
            "data_wavelength_range_nm": [range_min, range_max],
            "points": int(flux_array.size),
            "flux_unit": flux_unit,
            "reported_flux_unit": _coerce_header_value(flux_unit_hint) if flux_unit_hint else None,
            "reported_wavelength_unit": _coerce_header_value(reported_wavelength_unit) if reported_wavelength_unit else None,
        }
        metadata["original_wavelength_unit"] = resolved_unit
        metadata.setdefault("wavelength_coverage_nm", [range_min, range_max])

        if flux_array.size >= 2:
            metadata["wavelength_step_nm"] = float(wavelength_nm[1] - wavelength_nm[0])

        header_snapshot = _gather_metadata(header, HEADER_METADATA_KEYS.keys())
        for key, meta_key in HEADER_METADATA_KEYS.items():
            value = header_snapshot.get(key)
            if value is None:
                continue
            metadata.setdefault(meta_key, value)

        metadata.setdefault("wavelength_axis_type", header.get("CTYPE1"))
        metadata.setdefault("spectral_reference", header.get("SPECSYS"))

        label_candidates: List[str] = []
        for field in ("target", "source"):
            value = metadata.get(field)
            if isinstance(value, str) and value.strip():
                label_candidates.append(value.strip())

        label_hint = next((candidate for candidate in label_candidates if candidate), None)

        provenance_details.setdefault("data_mode", data_mode)
        filtered_unit_inference = {k: v for k, v in unit_inference.items() if v is not None}

        provenance: Dict[str, object] = {
            "format": "fits",
            "hdu_index": data_index,
            "hdu_name": getattr(data_hdu, "name", ""),
            "mask_applied": mask_flag,
            "data_mode": data_mode,
            "samples": int(flux_array.size),
        }
        provenance["hdu_type"] = type(data_hdu).__name__
        if filtered_unit_inference:
            provenance["unit_inference"] = filtered_unit_inference
        provenance.update(provenance_details)

        if payload is not None:
            provenance["checksum"] = checksum_bytes(payload)
        if inferred_name:
            provenance["filename"] = inferred_name

        provenance_units: Dict[str, object] = {"wavelength_converted_to": "nm", "flux_unit": flux_unit}
        if resolved_unit:
            provenance_units["wavelength_input"] = resolved_unit
        if reported_wavelength_unit:
            provenance_units["wavelength_reported"] = _coerce_header_value(reported_wavelength_unit)
        if flux_unit_hint:
            provenance_units["flux_input"] = _coerce_header_value(flux_unit_hint)
        provenance["units"] = provenance_units

        conversions: Dict[str, object] = {}
        if resolved_unit and str(resolved_unit).lower() != "nm":
            conversions["wavelength_unit"] = {"from": resolved_unit, "to": "nm"}
        if flux_unit_hint and str(flux_unit_hint) != flux_unit:
            conversions["flux_unit"] = {
                "from": _coerce_header_value(flux_unit_hint),
                "to": flux_unit,
            }
        if conversions:
            provenance["conversions"] = conversions

        interesting_cards = [
            "OBJECT",
            "INSTRUME",
            "TELESCOP",
            "DATE-OBS",
            "DATE_OBS",
            "EXPTIME",
            "AIRMASS",
            "PROPOSID",
            "OBSERVER",
            "BUNIT",
            "CUNIT1",
            "CTYPE1",
        ]
        provenance["header"] = {
            key: _coerce_header_value(header.get(key))
            for key in interesting_cards
            if header.get(key) is not None
        }

        axis = "emission"

        return {
            "label_hint": label_hint,
            "wavelength_nm": [float(value) for value in wavelength_nm.tolist()],
            "flux": [float(value) for value in flux_array.tolist()],
            "flux_unit": flux_unit,
            "flux_kind": flux_kind,
            "metadata": metadata,
            "provenance": provenance,
            "axis": axis,
            "kind": "spectrum",
        }
    finally:
        hdul.close()
