from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from html import unescape
from typing import Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import urljoin

import requests
import numpy as np
from astropy import units as u

from ..ingest_jcamp import parse_jcamp

__all__ = [
    "DEFAULT_RESOLUTION_CM_1",
    "QuantIRFetchError",
    "available_species",
    "manual_species_catalog",
    "fetch",
]


BASE_URL = "https://webbook.nist.gov"
CATALOG_URL = f"{BASE_URL}/chemistry/quant-ir/"
REQUEST_TIMEOUT = 30
DEFAULT_RESOLUTION_CM_1 = 0.125
DEFAULT_APODIZATION_PRIORITY: Tuple[str, ...] = (
    "Boxcar",
    "Triangular",
    "Happ Genzel",
    "3-Term Blackmann-Harris",
    "Norton Beer Strong",
)
STANDARD_ATMOSPHERE = 101325.0 * u.Pa
_JCAMP_PATTERN = re.compile(r"display_jcamp\('([^']+)'", re.IGNORECASE)
_RELATIVE_UNCERTAINTY_PATTERN = re.compile(r"([-+]?\d*\.?\d+)")
_DELTA_X_PATTERN = re.compile(r"##DELTAX\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", re.IGNORECASE)


class QuantIRFetchError(RuntimeError):
    """Raised when a NIST Quantitative IR request cannot be satisfied."""


@dataclass(frozen=True)
class QuantIRMeasurement:
    apodization: str
    resolution_links: Mapping[float, str]


@dataclass(frozen=True)
class QuantIRSpecies:
    name: str
    relative_uncertainty: str
    measurements: Tuple[QuantIRMeasurement, ...]


def _normalise_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _download_text(url: str, *, session: Optional[requests.Session] = None) -> str:
    try:
        response = (session or requests).get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - defensive branch
        raise QuantIRFetchError(f"Failed to download {url}: {exc}") from exc
    if not response.encoding:
        response.encoding = "utf-8"
    return response.text


def _download_bytes(url: str, *, session: Optional[requests.Session] = None) -> bytes:
    try:
        response = (session or requests).get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - defensive branch
        raise QuantIRFetchError(f"Failed to download {url}: {exc}") from exc
    return response.content


def _parse_quantity(value: object, default_unit: u.UnitBase) -> Optional[u.Quantity]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        quantity = u.Quantity(text)
    except Exception:
        match = re.search(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([\wµμ/^-]*)", text)
        if not match:
            return None
        number = match.group(1)
        unit_label = match.group(2) or ""
        try:
            magnitude = float(number)
        except ValueError:
            return None
        try:
            unit = u.Unit(unit_label) if unit_label else default_unit
        except Exception:
            unit = default_unit
        quantity = magnitude * unit
    if not quantity.unit.is_equivalent(default_unit):
        try:
            quantity = quantity.to(default_unit)
        except Exception:
            return None
    return quantity


def _infer_mixing_ratio(metadata: Mapping[str, object]) -> u.Quantity:
    explicit = metadata.get("mixing_ratio_umol_per_mol")
    if explicit is not None:
        try:
            value = float(explicit)
        except (TypeError, ValueError):
            value = None
        else:
            if math.isfinite(value) and value > 0.0:
                return value * (u.umol / u.mol)

    pressure_quantity = _parse_quantity(metadata.get("pressure"), u.Pa)
    if pressure_quantity is None:
        return 1.0 * (u.umol / u.mol)
    try:
        pressure_pa = pressure_quantity.to(u.Pa)
    except Exception:
        return 1.0 * (u.umol / u.mol)
    fraction = (pressure_pa / STANDARD_ATMOSPHERE).decompose().value
    if not math.isfinite(fraction) or fraction <= 0.0:
        return 1.0 * (u.umol / u.mol)
    return fraction * 1e6 * (u.umol / u.mol)


def _infer_path_length(metadata: Mapping[str, object]) -> u.Quantity:
    for key in ("path_length", "cell_path_length", "optical_path_length"):
        quantity = _parse_quantity(metadata.get(key), u.m)
        if quantity is not None and quantity > 0 * u.m:
            return quantity.to(u.m)
    return 1.0 * u.m


def _annotate_axis_units(
    payload: Dict[str, object],
    metadata: Mapping[str, object],
    provenance: Mapping[str, object],
) -> None:
    wavelengths = payload.get("wavelength_nm")
    wavenumbers: Optional[np.ndarray] = None
    if isinstance(wavelengths, (list, tuple)) and wavelengths:
        try:
            wavelength_array = np.asarray(wavelengths, dtype=float)
        except Exception:
            wavelength_array = None
        if wavelength_array is not None and wavelength_array.size:
            valid = np.isfinite(wavelength_array) & (wavelength_array != 0.0)
            if np.any(valid):
                wavenumbers = np.full_like(wavelength_array, np.nan)
                wavenumbers[valid] = 1e7 / wavelength_array[valid]
                payload["wavenumber_cm_1"] = wavenumbers.tolist()
                finite = wavenumbers[np.isfinite(wavenumbers)]
                if finite.size:
                    low = float(np.min(finite))
                    high = float(np.max(finite))
                    metadata["wavenumber_range_cm_1"] = [min(low, high), max(low, high)]

    metadata.setdefault("axis_kind", "wavelength")
    metadata["axis_unit"] = "cm^-1"
    metadata["wavelength_unit"] = "cm^-1"
    metadata["preferred_wavelength_unit"] = "cm^-1"
    metadata["wavelength_display_unit"] = "cm^-1"

    if isinstance(provenance, Mapping):
        units_meta = provenance.get("units") if isinstance(provenance.get("units"), Mapping) else None
        units_data: Dict[str, object] = dict(units_meta or {})
        units_data.setdefault("wavelength_display", "cm^-1")
        units_data.setdefault("preferred_wavelength", "cm^-1")
        provenance["units"] = units_data

def _parse_catalog(html: str) -> Dict[str, QuantIRSpecies]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - defensive branch
        raise QuantIRFetchError("beautifulsoup4 is required to parse the Quant IR catalog") from exc

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "list"})
    if table is None:
        raise QuantIRFetchError("Could not locate Quant IR species table")

    rows = table.find_all("tr")
    if len(rows) <= 1:
        raise QuantIRFetchError("Quant IR species table contained no data")

    catalog: Dict[str, QuantIRSpecies] = {}
    current_name: Optional[str] = None
    current_uncertainty: str = ""
    current_measurements: list[QuantIRMeasurement] = []

    for row in rows[1:]:
        cells = row.find_all("td")
        if not cells:
            continue
        if cells[0].has_attr("rowspan"):
            if current_name is not None:
                catalog[_normalise_token(current_name)] = QuantIRSpecies(
                    name=current_name,
                    relative_uncertainty=current_uncertainty,
                    measurements=tuple(current_measurements),
                )
                current_measurements = []
            current_name = cells[0].get_text(strip=True)
            current_uncertainty = cells[1].get_text(strip=True)
            data_cells = cells[2:]
        else:
            data_cells = cells
        if len(data_cells) < 2 or current_name is None:
            continue
        apod_cell = data_cells[0]
        resolution_cell = data_cells[1]
        apodization = apod_cell.get_text(strip=True)
        links = resolution_cell.find_all("a")
        resolutions: Dict[float, str] = {}
        for link in links:
            href = link.get("href")
            label = link.get_text(strip=True)
            if not href or not label:
                continue
            try:
                value = float(label)
            except ValueError:
                continue
            resolutions[value] = urljoin(CATALOG_URL, href)
        if not resolutions:
            continue
        current_measurements.append(
            QuantIRMeasurement(apodization=apodization, resolution_links=dict(resolutions))
        )

    if current_name is not None and current_measurements:
        catalog[_normalise_token(current_name)] = QuantIRSpecies(
            name=current_name,
            relative_uncertainty=current_uncertainty,
            measurements=tuple(current_measurements),
        )

    return catalog


@lru_cache(maxsize=1)
def _cached_catalog() -> Dict[str, QuantIRSpecies]:
    html = _download_text(CATALOG_URL)
    return _merge_manual_species(_parse_catalog(html))


def _manual_species_catalog() -> Dict[str, QuantIRSpecies]:
    return manual_species_catalog()


def manual_species_catalog() -> Dict[str, QuantIRSpecies]:
    """Return manually curated Quant IR species records."""

    return dict(_MANUAL_SPECIES_CATALOG)


def _merge_manual_species(
    catalog: Mapping[str, QuantIRSpecies]
) -> Dict[str, QuantIRSpecies]:
    merged = dict(catalog)
    for key, species in _MANUAL_SPECIES_CATALOG.items():
        merged.setdefault(key, species)
    return merged


def _load_catalog(*, session: Optional[requests.Session] = None) -> Dict[str, QuantIRSpecies]:
    if session is not None:
        html = _download_text(CATALOG_URL, session=session)
        return _merge_manual_species(_parse_catalog(html))
    return _cached_catalog()


def available_species(*, session: Optional[requests.Session] = None) -> Tuple[Dict[str, object], ...]:
    catalog = _load_catalog(session=session)
    entries: list[Dict[str, object]] = []
    seen_names: set[str] = set()
    for species in sorted(catalog.values(), key=lambda item: item.name.lower()):
        key = species.name.lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        entries.append(
            {
                "name": species.name,
                "relative_uncertainty": species.relative_uncertainty,
                "measurements": [
                    {
                        "apodization": measurement.apodization,
                        "resolutions_cm_1": sorted(measurement.resolution_links.keys()),
                    }
                    for measurement in species.measurements
                ],
            }
        )
    return tuple(entries)


def _choose_measurement(
    species: QuantIRSpecies,
    resolution_cm_1: float,
    priority: Sequence[str],
) -> Tuple[QuantIRMeasurement, float, str]:
    target = float(resolution_cm_1)
    normalised_priority = [_normalise_token(item) for item in priority]

    for candidate_name in normalised_priority:
        if not candidate_name:
            continue
        for measurement in species.measurements:
            if _normalise_token(measurement.apodization) != candidate_name:
                continue
            for value, href in measurement.resolution_links.items():
                if math.isclose(value, target, rel_tol=1e-9, abs_tol=1e-9):
                    return measurement, value, href

    for measurement in species.measurements:
        for value, href in measurement.resolution_links.items():
            if math.isclose(value, target, rel_tol=1e-9, abs_tol=1e-9):
                return measurement, value, href

    raise QuantIRFetchError(
        f"{species.name} does not provide a {resolution_cm_1} cm⁻¹ measurement in the Quant IR catalog."
    )


def _extract_jcamp_url(page_html: str, page_url: str) -> str:
    match = _JCAMP_PATTERN.search(page_html)
    if not match:
        raise QuantIRFetchError("Could not locate JCAMP link on Quant IR spectrum page")
    relative = unescape(match.group(1))
    return urljoin(page_url, relative)


def _extract_delta_x(jcamp_bytes: bytes) -> Optional[float]:
    try:
        text = jcamp_bytes.decode("latin-1", errors="ignore")
    except Exception:  # pragma: no cover - extremely defensive
        return None
    match = _DELTA_X_PATTERN.search(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:  # pragma: no cover - defensive branch
        return None


def _resample_manual_payload(
    payload: Dict[str, object], *, target_resolution: float
) -> Optional[float]:
    wavelengths_nm = payload.get("wavelength_nm")
    flux = payload.get("flux")
    if (
        not isinstance(wavelengths_nm, list)
        or not isinstance(flux, list)
        or len(wavelengths_nm) != len(flux)
        or len(wavelengths_nm) < 2
    ):
        return None

    wavelength_array = np.asarray(wavelengths_nm, dtype=float)
    flux_array = np.asarray(flux, dtype=float)
    if wavelength_array.ndim != 1 or flux_array.ndim != 1:
        return None

    wavenumbers = 1e7 / wavelength_array
    sort_idx = np.argsort(wavenumbers)
    wavenumbers = wavenumbers[sort_idx]
    flux_sorted = flux_array[sort_idx]

    diffs = np.diff(wavenumbers)
    if diffs.size == 0:
        return None
    median_step = float(np.median(diffs))
    if math.isclose(median_step, target_resolution, rel_tol=0.01, abs_tol=1e-6):
        return median_step

    start = float(wavenumbers[0])
    stop = float(wavenumbers[-1])
    new_wavenumbers = np.arange(
        start,
        stop + target_resolution * 0.5,
        target_resolution,
        dtype=float,
    )
    new_flux = np.interp(new_wavenumbers, wavenumbers, flux_sorted)
    new_wavelengths_nm = 1e7 / new_wavenumbers

    payload["wavelength_nm"] = new_wavelengths_nm.tolist()
    payload["flux"] = new_flux.tolist()

    wavelength_dict = payload.get("wavelength")
    if isinstance(wavelength_dict, dict):
        wavelength_dict["values"] = new_wavelengths_nm.tolist()

    wavelength_quantity = payload.get("wavelength_quantity")
    unit = getattr(wavelength_quantity, "unit", None)
    if unit is not None:
        payload["wavelength_quantity"] = new_wavelengths_nm * unit

    payload["downsample"] = {}
    return median_step


def _percent_transmittance(
    samples: np.ndarray,
    *,
    coefficient_units: bool,
    mixing_ratio: u.Quantity,
    path_length: u.Quantity,
) -> np.ndarray:
    if coefficient_units:
        coefficient = np.asarray(samples, dtype=float)
        coefficient = np.nan_to_num(coefficient, nan=0.0, posinf=0.0, neginf=0.0)
        coefficient_quantity = coefficient * (u.mol / (u.umol * u.m))
        absorbance = coefficient_quantity * mixing_ratio * path_length
        absorbance_values = np.asarray(
            absorbance.to_value(u.dimensionless_unscaled), dtype=float
        )
        safe_absorbance = np.clip(absorbance_values, a_min=0.0, a_max=None)
        transmittance_fraction = np.power(10.0, -safe_absorbance)
    else:
        transmittance_fraction = np.asarray(samples, dtype=float)
        transmittance_fraction = np.nan_to_num(
            transmittance_fraction, nan=0.0, posinf=0.0, neginf=0.0
        )
        transmittance_fraction = np.clip(transmittance_fraction, a_min=0.0, a_max=None)
    return transmittance_fraction * 100.0


def _prepare_flux(payload: Dict[str, object], *, manual_entry: bool) -> None:
    flux = payload.get("flux")
    if not isinstance(flux, (list, tuple)):
        return

    try:
        flux_array = np.asarray(flux, dtype=float)
    except Exception:
        return

    if flux_array.ndim != 1 or flux_array.size == 0:
        return

    metadata_raw = payload.get("metadata")
    provenance_raw = payload.get("provenance")

    metadata = dict(metadata_raw or {})
    provenance = dict(provenance_raw or {})

    reported_unit = metadata.get("reported_flux_unit") if isinstance(metadata_raw, Mapping) else None

    coefficient_units = False
    if not manual_entry and isinstance(reported_unit, str):
        if "(micromol/mol)-1m-1" in reported_unit.replace(" ", ""):
            coefficient_units = True

    mixing_ratio = _infer_mixing_ratio(metadata)
    path_length = _infer_path_length(metadata)

    converted = _percent_transmittance(
        flux_array,
        coefficient_units=coefficient_units,
        mixing_ratio=mixing_ratio,
        path_length=path_length,
    )
    converted = np.clip(converted, a_min=0.0, a_max=100.0)

    payload["flux"] = converted.tolist()
    payload["flux_unit"] = "percent transmittance"
    payload["flux_kind"] = "transmission"
    payload["axis"] = "transmission"

    downsample = payload.get("downsample")
    if isinstance(downsample, Mapping):
        for tier in downsample.values():
            if not isinstance(tier, Mapping):
                continue
            samples = tier.get("flux")
            if not isinstance(samples, (list, tuple)):
                continue
            try:
                tier_array = np.asarray(samples, dtype=float)
            except Exception:
                continue
            tier_converted = _percent_transmittance(
                tier_array,
                coefficient_units=coefficient_units,
                mixing_ratio=mixing_ratio,
                path_length=path_length,
            )
            tier_converted = np.clip(tier_converted, a_min=0.0, a_max=100.0)
            tier["flux"] = tier_converted.tolist()

    calibration = {
        "mixing_ratio_umol_per_mol": float(
            mixing_ratio.to_value(u.umol / u.mol)
        ),
        "path_length_m": float(path_length.to_value(u.m)),
        "reference": "Beer–Lambert conversion of NIST Quant IR absorption coefficients",
    }

    _annotate_axis_units(payload, metadata, provenance)

    metadata.setdefault("axis", "transmission")
    metadata.setdefault("axis_kind", "wavelength")
    original_unit = metadata.get("flux_unit_original")
    if original_unit is None and reported_unit is not None:
        metadata["flux_unit_original"] = reported_unit
    metadata["reported_flux_unit"] = "percent transmittance"
    metadata["flux_unit"] = "percent transmittance"
    metadata["flux_unit_display"] = "Transmittance (%)"
    metadata["transmittance_basis"] = "percent"
    if coefficient_units:
        metadata["absorption_coefficient_unit"] = str(reported_unit)
        metadata["quant_ir_calibration"] = calibration
        metadata[
            "transmittance_conversion"
        ] = (
            "Converted from Quant IR absorption coefficients using "
            "T=10^(-α·χ·L) with χ derived from sample pressure and L in meters, expressed as percent transmittance."
        )
    else:
        metadata[
            "transmittance_conversion"
        ] = "Scaled manual WebBook transmittance samples to percent."

    provenance.setdefault("axis", "transmission")
    provenance["flux_unit"] = "percent transmittance"
    provenance["flux_unit_display"] = "Transmittance (%)"
    original_unit = metadata.get("flux_unit_original")
    if original_unit is not None:
        provenance["flux_unit_original"] = original_unit
    if coefficient_units:
        provenance["quant_ir_calibration"] = calibration
        provenance[
            "transmittance_conversion"
        ] = (
            "Converted from Quant IR absorption coefficients using "
            "T=10^(-α·χ·L) with χ derived from sample pressure and L in meters, expressed as percent transmittance."
        )
    else:
        provenance[
            "transmittance_conversion"
        ] = "Scaled manual WebBook transmittance samples to percent."

    payload["metadata"] = metadata
    payload["provenance"] = provenance


def _parse_relative_uncertainty(value: str) -> Optional[float]:
    match = _RELATIVE_UNCERTAINTY_PATTERN.search(value)
    if not match:
        return None
    try:
        return float(match.group(1)) / 100.0
    except ValueError:  # pragma: no cover - defensive branch
        return None


def fetch(
    *,
    species: str,
    resolution_cm_1: float = DEFAULT_RESOLUTION_CM_1,
    session: Optional[requests.Session] = None,
    apodization_priority: Sequence[str] = DEFAULT_APODIZATION_PRIORITY,
) -> Dict[str, object]:
    if not species:
        raise QuantIRFetchError("Species must be provided")

    catalog = _load_catalog(session=session)
    key = _normalise_token(species)
    record = catalog.get(key)
    if record is None:
        raise QuantIRFetchError(f"{species} is not available in the NIST Quant IR catalog")

    measurement, actual_resolution, page_href = _choose_measurement(
        record, resolution_cm_1, apodization_priority
    )
    page_url = page_href
    page_html = _download_text(page_url, session=session)
    jcamp_url = _extract_jcamp_url(page_html, page_url)
    jcamp_bytes = _download_bytes(jcamp_url, session=session)
    payload = parse_jcamp(jcamp_bytes, filename=f"{record.name}.jdx")
    delta_x = _extract_delta_x(jcamp_bytes)
    manual_entry = key in _MANUAL_SPECIES_LOOKUP

    resampled_from = None
    if manual_entry:
        resampled_from = _resample_manual_payload(
            payload, target_resolution=actual_resolution
        )

    metadata = dict(payload.get("metadata") or {})
    metadata.setdefault(
        "source",
        "NIST IR (WebBook)" if manual_entry else "NIST Quantitative IR Database",
    )
    metadata["relative_uncertainty"] = record.relative_uncertainty
    metadata["relative_uncertainty_fraction"] = _parse_relative_uncertainty(
        record.relative_uncertainty
    )
    metadata["apodization"] = measurement.apodization
    metadata["resolution_cm_1"] = actual_resolution
    metadata["catalog_page"] = page_url
    metadata["jcamp_url"] = jcamp_url
    metadata["manual_entry"] = manual_entry
    if manual_entry:
        manual_record = _MANUAL_SPECIES_LOOKUP.get(key)
        if manual_record and manual_record.tokens:
            metadata["aliases"] = tuple(sorted({alias for alias in manual_record.tokens}))
    if resampled_from is not None and not math.isclose(
        resampled_from, actual_resolution, rel_tol=0.01, abs_tol=1e-6
    ):
        metadata["resampled_from_resolution_cm_1"] = resampled_from
    if delta_x is not None:
        metadata["source_delta_x_cm_1"] = delta_x
    payload["metadata"] = metadata

    provenance = dict(payload.get("provenance") or {})
    provenance["archive"] = "NIST Quantitative IR"
    provenance["relative_uncertainty"] = record.relative_uncertainty
    provenance["apodization"] = measurement.apodization
    provenance["resolution_cm_1"] = actual_resolution
    provenance["catalog_page"] = page_url
    provenance["jcamp_url"] = jcamp_url
    provenance["manual_entry"] = manual_entry
    if manual_entry:
        manual_record = _MANUAL_SPECIES_LOOKUP.get(key)
        if manual_record and manual_record.tokens:
            provenance["aliases"] = tuple(sorted({alias for alias in manual_record.tokens}))
    if resampled_from is not None and not math.isclose(
        resampled_from, actual_resolution, rel_tol=0.01, abs_tol=1e-6
    ):
        provenance["resampled_from_resolution_cm_1"] = resampled_from
    if delta_x is not None:
        provenance["source_delta_x_cm_1"] = delta_x
    payload["provenance"] = provenance

    provider_label = "NIST IR (manual 0.125 cm⁻¹)" if manual_entry else "NIST Quant IR"
    label = (
        f"{record.name} • {provider_label} ({measurement.apodization}, {actual_resolution:.3f} cm⁻¹)"
    )
    payload["label"] = label
    payload["provider"] = provider_label
    payload["summary"] = (
        f"{record.name} {measurement.apodization} window at {actual_resolution:.3f} cm⁻¹"
        f" ({record.relative_uncertainty})"
    )
    payload.setdefault("kind", "spectrum")

    _prepare_flux(payload, manual_entry=manual_entry)

    return payload
@dataclass(frozen=True)
class ManualSpeciesRecord:
    name: str
    page_url: str
    tokens: Tuple[str, ...]
    relative_uncertainty: str = "—"
    apodization: str = "Manual (best available)"

    def species(self) -> QuantIRSpecies:
        return QuantIRSpecies(
            name=self.name,
            relative_uncertainty=self.relative_uncertainty,
            measurements=(
                QuantIRMeasurement(
                    apodization=self.apodization,
                    resolution_links={DEFAULT_RESOLUTION_CM_1: self.page_url},
                ),
            ),
        )

    def all_tokens(self) -> Tuple[str, ...]:
        return (self.name, *self.tokens)


_MANUAL_SPECIES_RECORDS: Tuple[ManualSpeciesRecord, ...] = (
    ManualSpeciesRecord(
        name="Water",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C7732185&Index=1&Type=IR",
        tokens=("H2O", "7732-18-5"),
    ),
    ManualSpeciesRecord(
        name="Methane",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C74828&Index=1&Type=IR",
        tokens=("CH4", "74-82-8"),
    ),
    ManualSpeciesRecord(
        name="Carbon Dioxide",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C124389&Index=1&Type=IR",
        tokens=("CO2", "124-38-9"),
    ),
    ManualSpeciesRecord(
        name="Benzene",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C71432&Index=7&Type=IR",
        tokens=("C6H6", "71-43-2"),
        relative_uncertainty="2.1 % relative (B=1.1E-04,C=5.2E-10,D=5.2E-15)",
    ),
    ManualSpeciesRecord(
        name="Ethylene",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C74851&Index=5&Type=IR",
        tokens=("CH2CH2", "C2H4", "74-85-1"),
        relative_uncertainty="2.1 % relative (B=1.1E-04,C=8.5E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Acetone",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C67641&Index=9&Type=IR",
        tokens=("CH3COCH3", "C3H6O", "67-64-1"),
        relative_uncertainty="2.3 % relative (B=1.3E-04,C=1.7E-09,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Ethanol",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C64175&Index=8&Type=IR",
        tokens=("C2H5OH", "C2H6O", "64-17-5"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=2.9E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Methanol",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C67561&Index=7&Type=IR",
        tokens=("CH3OH", "C1H4O", "67-56-1"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=6.6E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="2-Propanol",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C67630&Index=8&Type=IR",
        tokens=("Isopropanol", "C3H8O", "67-63-0"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=6.5E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Ethyl Acetate",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C141786&Index=7&Type=IR",
        tokens=("C4H8O2", "141-78-6"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=6.3E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="1-Butanol",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C71363&Index=8&Type=IR",
        tokens=("C4H10O", "71-36-3"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=2.6E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Sulfur Hexafluoride",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C2551624&Index=5&Type=IR",
        tokens=("SF6", "2551-62-4"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=2.6E-08,D=5.6E-11)",
    ),
    ManualSpeciesRecord(
        name="Acetonitrile",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C75058&Index=7&Type=IR",
        tokens=("CH3CN", "C2H3N", "75-05-8"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=3.1E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Acrylonitrile",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C107131&Index=6&Type=IR",
        tokens=("CH2CHCN", "C3H3N", "107-13-1"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=6.4E-09,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Sulfur Dioxide",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C7446095&Index=6&Type=IR",
        tokens=("SO2", "7446-09-5"),
        relative_uncertainty="2.1 % relative (B=1.1E-04,C=7.6E-10,D=2.7E-14)",
    ),
    ManualSpeciesRecord(
        name="Carbon Tetrachloride",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C56235&Index=9&Type=IR",
        tokens=("CCl4", "56-23-5"),
        relative_uncertainty="2.1 % relative (B=1.1E-04,C=2.7E-09,D=1.4E-13)",
    ),
    ManualSpeciesRecord(
        name="Butane",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C106978&Index=6&Type=IR",
        tokens=("C4H10", "106-97-8"),
        relative_uncertainty="2.0 % relative (B=1.0E-04,C=-1.9E-11,D=8.7E-15)",
    ),
    ManualSpeciesRecord(
        name="Ethylbenzene",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C100414&Index=8&Type=IR",
        tokens=("C8H10", "100-41-4"),
        relative_uncertainty="2.1 % relative (B=1.13E-04,C=1.09E-9,D=2.34E-14)",
    ),
)

_MANUAL_SPECIES_LOOKUP: Dict[str, ManualSpeciesRecord] = {}
_MANUAL_SPECIES_CATALOG: Dict[str, QuantIRSpecies] = {}

for manual_record in _MANUAL_SPECIES_RECORDS:
    species = manual_record.species()
    for token in manual_record.all_tokens():
        normalised = _normalise_token(token)
        if not normalised:
            continue
        _MANUAL_SPECIES_LOOKUP[normalised] = manual_record
        _MANUAL_SPECIES_CATALOG[normalised] = species
