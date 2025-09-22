from __future__ import annotations

"""Fetch VLT/X-Shooter spectra from curated open-data Zenodo records."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import unicodedata
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from astropy import units as u
from astropy.io import fits
import requests

from app._version import get_version_info
from app.utils.flux import flux_percentile_range

__all__ = ["fetch", "EsoFetchError", "available_spectra"]


REQUEST_TIMEOUT = 30  # seconds
ARCHIVE_LABEL = "ESO"
CANONICAL_WAVELENGTH_UNIT = "nm"
CANONICAL_FLUX_UNIT = "erg s^-1 cm^-2 nm^-1"


class EsoFetchError(RuntimeError):
    """Raised when an ESO spectrum cannot be retrieved."""


def _normalise_token(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_only.lower())


@dataclass(frozen=True)
class EsoSpectrum:
    identifier: str
    target_name: str
    label: str
    record_id: str
    filename: str
    mode: str
    instrument: str
    program: str
    doi: str
    citation: str
    description: str
    spectral_type: str
    distance_pc: float
    aliases: Tuple[str, ...]
    search_tokens: Tuple[str, ...]

    @property
    def cache_key(self) -> str:
        return _normalise_token(self.identifier)

    @property
    def access_url(self) -> str:
        return (
            f"https://zenodo.org/api/records/{self.record_id}/files/"
            f"{self.filename}/content"
        )


def _create_spectrum(**kwargs: Any) -> EsoSpectrum:
    aliases = set(kwargs.get("aliases", ()))
    tokens: set[str] = set()
    tokens.add(_normalise_token(kwargs.get("identifier", "")))
    tokens.add(_normalise_token(kwargs.get("target_name", "")))
    tokens.add(_normalise_token(kwargs.get("label", "")))
    for alias in aliases:
        tokens.add(_normalise_token(alias))
    tokens.discard("")
    kwargs["aliases"] = tuple(sorted(aliases))
    kwargs["search_tokens"] = tuple(sorted(tokens))
    return EsoSpectrum(**kwargs)


_SPECTRA: Tuple[EsoSpectrum, ...] = (
    _create_spectrum(
        identifier="SZ71-UVB",
        target_name="Sz 71",
        label="Sz 71 • X-Shooter UVB",
        record_id="10024073",
        filename="flux_Sz71_uvb.fits",
        mode="UVB",
        instrument="VLT/X-Shooter",
        program="PENELLOPE",
        doi="10.5281/zenodo.10024073",
        citation="Manara, C. F. et al. (2023). PENELLOPE X-Shooter spectra of Lupus targets. Zenodo.",
        description="PENELLOPE UVB arm spectrum of the Lupus young star Sz 71.",
        spectral_type="M1.5e",
        distance_pc=155.2,
        aliases=("Sz71", "2MASS J16093030-3904316"),
    ),
    _create_spectrum(
        identifier="RYLUP-UVB",
        target_name="RY Lup",
        label="RY Lup • X-Shooter UVB",
        record_id="10024073",
        filename="flux_RYLup_uvb.fits",
        mode="UVB",
        instrument="VLT/X-Shooter",
        program="PENELLOPE",
        doi="10.5281/zenodo.10024073",
        citation="Manara, C. F. et al. (2023). PENELLOPE X-Shooter spectra of Lupus targets. Zenodo.",
        description="High S/N UVB spectrum of the transitional disk star RY Lup from PENELLOPE.",
        spectral_type="G8/K1IV-V",
        distance_pc=153.5,
        aliases=("RYLup", "RY Lupus"),
    ),
    _create_spectrum(
        identifier="SZ130-NIR",
        target_name="Sz 130",
        label="Sz 130 • X-Shooter NIR",
        record_id="10024073",
        filename="flux_Sz130_nir_tell.fits",
        mode="NIR",
        instrument="VLT/X-Shooter",
        program="PENELLOPE",
        doi="10.5281/zenodo.10024073",
        citation="Manara, C. F. et al. (2023). PENELLOPE X-Shooter spectra of Lupus targets. Zenodo.",
        description="Telluric-corrected near-infrared arm spectrum of Sz 130 from PENELLOPE.",
        spectral_type="M1.5",
        distance_pc=159.2,
        aliases=("Sz130", "Gaia DR3 6016650308488574208"),
    ),
)

_TOKEN_LOOKUP: Dict[str, EsoSpectrum] = {}
for spec in _SPECTRA:
    _TOKEN_LOOKUP[_normalise_token(spec.identifier)] = spec
    _TOKEN_LOOKUP[_normalise_token(spec.target_name)] = spec
    for alias in spec.search_tokens:
        if alias:
            _TOKEN_LOOKUP.setdefault(alias, spec)


def available_spectra() -> Tuple[Dict[str, object], ...]:
    records: List[Dict[str, object]] = []
    for spec in _SPECTRA:
        records.append(
            {
                "identifier": spec.identifier,
                "target_name": spec.target_name,
                "label": spec.label,
                "record_id": spec.record_id,
                "filename": spec.filename,
                "mode": spec.mode,
                "instrument": spec.instrument,
                "program": spec.program,
                "spectral_type": spec.spectral_type,
                "distance_pc": spec.distance_pc,
                "doi": spec.doi,
                "citation": spec.citation,
                "description": spec.description,
                "aliases": tuple(spec.aliases),
            }
        )
    return tuple(records)


def fetch(
    target: str = "",
    *,
    identifier: str | None = None,
    cache_dir: str | Path | None = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Fetch an ESO X-Shooter spectrum and return normalised payload."""

    spec = _resolve_spectrum(target=target, identifier=identifier)
    cache_directory = _resolve_cache_dir(cache_dir) / spec.cache_key
    cache_directory.mkdir(parents=True, exist_ok=True)

    local_path = cache_directory / spec.filename
    cache_hit = local_path.exists() and not force_refresh

    if not cache_hit:
        _download_file(spec.access_url, local_path)

    spectrum = _parse_xshooter_spectrum(local_path)
    effective_range = flux_percentile_range(
        spectrum["wavelength_nm"], spectrum["flux"], coverage=0.985
    )

    sha256_hash = _sha256(local_path)
    fetch_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    version_info = get_version_info().get("version", "unknown")

    meta: Dict[str, Any] = {
        "archive": ARCHIVE_LABEL,
        "target_name": spec.target_name,
        "identifier": spec.identifier,
        "instrument": spec.instrument,
        "mode": spec.mode,
        "program": spec.program,
        "doi": spec.doi,
        "citation_text": spec.citation,
        "description": spec.description,
        "spectral_type": spec.spectral_type,
        "distance_pc": spec.distance_pc,
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


def _resolve_spectrum(target: str, identifier: str | None) -> EsoSpectrum:
    if identifier:
        token = _normalise_token(identifier)
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
    raise EsoFetchError("No ESO spectra configured")


def _resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir)
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "providers" / "eso"


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)


def _parse_xshooter_spectrum(path: Path) -> Dict[str, np.ndarray]:
    with fits.open(path) as hdul:
        primary = hdul[0]
        data = primary.data
        if data is None:
            raise EsoFetchError(f"ESO spectrum {path} contains no data")

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
        bunit = header.get("BUNIT", "erg/s/cm2/Angstrom")
        try:
            flux_quantity = flux * u.Unit(bunit)
        except ValueError as exc:  # pragma: no cover - defensive
            raise EsoFetchError(f"Unrecognised flux unit '{bunit}' in {path}") from exc
        flux_converted = flux_quantity.to(u.erg / (u.s * u.cm**2 * u.nm)).value

        uncertainty = None
        if len(hdul) > 1 and hdul[1].data is not None:
            err_data = np.asarray(hdul[1].data, dtype=float)
            try:
                err_quantity = err_data * u.Unit(bunit)
            except ValueError as exc:  # pragma: no cover - defensive
                raise EsoFetchError(
                    f"Unrecognised uncertainty unit '{bunit}' in {path}"
                ) from exc
            uncertainty = err_quantity.to(u.erg / (u.s * u.cm**2 * u.nm)).value

        return {
            "wavelength_nm": wavelength_quantity.to(u.nm).value.astype(float),
            "flux": flux_converted.astype(float),
            "uncertainty": None if uncertainty is None else uncertainty.astype(float),
            "units_original": {
                "wavelength": cunit,
                "flux": bunit,
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
