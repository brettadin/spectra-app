from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import re

import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy.units import Quantity
from astropy.wcs import WCS

from .ingest_ascii import checksum_bytes  # reuse checksum helper
from .units import canonical_unit, to_nm


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


EVENT_FLUX_COLUMNS = {
    "rawx",
    "rawy",
    "xcorr",
    "ycorr",
    "xdopp",
    "xfull",
    "yfull",
    "epsilon",
    "dq",
    "pha",
}


def _is_probably_event_column(name: str) -> bool:
    label = name.strip().lower()
    return label in EVENT_FLUX_COLUMNS or label.startswith("raw")


def _looks_like_event_table(
    flux_column: str,
    column_unit: Optional[str],
    header_unit: Optional[str],
    raw_values: np.ndarray,
) -> bool:
    if _is_probably_event_column(flux_column):
        return True

    for unit in (column_unit, header_unit):
        if not unit:
            continue
        lowered = str(unit).strip().lower()
        if lowered in {"pixel", "pixels", "pix"}:
            return True

    try:
        flattened = np.asarray(raw_values).reshape(-1)
    except Exception:  # pragma: no cover - defensive
        flattened = np.array(raw_values).reshape(-1)

    if flattened.size >= 512 and np.issubdtype(flattened.dtype, np.integer):
        sample = flattened[: min(flattened.size, 4096)]
        if np.unique(sample).size <= 256:
            return True

    return False


def _suggest_event_bins(size: int) -> int:
    if size <= 0:
        return 1
    bins = max(int(np.sqrt(size)), 32)
    return int(min(bins, 4096))


def _bin_event_samples(wavelengths: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, int]]:
    finite = wavelengths[np.isfinite(wavelengths)]
    if finite.size == 0:
        raise ValueError("Event spectrum contains no finite wavelength samples.")

    minimum = float(finite.min())
    maximum = float(finite.max())
    if np.isclose(minimum, maximum):
        return np.array([minimum], dtype=float), np.array([float(finite.size)]), {
            "method": "sqrt",
            "bin_count": 1,
            "nonzero_bins": 1,
            "original_samples": int(finite.size),
        }

    bins = _suggest_event_bins(finite.size)
    counts, edges = np.histogram(finite, bins=bins, range=(minimum, maximum))
    centres = 0.5 * (edges[:-1] + edges[1:])
    nonzero = counts > 0

    provenance = {
        "method": "sqrt",
        "bin_count": int(bins),
        "nonzero_bins": int(np.count_nonzero(nonzero)),
        "original_samples": int(finite.size),
    }

    return centres[nonzero], counts[nonzero].astype(float), provenance


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


def _collapse_image_data(
    masked: np.ma.MaskedArray,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, object]]:
    """Collapse an image-like masked array to a 1-D spectrum."""

    provenance: Dict[str, object] = {"original_shape": list(masked.shape)}

    if masked.ndim <= 1:
        flux_view = np.array(np.ma.getdata(masked), dtype=float)
        flux_array = _ensure_1d(flux_view)
        mask_array = np.ma.getmaskarray(masked)
    else:
        collapse_axes = tuple(range(masked.ndim - 1))
        collapsed = masked
        if collapse_axes:
            collapsed = masked.mean(axis=collapse_axes)
        provenance.update(
            {
                "collapse_operation": "mean",
                "collapsed_axes": list(collapse_axes),
                "post_collapse_shape": list(np.shape(collapsed)),
            }
        )
        flux_view = np.array(np.ma.getdata(collapsed), dtype=float)
        flux_array = _ensure_1d(flux_view)
        mask_array = np.ma.getmaskarray(collapsed)

    if mask_array is np.ma.nomask or np.isscalar(mask_array):
        mask_flat = np.zeros_like(flux_array, dtype=bool)
    else:
        mask_flat = np.array(mask_array, dtype=bool).reshape(flux_array.shape)

    if flux_array.size:
        provenance["points"] = int(flux_array.size)

    return flux_array, mask_flat, provenance


def _mask_to_bool(mask, size: int) -> np.ndarray:
    if mask is np.ma.nomask or mask is False:
        return np.zeros(size, dtype=bool)
    arr = np.array(mask, dtype=bool).reshape(-1)
    if arr.size >= size:
        return arr[:size]
    padded = np.zeros(size, dtype=bool)
    padded[: arr.size] = arr
    return padded


_SPECTRAL_AXIS_PREFIXES = {
    "FREQ",
    "WAVE",
    "AWAV",
    "VWAV",
    "WAVN",
    "VRAD",
    "VELO",
    "VOPT",
    "ZOPT",
    "BETA",
    "ENER",
}


def _ctype_is_spectral(value: Optional[str]) -> bool:
    if not value:
        return False
    token = str(value).strip()
    if not token:
        return False
    prefix = token.split("-")[0].upper()
    if len(prefix) < 4:
        return False
    return any(prefix.startswith(candidate) for candidate in _SPECTRAL_AXIS_PREFIXES)


def _unit_is_wavelength(unit: Optional[str]) -> bool:
    if not unit:
        return False
    try:
        canonical_unit(str(unit))
    except ValueError:
        return False
    return True


def _label_suggests_wavelength(name: str) -> bool:
    label = name.strip().lower()
    if not label:
        return False
    tokens = ("wave", "lam", "freq", "wn", "ener")
    return any(token in label for token in tokens)


def _detect_table_columns(names: Sequence[str]) -> Tuple[str, str]:
    if len(names) < 2:
        raise ValueError("FITS table must contain at least two columns for wavelength and flux")

    wavelength = names[0]
    flux = names[1]

    for name in names:
        if _label_suggests_wavelength(name):
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

    wavelength_values = np.array(np.ma.getdata(wavelength_data), dtype=float)
    flux_values = np.array(np.ma.getdata(flux_data), dtype=float)

    if wavelength_values.ndim > 1:
        wavelength_values = wavelength_values.reshape(-1)
    if flux_values.ndim > 1:
        flux_values = flux_values.reshape(-1)

    wavelength_values = _ensure_1d(wavelength_values)
    flux_values = _ensure_1d(flux_values)

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

    column_unit_hint = _column_unit(hdu, wave_idx)
    header_unit_hint = hdu.header.get("CUNIT1") or hdu.header.get("XUNIT")
    wavelength_unit_hint = column_unit_hint or header_unit_hint

    flux_unit_column = _column_unit(hdu, flux_idx)
    flux_unit_header = (
        hdu.header.get("BUNIT")
        or hdu.header.get("BUNIT1")
        or hdu.header.get("FLUXUNIT")
    )

    derived_flux_unit: Optional[str] = None
    event_meta: Optional[Dict[str, object]] = None
    if _looks_like_event_table(
        flux_col,
        flux_unit_column,
        flux_unit_header,
        np.ma.getdata(flux_data),
    ):
        binned_wavelengths, binned_flux, bin_meta = _bin_event_samples(wavelength_values)
        wavelength_values = binned_wavelengths
        flux_values = binned_flux
        derived_flux_unit = "count"
        event_meta = {
            "binning": bin_meta,
            "flux_source_column": flux_col,
            "original_row_count": int(len(data)),
        }
        if flux_unit_column or flux_unit_header:
            event_meta["original_flux_unit"] = str(
                flux_unit_column or flux_unit_header
            )

    flux_unit_hint = flux_unit_column or flux_unit_header

    axis_type = hdu.header.get("CTYPE1")
    unit_missing = not (wavelength_unit_hint and str(wavelength_unit_hint).strip())
    assumed_unit: Optional[str] = None


    if unit_missing:
        if _ctype_is_spectral(axis_type) or _label_suggests_wavelength(wavelength_col):
            resolved_unit = "nm"
            assumed_unit = "nm"
        else:
            axis_display = _coerce_header_value(axis_type) if axis_type is not None else None
            raise ValueError(
                "FITS table column "
                f"{wavelength_col!r} does not advertise a spectral axis "
                f"(CTYPE1={axis_display!r})."
            )
    else:
        resolved_unit = _normalise_wavelength_unit(wavelength_unit_hint)

    if not _unit_is_wavelength(resolved_unit):
        unit_display = _coerce_header_value(wavelength_unit_hint) if wavelength_unit_hint else None
        axis_display = _coerce_header_value(axis_type) if axis_type is not None else None
        raise ValueError(
            "FITS table column "
            f"{wavelength_col!r} uses unsupported spectral unit "
            f"{unit_display!r} (CTYPE1={axis_display!r})."
        )

    if unit_missing:
        if _ctype_is_spectral(axis_type) or _label_suggests_wavelength(wavelength_col):
            resolved_unit = "nm"
            assumed_unit = "nm"
        else:
            axis_display = _coerce_header_value(axis_type) if axis_type is not None else None
            raise ValueError(
                "FITS table column "
                f"{wavelength_col!r} does not advertise a spectral axis "
                f"(CTYPE1={axis_display!r})."
            )
    else:
        resolved_unit = _normalise_wavelength_unit(wavelength_unit_hint)

    if not _unit_is_wavelength(resolved_unit):
        unit_display = _coerce_header_value(wavelength_unit_hint) if wavelength_unit_hint else None
        axis_display = _coerce_header_value(axis_type) if axis_type is not None else None
        raise ValueError(
            "FITS table column "
            f"{wavelength_col!r} uses unsupported spectral unit "
            f"{unit_display!r} (CTYPE1={axis_display!r})."
        )

    dropped_nonpositive_source = 0
    if _is_wavenumber_unit(resolved_unit):
        positive_mask = wavelength_values > 0
        if not np.all(positive_mask):
            dropped_nonpositive_source = int(
                positive_mask.size - np.count_nonzero(positive_mask)
            )
            wavelength_values = wavelength_values[positive_mask]
            flux_values = flux_values[positive_mask]
        if wavelength_values.size == 0:
            raise ValueError(
                "FITS table ingestion yielded no positive wavenumber samples."
            )

    try:
        wavelength_quantity = to_nm(wavelength_values, resolved_unit)
    except ValueError as exc:
        raise ValueError(
            f"Unable to convert values from unit {resolved_unit!r} to nm."
        ) from exc

    wavelength_nm_values = np.asarray(wavelength_quantity.to_value(u.nm), dtype=float)
    if wavelength_nm_values.size == 0:
        raise ValueError(
            "FITS table ingestion yielded no positive wavelength samples."
        )

    positive_nm_mask = wavelength_nm_values > 0
    positive_count = int(np.count_nonzero(positive_nm_mask))
    dropped_nonpositive_nm = 0
    if positive_count == 0:
        raise ValueError(
            "FITS table ingestion yielded no positive wavelength samples after conversion to nm."
        )
    if positive_count < wavelength_nm_values.size:
        dropped_nonpositive_nm = int(wavelength_nm_values.size - positive_count)
        wavelength_quantity = wavelength_quantity[positive_nm_mask]
        wavelength_nm_values = wavelength_nm_values[positive_nm_mask]
        flux_values = flux_values[positive_nm_mask]

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

    unit_resolution: Dict[str, object] = {
        "column": _coerce_header_value(column_unit_hint) if column_unit_hint else None,
        "header": _coerce_header_value(header_unit_hint) if header_unit_hint else None,
        "resolved": resolved_unit,
    }
    if axis_type is not None:
        unit_resolution["axis_type"] = _coerce_header_value(axis_type)
    if assumed_unit is not None:
        unit_resolution["assumed"] = assumed_unit
        if _ctype_is_spectral(axis_type):
            unit_resolution["assumed_from"] = "ctype1"
        else:
            unit_resolution["assumed_from"] = "column_name"

    provenance["wavelength_unit_resolution"] = unit_resolution

    if dropped_nonpositive_source:
        provenance["dropped_nonpositive_wavenumbers"] = dropped_nonpositive_source
    if dropped_nonpositive_nm:
        provenance["dropped_nonpositive_wavelengths"] = dropped_nonpositive_nm

    if event_meta is not None:
        event_meta["derived_flux_unit"] = derived_flux_unit
        provenance["event_table"] = event_meta
        provenance["derived_flux_unit"] = derived_flux_unit

    return (
        wavelength_quantity,
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
    if not text:
        return default

    candidates = [text]
    if "(" in text and ")" in text:
        candidates.append(re.sub(r"\(.*?\)", "", text).strip())
    candidates.append(text.split()[0])

    for candidate in candidates:
        if not candidate:
            continue
        try:
            return canonical_unit(candidate)
        except ValueError:
            continue

    lowered = text.casefold().replace("μ", "µ")
    condensed = lowered.replace(" ", "")
    if "cm" in condensed and ("-1" in condensed or "⁻1" in condensed or "/" in condensed):
        return "cm^-1"
    if any(token in condensed for token in ("wavenumber", "spatialfrequency", "kayser")):
        return "cm^-1"
    return text


def _is_wavenumber_unit(unit: Optional[str]) -> bool:
    if not unit:
        return False
    try:
        return canonical_unit(str(unit)) == "cm^-1"
    except ValueError:
        return False




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
) -> Tuple[Quantity, Dict[str, object]]:
    """Derive a spectral axis from the FITS header using WCS."""

    def _collect_alternate_keys() -> List[str]:
        keys = [""]
        pattern = re.compile(r"^CTYPE\d+([A-Z])$")
        for card in header.keys():
            match = pattern.match(str(card))
            if match:
                suffix = match.group(1)
                if suffix not in keys:
                    keys.append(suffix)
        return keys

    def _find_spectral_pixel_axis(
        wcs: WCS, alternate_key: Optional[str]
    ) -> int:
        spectral_axis = getattr(wcs.wcs, "spec", None)
        if spectral_axis is None:
            spectral_axis = -1
        if spectral_axis < 0:
            for axis_index, axis_type in enumerate(getattr(wcs.wcs, "ctype", ())):
                if _ctype_is_spectral(axis_type):
                    spectral_axis = axis_index
                    break
        if spectral_axis < 0:
            for axis_index in range(wcs.pixel_n_dim):
                axis_number = axis_index + 1
                unit_candidate: Optional[str] = None
                if alternate_key:
                    unit_candidate = header.get(f"CUNIT{axis_number}{alternate_key}")
                if not unit_candidate:
                    unit_candidate = header.get(f"CUNIT{axis_number}")
                if _unit_is_wavelength(unit_candidate):
                    spectral_axis = axis_index
                    break
        if spectral_axis < 0 and wcs.pixel_n_dim == 1:
            spectral_axis = 0
        if spectral_axis < 0 or spectral_axis >= wcs.pixel_n_dim:
            raise ValueError("WCS does not advertise a spectral pixel axis")
        return int(spectral_axis)

    def _find_world_axis(wcs: WCS, pixel_axis: int) -> int:
        correlation = wcs.axis_correlation_matrix
        correlated: List[int] = []
        if correlation is not None and pixel_axis < correlation.shape[1]:
            correlated = [
                int(index)
                for index in np.nonzero(correlation[:, pixel_axis])[0].tolist()
            ]

        def _is_spectral_physical(value: Optional[str]) -> bool:
            if not value:
                return False
            lowered = str(value).lower()
            return "spectral" in lowered or lowered.startswith("em.")

        physical_types = wcs.world_axis_physical_types or ()
        if correlated:
            for index in correlated:
                if index < len(physical_types) and _is_spectral_physical(
                    physical_types[index]
                ):
                    return index
            return correlated[0]

        for index, value in enumerate(physical_types):
            if _is_spectral_physical(value):
                return int(index)

        return min(pixel_axis, max(wcs.world_n_dim - 1, 0))

    def _sample_quantity(
        wcs: WCS,
        pixel_axis: int,
        world_axis: int,
        alternate_key: Optional[str],
    ) -> Quantity:
        pixel_coords: List[np.ndarray] = []
        for axis_index in range(wcs.pixel_n_dim):
            if axis_index == pixel_axis:
                coords = np.arange(size, dtype=float)
            else:
                if axis_index < len(wcs.wcs.crpix):
                    ref = float(wcs.wcs.crpix[axis_index]) - 1.0
                else:  # pragma: no cover - malformed WCS
                    ref = 0.0
                coords = np.full(size, ref, dtype=float)
            pixel_coords.append(coords)

        world = wcs.all_pix2world(*pixel_coords, 0)
        if wcs.world_n_dim == 1:
            world_axes = [np.asarray(world, dtype=float).reshape(-1)]
        else:
            world_axes = [np.asarray(axis, dtype=float).reshape(-1) for axis in world]

        world_values = world_axes[world_axis]

        unit_text: Optional[str] = None
        world_units = wcs.world_axis_units or ()
        if world_axis < len(world_units):
            unit_text = world_units[world_axis] or None

        axis_number = pixel_axis + 1
        if not unit_text and alternate_key:
            unit_text = header.get(f"CUNIT{axis_number}{alternate_key}") or None
        if not unit_text:
            unit_text = header.get(f"CUNIT{axis_number}") or None

        if unit_text:
            try:
                unit_obj = u.Unit(unit_text)
            except Exception as exc:  # pragma: no cover - invalid unit text
                raise ValueError(f"Unsupported WCS spectral unit: {unit_text!r}") from exc
        else:
            unit_obj = u.dimensionless_unscaled

        return u.Quantity(world_values, unit_obj, copy=False)

    alternate_keys = _collect_alternate_keys()
    last_error: Optional[Exception] = None

    for key in alternate_keys:
        wcs_key = key if key else " "
        try:
            wcs = WCS(header, key=wcs_key)
        except Exception as exc:  # pragma: no cover - astropy validation
            last_error = exc
            continue

        try:
            spectral_axis = _find_spectral_pixel_axis(wcs, key or None)
            world_axis = _find_world_axis(wcs, spectral_axis)
            quantity = _sample_quantity(wcs, spectral_axis, world_axis, key or None)
        except Exception as exc:  # pragma: no cover - defensive conversion
            last_error = exc
            continue

        meta: Dict[str, object] = {
            "pixel_axis": int(spectral_axis),
            "world_axis": int(world_axis),
            "world_physical_type": None,
            "ctype": None,
            "unit": canonical_unit(quantity),
        }

        if key:
            meta["wcs_key"] = key

        physical_types = wcs.world_axis_physical_types or ()
        if world_axis < len(physical_types):
            meta["world_physical_type"] = physical_types[world_axis]

        ctypes = getattr(wcs.wcs, "ctype", ())
        if spectral_axis < len(ctypes):
            meta["ctype"] = _coerce_header_value(ctypes[spectral_axis])

        if spectral_axis < len(wcs.wcs.crpix):
            meta["crpix"] = float(wcs.wcs.crpix[spectral_axis])
        if world_axis < len(wcs.wcs.crval):
            meta["crval"] = float(wcs.wcs.crval[world_axis])
        if spectral_axis < len(wcs.wcs.cdelt):
            meta["cdelt"] = float(wcs.wcs.cdelt[spectral_axis])

        if wcs.wcs.has_cd():
            meta["cd_matrix"] = wcs.wcs.cd.tolist()
        elif wcs.wcs.has_pc():
            meta["pc_matrix"] = wcs.wcs.pc.tolist()

        return quantity, meta

    message = "FITS header does not describe a spectral WCS axis."
    if last_error is not None:
        raise ValueError(message) from last_error
    raise ValueError(message)


def _convert_wcs_axis_to_wavelength(axis: Quantity, header) -> Quantity:
    """Convert a WCS-derived spectral axis to nanometres."""

    try:
        return axis.to(u.nm)
    except u.UnitConversionError:
        pass

    try:
        return axis.to(u.nm, equivalencies=u.spectral())
    except u.UnitConversionError:
        pass

    rest_wavelength_keys = ("RESTWAV", "RESTWAVE", "RESTWVL")
    rest_frequency_keys = ("RESTFRQ", "RESTFREQ")

    for key in rest_wavelength_keys:
        value = header.get(key)
        if value is None:
            continue
        try:
            rest_quantity = u.Quantity(value, u.m, copy=False)
        except Exception:
            rest_quantity = u.Quantity(value, u.m)
        try:
            return axis.to(u.nm, equivalencies=u.doppler_optical(rest_quantity))
        except u.UnitConversionError:
            continue

    for key in rest_frequency_keys:
        value = header.get(key)
        if value is None:
            continue
        try:
            rest_quantity = u.Quantity(value, u.Hz, copy=False)
        except Exception:
            rest_quantity = u.Quantity(value, u.Hz)
        for equivalency in (
            u.doppler_radio(rest_quantity),
            u.doppler_relativistic(rest_quantity),
        ):
            try:
                return axis.to(u.nm, equivalencies=equivalency)
            except u.UnitConversionError:
                continue

    raise ValueError(f"Unsupported WCS spectral unit: {axis.unit!r}")


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
    Quantity,
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
        wavelength_quantity,
        flux_array,
        resolved_unit,
        reported_wavelength_unit,
        flux_unit_hint,
        table_provenance,
    ) = _extract_table_data(hdu)

    unit_resolution = table_provenance.get("wavelength_unit_resolution", {})
    unit_inference = {
        "column": unit_resolution.get("column"),
        "header": unit_resolution.get("header"),
        "resolved": unit_resolution.get("resolved", resolved_unit),
        "axis_type": unit_resolution.get("axis_type"),
    }
    if "assumed" in unit_resolution:
        unit_inference["assumed"] = unit_resolution["assumed"]
        unit_inference["assumed_from"] = unit_resolution.get("assumed_from")

    mask_flag = bool(table_provenance.get("mask_applied", False))

    provenance_details = dict(table_provenance)
    try:
        table_wcs_axis, table_wcs_meta = _compute_wavelengths(
            wavelength_quantity.size,
            hdu.header,
        )
    except ValueError:
        table_wcs_axis = None
    else:
        table_wcs_meta = dict(table_wcs_meta)
        table_wcs_meta.setdefault("unit", canonical_unit(table_wcs_axis))
        try:
            converted = _convert_wcs_axis_to_wavelength(table_wcs_axis, hdu.header)
            converted_values = np.asarray(converted.to_value(u.nm), dtype=float)
            table_wcs_meta["wavelength_range_nm"] = [
                float(np.min(converted_values)),
                float(np.max(converted_values)),
            ]
        except ValueError:
            table_wcs_meta["conversion_failed"] = True
        provenance_details["wcs"] = table_wcs_meta

    return (
        wavelength_quantity,
        flux_array,
        resolved_unit,
        reported_wavelength_unit,
        flux_unit_hint,
        unit_inference,
        mask_flag,
        "table",
        provenance_details,
    )


def _ingest_image_hdu(
    hdu,
) -> Tuple[
    Quantity,
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
    flux_array, mask_flat, collapse_meta = _collapse_image_data(masked)

    if flux_array.size == 0:
        raise ValueError("FITS data array is empty.")

    axis_type = hdu.header.get("CTYPE1")
    unit_hint_raw = hdu.header.get("CUNIT1") or hdu.header.get("XUNIT")
    if not (_ctype_is_spectral(axis_type) or _unit_is_wavelength(unit_hint_raw)):
        axis_display = _coerce_header_value(axis_type) if axis_type is not None else None
        unit_display = _coerce_header_value(unit_hint_raw) if unit_hint_raw is not None else None
        raise ValueError(
            "FITS image HDU does not describe a spectral axis "
            f"(CTYPE1={axis_display!r}, CUNIT1={unit_display!r})."
        )

    wavelength_axis, wcs_meta = _compute_wavelengths(flux_array.size, hdu.header)
    resolved_unit = canonical_unit(wavelength_axis)

    try:
        wavelength_quantity = _convert_wcs_axis_to_wavelength(
            wavelength_axis, hdu.header
        )
        wavelength_nm_values = np.asarray(
            wavelength_quantity.to_value(u.nm), dtype=float
        ).reshape(-1)
    except ValueError as exc:
        raise ValueError(
            "Unable to convert image axis values from WCS unit "
            f"{resolved_unit!r} to nm."
        ) from exc

    base_valid = (~mask_flat) & np.isfinite(flux_array) & np.isfinite(wavelength_nm_values)
    positive_mask = wavelength_nm_values > 0
    positive_count = int(np.count_nonzero(positive_mask))
    dropped_nonpositive = int(wavelength_nm_values.size - positive_count)
    if positive_count == 0:
        raise ValueError("FITS image ingestion yielded no positive-wavelength samples.")

    valid = base_valid & positive_mask
    flux_array = flux_array[valid]
    wavelength_nm_values = wavelength_nm_values[valid]
    wavelength_quantity = wavelength_quantity[valid]
    if flux_array.size == 0:
        raise ValueError("FITS ingestion yielded no positive wavelength samples.")

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

    wcs_details = dict(wcs_meta)
    wcs_details["wavelength_range_nm"] = [
        float(np.min(wavelength_nm_values)),
        float(np.max(wavelength_nm_values)),
    ]
    provenance_details: Dict[str, object] = {"wcs": wcs_details}
    if dropped_nonpositive:
        provenance_details["dropped_nonpositive_wavelengths"] = dropped_nonpositive
    if collapse_meta:
        provenance_details["image_collapse"] = collapse_meta
    reported_wavelength_unit = hdu.header.get("CUNIT1") or hdu.header.get("XUNIT")

    return (
        wavelength_quantity,
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
            wavelength_quantity,
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

        derived_flux_unit = provenance_details.get("derived_flux_unit") if isinstance(provenance_details, dict) else None
        flux_unit_source = derived_flux_unit or flux_unit_hint
        flux_unit, flux_kind = _normalise_flux_unit(flux_unit_source)

        wavelength_nm_values = np.asarray(
            wavelength_quantity.to_value(u.nm), dtype=float
        )
        range_min = float(np.min(wavelength_nm_values))
        range_max = float(np.max(wavelength_nm_values))
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
            step = wavelength_quantity[1] - wavelength_quantity[0]
            metadata["wavelength_step_nm"] = float(step.to_value(u.nm))

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
        if derived_flux_unit:
            provenance_units["flux_derived"] = derived_flux_unit
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

        wavelength_list = wavelength_nm_values.tolist()
        flux_list = flux_array.tolist()
        return {
            "label_hint": label_hint,
            "wavelength_nm": wavelength_list,
            "wavelength": {"values": wavelength_list, "unit": "nm"},
            "wavelength_quantity": wavelength_quantity,
            "flux": flux_list,
            "flux_unit": flux_unit,
            "flux_kind": flux_kind,
            "metadata": metadata,
            "provenance": provenance,
            "axis": axis,
            "kind": "spectrum",
        }
    finally:
        hdul.close()
