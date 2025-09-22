from __future__ import annotations

"""Fetch Sloan Digital Sky Survey spectra for curated stellar targets."""

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

__all__ = ["fetch", "SdssFetchError", "available_targets"]


BASE_URL = "http://data.sdss.org/sas/dr17/sdss/spectro/redux/v5_13_2/spectra/full"
REQUEST_TIMEOUT = 30  # seconds
ORIGINAL_FLUX_UNIT = "1e-17 erg s^-1 cm^-2 Å^-1"
ORIGINAL_WAVELENGTH_UNIT = "Å"
CANONICAL_FLUX_UNIT = "erg s^-1 cm^-2 nm^-1"
CANONICAL_WAVELENGTH_UNIT = "nm"
ARCHIVE_LABEL = "SDSS DR17"
CITATION = (
    "Abdurro'uf, U., Accetta, K., Ahumada, R., et al. (2022). "
    "The 17th Data Release of the Sloan Digital Sky Surveys. ApJS 259, 35."
)
DOI = "10.3847/1538-4365/ac4414"


class SdssFetchError(RuntimeError):
    """Raised when a SDSS spectrum cannot be retrieved."""


def _normalise_token(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    return re.sub(r"[^a-z0-9]+", "", lowered)


@dataclass(frozen=True)
class SdssTarget:
    canonical_name: str
    plate: int
    mjd: int
    fiber: int
    subclass: str
    sn_median_r: float
    ra_deg: float
    dec_deg: float
    label: str
    instrument: str = "SDSS/BOSS"
    data_release: str = ARCHIVE_LABEL
    aliases: Tuple[str, ...] = ()
    search_tokens: Tuple[str, ...] = ()

    @property
    def slug(self) -> str:
        return f"{self.plate}-{self.mjd}-{self.fiber:04d}"

    @property
    def cache_key(self) -> str:
        return self.slug


def _create_target(**kwargs: Any) -> SdssTarget:
    aliases = set(kwargs.get("aliases", ()))
    tokens: set[str] = set()
    tokens.add(_normalise_token(str(kwargs.get("canonical_name", ""))))
    tokens.add(_normalise_token(str(kwargs.get("label", ""))))
    plate = kwargs.get("plate")
    mjd = kwargs.get("mjd")
    fiber = kwargs.get("fiber")
    if plate is not None and mjd is not None and fiber is not None:
        tokens.add(_normalise_token(f"{plate}{mjd}{fiber:04d}"))
        tokens.add(_normalise_token(f"{plate}-{mjd}-{fiber:04d}"))
    for alias in list(aliases):
        tokens.add(_normalise_token(alias))
    tokens.discard("")
    kwargs["aliases"] = tuple(sorted(aliases))
    kwargs["search_tokens"] = tuple(sorted(tokens))
    return SdssTarget(**kwargs)


_TARGETS: Tuple[SdssTarget, ...] = (
    _create_target(
        canonical_name="SDSS J234828.73+164429.3",
        label="SDSS J234828.73+164429.3 (F3/F5V)",
        plate=6138,
        mjd=56598,
        fiber=934,
        subclass="F3/F5V",
        sn_median_r=171.7975,
        ra_deg=357.1197,
        dec_deg=16.74147,
        aliases=("SDSS J234828.73+164429.3", "6138-56598-0934"),
    ),
    _create_target(
        canonical_name="SDSS J234333.32+171248.7",
        label="SDSS J234333.32+171248.7 (F3/F5V)",
        plate=6138,
        mjd=56598,
        fiber=716,
        subclass="F3/F5V",
        sn_median_r=144.1442,
        ra_deg=355.88888,
        dec_deg=17.21354,
        aliases=("SDSS J234333.32+171248.7", "6138-56598-0716"),
    ),
    _create_target(
        canonical_name="Gaia DR3 2050891968120836864",
        label="Gaia DR3 2050891968120836864 (F9)",
        plate=2821,
        mjd=54393,
        fiber=134,
        subclass="F9",
        sn_median_r=135.2801,
        ra_deg=290.08288,
        dec_deg=36.627886,
        aliases=("SDSS J192019.89+363739.4", "2821-54393-0134"),
    ),
    _create_target(
        canonical_name="SDSS Plate 3128 Fiber 0178",
        label="SDSS Plate 3128 Fiber 0178 (G2)",
        plate=3128,
        mjd=54776,
        fiber=178,
        subclass="G2",
        sn_median_r=133.8918,
        ra_deg=340.01167,
        dec_deg=13.415657,
        aliases=("3128-54776-0178", "SDSS J224002.80+132456.3"),
    ),
)

_TOKEN_LOOKUP: Dict[str, SdssTarget] = {}
for entry in _TARGETS:
    _TOKEN_LOOKUP[_normalise_token(entry.slug)] = entry
    for token in entry.search_tokens:
        if token:
            _TOKEN_LOOKUP.setdefault(token, entry)


def available_targets() -> Tuple[Dict[str, object], ...]:
    records: List[Dict[str, object]] = []
    for entry in _TARGETS:
        records.append(
            {
                "canonical_name": entry.canonical_name,
                "label": entry.label,
                "plate": entry.plate,
                "mjd": entry.mjd,
                "fiber": entry.fiber,
                "subclass": entry.subclass,
                "sn_median_r": entry.sn_median_r,
                "ra_deg": entry.ra_deg,
                "dec_deg": entry.dec_deg,
                "instrument": entry.instrument,
                "data_release": entry.data_release,
                "aliases": tuple(entry.aliases),
                "search_tokens": tuple(entry.search_tokens),
            }
        )
    return tuple(records)


def fetch(
    target: str = "",
    *,
    plate: int | None = None,
    mjd: int | None = None,
    fiber: int | None = None,
    cache_dir: str | Path | None = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Fetch a curated SDSS spectrum and return normalised payload."""

    entry = _resolve_target(target, plate=plate, mjd=mjd, fiber=fiber)

    cache_directory = _resolve_cache_dir(cache_dir) / entry.cache_key
    cache_directory.mkdir(parents=True, exist_ok=True)

    filename = f"spec-{entry.plate}-{entry.mjd:05d}-{entry.fiber:04d}.fits"
    local_path = cache_directory / filename
    cache_hit = local_path.exists() and not force_refresh

    if not cache_hit:
        remote_url = _remote_url(entry.plate, entry.mjd, entry.fiber)
        _download_file(remote_url, local_path)
    else:
        remote_url = _remote_url(entry.plate, entry.mjd, entry.fiber)

    spectrum = _parse_sdss_spectrum(local_path)
    effective_range = flux_percentile_range(
        spectrum["wavelength_nm"], spectrum["flux"], coverage=0.98
    )

    sha256_hash = _sha256(local_path)
    fetch_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    version_info = get_version_info().get("version", "unknown")

    meta: Dict[str, Any] = {
        "archive": ARCHIVE_LABEL,
        "data_release": entry.data_release,
        "instrument": entry.instrument,
        "target_name": entry.canonical_name,
        "label": entry.label,
        "plate": entry.plate,
        "mjd": entry.mjd,
        "fiber": entry.fiber,
        "subclass": entry.subclass,
        "sn_median_r": entry.sn_median_r,
        "ra_deg": entry.ra_deg,
        "dec_deg": entry.dec_deg,
        "doi": DOI,
        "citation_text": CITATION,
        "access_url": remote_url,
        "cache_path": str(local_path),
        "cache_hit": cache_hit,
        "file_hash_sha256": sha256_hash,
        "fetched_at_utc": fetch_time,
        "app_version": version_info,
        "units_original": {
            "wavelength": ORIGINAL_WAVELENGTH_UNIT,
            "flux": ORIGINAL_FLUX_UNIT,
        },
        "units_converted": {
            "wavelength": CANONICAL_WAVELENGTH_UNIT,
            "flux": CANONICAL_FLUX_UNIT,
        },
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


def _resolve_target(
    target: str,
    *,
    plate: int | None = None,
    mjd: int | None = None,
    fiber: int | None = None,
) -> SdssTarget:
    if plate is not None and mjd is not None and fiber is not None:
        for entry in _TARGETS:
            if entry.plate == int(plate) and entry.mjd == int(mjd) and entry.fiber == int(fiber):
                return entry
    if target:
        token = _normalise_token(target)
        entry = _TOKEN_LOOKUP.get(token)
        if entry is not None:
            return entry
    if target:
        # Try matching by partial token
        token = _normalise_token(target)
        for entry in _TARGETS:
            for alias in entry.search_tokens:
                if alias.startswith(token) or token.startswith(alias):
                    return entry
    known = ", ".join(entry.slug for entry in _TARGETS)
    raise SdssFetchError(
        "Unknown SDSS target. Provide plate, mjd, fiber or known name. "
        f"Configured targets: {known}."
    )


def _remote_url(plate: int, mjd: int, fiber: int) -> str:
    return f"{BASE_URL}/{plate}/spec-{plate}-{mjd:05d}-{fiber:04d}.fits"


def _resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir)
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "providers" / "sdss"


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        if response.status_code == 404:
            raise SdssFetchError(f"SDSS spectrum not found at {url}")
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)


def _parse_sdss_spectrum(path: Path) -> Dict[str, np.ndarray]:
    with fits.open(path) as hdul:
        if len(hdul) < 2:
            raise SdssFetchError(
                f"SDSS file {path} is missing the primary spectral extension."
            )
        table = hdul[1].data
        if table is None:
            raise SdssFetchError(
                f"SDSS file {path} does not contain a spectral table."
            )
        try:
            loglam = np.asarray(table["loglam"], dtype=float)
            flux = np.asarray(table["flux"], dtype=float)
        except (KeyError, TypeError) as exc:  # pragma: no cover - defensive
            raise SdssFetchError("SDSS spectral table lacks loglam/flux columns") from exc

        wavelength = np.power(10.0, loglam) * u.AA
        flux_raw = flux * (1e-17 * u.erg / (u.s * u.cm**2 * u.AA))
        wavelength_nm = wavelength.to(u.nm).value
        flux_converted = flux_raw.to(u.erg / (u.s * u.cm**2 * u.nm)).value

        uncertainty: Optional[np.ndarray] = None
        if "ivar" in table.names:
            ivar = np.asarray(table["ivar"], dtype=float)
            with np.errstate(divide="ignore", invalid="ignore"):
                sigma = np.sqrt(np.where(ivar > 0.0, 1.0 / ivar, np.nan))
            sigma_quantity = sigma * (1e-17 * u.erg / (u.s * u.cm**2 * u.AA))
            uncertainty = sigma_quantity.to(u.erg / (u.s * u.cm**2 * u.nm)).value

        return {
            "wavelength_nm": wavelength_nm.astype(float),
            "flux": flux_converted.astype(float),
            "uncertainty": None if uncertainty is None else uncertainty.astype(float),
        }
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()
