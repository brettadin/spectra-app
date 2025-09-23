from __future__ import annotations

"""Fetch spectra linked to specific DOIs hosted on Zenodo."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import warnings
import unicodedata
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy.units import UnitsWarning
import requests

from app._version import get_version_info
from app.utils.flux import flux_percentile_range

__all__ = ["fetch", "DoiFetchError", "available_spectra"]


REQUEST_TIMEOUT = 30  # seconds
CANONICAL_WAVELENGTH_UNIT = "nm"
CANONICAL_FLUX_UNIT = "erg s^-1 cm^-2 nm^-1"
_FALLBACK_FLUX_UNIT_LABEL = "erg s^-1 cm^-2 Angstrom^-1"
_FALLBACK_FLUX_UNIT = u.erg / (u.s * u.cm**2 * u.AA)


class DoiFetchError(RuntimeError):
    """Raised when DOI-linked spectrum retrieval fails."""


def _normalise_token(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_only.lower())


@dataclass(frozen=True)
class DoiSpectrum:
    doi: str
    record_id: str
    filename: str
    label: str
    target_name: str
    instrument: str
    description: str
    citation: str
    archive: str
    aliases: Tuple[str, ...]
    search_tokens: Tuple[str, ...]

    @property
    def identifier(self) -> str:
        return f"DOI:{self.doi}"

    @property
    def cache_key(self) -> str:
        return _normalise_token(self.identifier)

    @property
    def access_url(self) -> str:
        return (
            f"https://zenodo.org/api/records/{self.record_id}/files/"
            f"{self.filename}/content"
        )


def _create_spectrum(**kwargs: Any) -> DoiSpectrum:
    aliases = set(kwargs.get("aliases", ()))
    tokens: set[str] = set()
    tokens.add(_normalise_token(kwargs.get("doi", "")))
    tokens.add(_normalise_token(kwargs.get("label", "")))
    tokens.add(_normalise_token(kwargs.get("target_name", "")))
    for alias in aliases:
        tokens.add(_normalise_token(alias))
    tokens.discard("")
    kwargs["aliases"] = tuple(sorted(aliases))
    kwargs["search_tokens"] = tuple(sorted(tokens))
    return DoiSpectrum(**kwargs)


_SPECTRA: Tuple[DoiSpectrum, ...] = (
    _create_spectrum(
        doi="10.5281/zenodo.6829330",
        record_id="6829330",
        filename="VHS1256b_XShooter_Petrus_22.fits",
        label="VHS 1256-1257 b • X-Shooter",
        target_name="VHS 1256-1257 b",
        instrument="VLT/X-Shooter",
        description="Medium-resolution X-Shooter spectrum of the substellar companion VHS 1256-1257 b (Petrus et al. 2022).",
        citation="Petrus, S. et al. (2022). X-Shooter spectrum of VHS 1256-1257 b. Zenodo.",
        archive="Zenodo",
        aliases=("VHS1256b", "Petrus2022"),
    ),
    _create_spectrum(
        doi="10.5281/zenodo.4268013",
        record_id="4268013",
        filename="GaiaJ1814-7355_SCI_SLIT_FLUX_MERGE1D_VIS.fits",
        label="Gaia J1814-7355 • X-Shooter VIS",
        target_name="Gaia J181417.84-735459.8",
        instrument="VLT/X-Shooter",
        description="VIS-arm merged spectrum of the white dwarf Gaia J181417.84-735459.8 from the X-Shooter reduced data release.",
        citation="González Egea, E. (2020). Reduced spectroscopy objects WDJ181417.84-735459.83 and VHS 472908521370. Zenodo.",
        archive="Zenodo",
        aliases=("GaiaJ1814-7355", "WDJ181417"),
    ),
)

_TOKEN_LOOKUP: Dict[str, DoiSpectrum] = {}
for spec in _SPECTRA:
    _TOKEN_LOOKUP[_normalise_token(spec.doi)] = spec
    _TOKEN_LOOKUP[_normalise_token(spec.identifier)] = spec
    _TOKEN_LOOKUP[_normalise_token(spec.target_name)] = spec
    for token in spec.search_tokens:
        if token:
            _TOKEN_LOOKUP.setdefault(token, spec)


def available_spectra() -> Tuple[Dict[str, object], ...]:
    records: List[Dict[str, object]] = []
    for spec in _SPECTRA:
        records.append(
            {
                "doi": spec.doi,
                "record_id": spec.record_id,
                "filename": spec.filename,
                "label": spec.label,
                "target_name": spec.target_name,
                "instrument": spec.instrument,
                "description": spec.description,
                "citation": spec.citation,
                "archive": spec.archive,
                "aliases": tuple(spec.aliases),
            }
        )
    return tuple(records)


def fetch(
    doi: str = "",
    *,
    target: str = "",
    cache_dir: str | Path | None = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Fetch a DOI-linked spectrum and return normalised payload."""

    spec = _resolve_spectrum(doi=doi, target=target)
    cache_directory = _resolve_cache_dir(cache_dir) / spec.cache_key
    cache_directory.mkdir(parents=True, exist_ok=True)

    local_path = cache_directory / spec.filename
    cache_hit = local_path.exists() and not force_refresh

    if not cache_hit:
        _download_file(spec.access_url, local_path)

    spectrum = _parse_zenodo_spectrum(local_path)
    effective_range = flux_percentile_range(
        spectrum["wavelength_nm"], spectrum["flux"], coverage=0.985
    )

    sha256_hash = _sha256(local_path)
    fetch_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    version_info = get_version_info().get("version", "unknown")

    meta: Dict[str, Any] = {
        "archive": spec.archive,
        "doi": spec.doi,
        "target_name": spec.target_name,
        "instrument": spec.instrument,
        "description": spec.description,
        "citation_text": spec.citation,
        "record_id": spec.record_id,
        "filename": spec.filename,
        "access_url": spec.access_url,
        "cache_path": str(local_path),
        "cache_hit": cache_hit,
        "file_hash_sha256": sha256_hash,
        "fetched_at_utc": fetch_time,
        "app_version": version_info,
        "units_converted": {
            "wavelength": CANONICAL_WAVELENGTH_UNIT,
            "flux": CANONICAL_FLUX_UNIT,
        },
        "units_original": spectrum["units_original"],
        "wavelength_min_nm": float(np.nanmin(spectrum["wavelength_nm"])),
        "wavelength_max_nm": float(np.nanmax(spectrum["wavelength_nm"])),
        "wavelength_sample_count": int(spectrum["wavelength_nm"].size),
    }

    if effective_range is not None:
        meta["wavelength_effective_range_nm"] = [
            float(effective_range[0]),
            float(effective_range[1]),
        ]

    payload: Dict[str, Any] = {
        "wavelength_nm": spectrum["wavelength_nm"].tolist(),
        "intensity": spectrum["flux"].tolist(),
        "meta": meta,
    }

    if spectrum["uncertainty"] is not None:
        payload["uncertainty_stat"] = spectrum["uncertainty"].tolist()

    return payload


def _resolve_spectrum(doi: str, target: str) -> DoiSpectrum:
    if doi:
        token = _normalise_token(doi)
        entry = _TOKEN_LOOKUP.get(token)
        if entry is not None:
            return entry
    if target:
        token = _normalise_token(target)
        entry = _TOKEN_LOOKUP.get(token)
        if entry is not None:
            return entry
        for candidate in _SPECTRA:
            for alias in candidate.search_tokens:
                if alias.startswith(token) or token.startswith(alias):
                    return candidate
    if _SPECTRA:
        return _SPECTRA[0]
    raise DoiFetchError("No DOI spectra configured")


def _resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir)
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "providers" / "doi"


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)


def _resolve_flux_unit(raw_unit: Optional[str], path: Path) -> Tuple[str, u.Unit]:
    label = (raw_unit or "").strip()
    if not label:
        return _FALLBACK_FLUX_UNIT_LABEL, _FALLBACK_FLUX_UNIT
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UnitsWarning)
        try:
            unit = u.Unit(label)
        except ValueError as exc:  # pragma: no cover - defensive
            raise DoiFetchError(f"Unrecognised flux unit '{label}' in {path}") from exc
    return label, unit


def _parse_zenodo_spectrum(path: Path) -> Dict[str, np.ndarray]:
    with fits.open(path) as hdul:
        primary = hdul[0]
        data = primary.data
        if data is None:
            raise DoiFetchError(f"Spectrum {path} contains no data")

        if data.ndim == 3 and data.shape[0] >= 3:
            wavelength = np.asarray(data[0, 0, :], dtype=float) * u.um
            flux = np.asarray(data[1, 0, :], dtype=float)
            err = np.asarray(data[2, 0, :], dtype=float)
            flux_quantity = flux * u.W / (u.m**2 * u.um)
            err_quantity = err * u.W / (u.m**2 * u.um)
            wavelength_nm = wavelength.to(u.nm).value
            flux_converted = flux_quantity.to(u.erg / (u.s * u.cm**2 * u.nm)).value
            err_converted = err_quantity.to(u.erg / (u.s * u.cm**2 * u.nm)).value
            return {
                "wavelength_nm": wavelength_nm.astype(float),
                "flux": flux_converted.astype(float),
                "uncertainty": err_converted.astype(float),
                "units_original": {
                    "wavelength": "µm",
                    "flux": "W m^-2 µm^-1",
                },
            }

        flux = np.asarray(data, dtype=float)
        header = primary.header
        cunit = header.get("CUNIT1", "nm")
        crpix = float(header.get("CRPIX1", 1.0))
        crval = float(header.get("CRVAL1", 0.0))
        cdelt = float(header.get("CDELT1", 1.0))
        pixels = np.arange(flux.size, dtype=float)
        wavelength = crval + (pixels + 1 - crpix) * cdelt
        wave_unit = u.Unit(cunit) if cunit else u.nm
        wavelength_quantity = wavelength * wave_unit
        bunit_label, flux_unit = _resolve_flux_unit(header.get("BUNIT"), path)
        flux_quantity = flux * flux_unit
        flux_converted = flux_quantity.to(u.erg / (u.s * u.cm**2 * u.nm)).value

        uncertainty = None
        if len(hdul) > 1 and hdul[1].data is not None:
            err_data = np.asarray(hdul[1].data, dtype=float)
            try:
                err_quantity = err_data * flux_unit
            except ValueError as exc:  # pragma: no cover - defensive
                raise DoiFetchError(
                    f"Unrecognised uncertainty unit '{bunit_label}' in {path}"
                ) from exc
            uncertainty = err_quantity.to(u.erg / (u.s * u.cm**2 * u.nm)).value

        return {
            "wavelength_nm": wavelength_quantity.to(u.nm).value.astype(float),
            "flux": flux_converted.astype(float),
            "uncertainty": None if uncertainty is None else uncertainty.astype(float),
            "units_original": {
                "wavelength": cunit,
                "flux": bunit_label,
            },
        }
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()
