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
        name="H2O",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=7732-18-5&Type=IR-SPEC&Index=1#IR-SPEC",
        tokens=("Water",),
    ),
    ManualSpeciesRecord(
        name="Methane",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C74828&Type=IR-SPEC&Index=1#IR-SPEC",
        tokens=("CH4",),
    ),
    ManualSpeciesRecord(
        name="CO2",
        page_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C124389&Type=IR-SPEC&Index=1#IR-SPEC",
        tokens=("Carbon dioxide",),
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
