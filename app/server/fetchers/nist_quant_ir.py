from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from html import unescape
from typing import Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import urljoin

import requests

from ..ingest_jcamp import parse_jcamp

__all__ = [
    "DEFAULT_RESOLUTION_CM_1",
    "QuantIRFetchError",
    "available_species",
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
    return _parse_catalog(html)


def _load_catalog(*, session: Optional[requests.Session] = None) -> Dict[str, QuantIRSpecies]:
    if session is not None:
        html = _download_text(CATALOG_URL, session=session)
        return _parse_catalog(html)
    return _cached_catalog()


def available_species(*, session: Optional[requests.Session] = None) -> Tuple[Dict[str, object], ...]:
    catalog = _load_catalog(session=session)
    entries: list[Dict[str, object]] = []
    for species in sorted(catalog.values(), key=lambda item: item.name.lower()):
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
    payload = parse_jcamp(_download_bytes(jcamp_url, session=session), filename=f"{record.name}.jdx")

    metadata = dict(payload.get("metadata") or {})
    metadata.setdefault("source", "NIST Quantitative IR Database")
    metadata["relative_uncertainty"] = record.relative_uncertainty
    metadata["relative_uncertainty_fraction"] = _parse_relative_uncertainty(
        record.relative_uncertainty
    )
    metadata["apodization"] = measurement.apodization
    metadata["resolution_cm_1"] = actual_resolution
    metadata["catalog_page"] = page_url
    metadata["jcamp_url"] = jcamp_url
    payload["metadata"] = metadata

    provenance = dict(payload.get("provenance") or {})
    provenance["archive"] = "NIST Quantitative IR"
    provenance["relative_uncertainty"] = record.relative_uncertainty
    provenance["apodization"] = measurement.apodization
    provenance["resolution_cm_1"] = actual_resolution
    provenance["catalog_page"] = page_url
    provenance["jcamp_url"] = jcamp_url
    payload["provenance"] = provenance

    label = f"{record.name} • NIST Quant IR ({measurement.apodization}, {actual_resolution:.3f} cm⁻¹)"
    payload["label"] = label
    payload["provider"] = "NIST Quant IR"
    payload["summary"] = (
        f"{record.name} {measurement.apodization} window at {actual_resolution:.3f} cm⁻¹"
        f" ({record.relative_uncertainty})"
    )
    payload.setdefault("kind", "spectrum")

    return payload
