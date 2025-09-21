"""Fetch stellar spectra from the CALSPEC archive hosted on MAST.

This module replaces the placeholder implementation that previously returned
empty arrays with logic that can download, cache, and parse CALSPEC FITS files
for a curated sample of bright nearby stars.  The spectra are normalised to the
app's canonical nanometre wavelength grid and preserve provenance metadata so
downstream overlays and exports can cite the original archive.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import unicodedata

import numpy as np
from astropy import units as u
from astropy.io import fits
import requests

from app._version import get_version_info

__all__ = ["fetch", "MastFetchError"]


CALSPEC_INDEX_URL = "https://ssb.stsci.edu/cdbs/calspec/"
REQUEST_TIMEOUT = 20  # seconds

ARCHIVE_LABEL = "MAST CALSPEC"
ORIGINAL_FLUX_UNIT = "erg s^-1 cm^-2 Å^-1"
CANONICAL_FLUX_UNIT = "erg s^-1 cm^-2 nm^-1"
ORIGINAL_WAVELENGTH_UNIT = "Å"
CANONICAL_WAVELENGTH_UNIT = "nm"


class MastFetchError(RuntimeError):
    """Raised when a CALSPEC product cannot be retrieved."""


def _normalise_token(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    return re.sub(r"[^a-z0-9]+", "", lowered)


@dataclass(frozen=True)
class CalSpecTarget:
    """Description of a curated CALSPEC calibration target."""

    canonical_name: str
    prefix: str
    spectral_type: str
    distance_pc: float
    instrument_label: str
    description: str
    aliases: Tuple[str, ...]
    preferred_modes: Tuple[str, ...] = ("stis", "stisnic", "nicmos", "wfc3")
    fallback_modes: Tuple[str, ...] = ("mod",)
    citation: str = (
        "Bohlin, A. D., M. C. Harris, C. R. Deustua, et al. (2014). "
        "Hubble Space Telescope CALSPEC Flux Standards: Sirius and Vega. AJ 147, 127."
    )
    doi: str = "10.1088/0004-6256/147/6/127"

    @property
    def cache_key(self) -> str:
        return _normalise_token(self.canonical_name)


_CALSPEC_TARGETS: Tuple[CalSpecTarget, ...] = (
    CalSpecTarget(
        canonical_name="Sirius A",
        prefix="sirius",
        spectral_type="A1 V",
        distance_pc=2.64,
        instrument_label="HST/STIS",
        description="Bright primary CALSPEC standard with ultraviolet-through-near-IR coverage.",
        aliases=(
            "sirius",
            "sirius a",
            "alpha cma",
            "alpha canis majoris",
            "hd 48915",
            "hr 2491",
        ),
        preferred_modes=("stis",),
    ),
    CalSpecTarget(
        canonical_name="Vega",
        prefix="alpha_lyr",
        spectral_type="A0 V",
        distance_pc=7.68,
        instrument_label="HST/STIS",
        description="A0 V flux standard exercising overlapping CALSPEC segments.",
        aliases=(
            "vega",
            "alpha lyr",
            "alpha lyrae",
            "hd 172167",
            "hr 7001",
        ),
        preferred_modes=("stis",),
    ),
    CalSpecTarget(
        canonical_name="18 Sco",
        prefix="18sco",
        spectral_type="G2 V",
        distance_pc=14.1,
        instrument_label="HST/STIS",
        description="Solar analogue to validate optical throughput and scaling.",
        aliases=(
            "18 sco",
            "hd 146233",
            "hr 6060",
            "hip 79672",
        ),
        preferred_modes=("stis",),
    ),
)


_ALIAS_LOOKUP: Dict[str, CalSpecTarget] = {}
for target in _CALSPEC_TARGETS:
    _ALIAS_LOOKUP[_normalise_token(target.canonical_name)] = target
    for alias in target.aliases:
        _ALIAS_LOOKUP[_normalise_token(alias)] = target


_CACHED_INDEX: Optional[List[str]] = None


def fetch(
    target: str = "",
    instrument: str = "",
    obs_id: str = "",
    *,
    cache_dir: str | Path | None = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Fetch a CALSPEC spectrum for ``target`` and return the normalised payload."""

    if not target:
        raise MastFetchError("A target name must be provided for CALSPEC fetching.")

    entry = _resolve_target(target)

    cache_directory = _resolve_cache_dir(cache_dir) / entry.cache_key
    cache_directory.mkdir(parents=True, exist_ok=True)

    selected_filename = _choose_remote_filename(entry, preferred_mode=instrument)
    remote_url = f"{CALSPEC_INDEX_URL}{selected_filename}"

    local_path = cache_directory / selected_filename
    cache_hit = local_path.exists() and not force_refresh
    if not cache_hit:
        _download_file(remote_url, local_path)

    spectrum = _parse_calspec_spectrum(local_path)

    sha256_hash = _sha256(local_path)
    fetch_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    version_info = get_version_info().get("version", "unknown")

    meta: Dict[str, Any] = {
        "source_type": "fetch",
        "archive": ARCHIVE_LABEL,
        "target_name": entry.canonical_name,
        "instrument": entry.instrument_label,
        "obs_id": obs_id or selected_filename,
        "program_id": None,
        "doi": entry.doi,
        "access_url": remote_url,
        "citation_text": entry.citation,
        "fetched_at_utc": fetch_time,
        "file_hash_sha256": sha256_hash,
        "units_original": {
            "wavelength": ORIGINAL_WAVELENGTH_UNIT,
            "flux": ORIGINAL_FLUX_UNIT,
        },
        "units_converted": {
            "wavelength": CANONICAL_WAVELENGTH_UNIT,
            "flux": CANONICAL_FLUX_UNIT,
        },
        "app_version": version_info,
        "cache_path": str(local_path),
        "cache_hit": cache_hit,
        "spectral_type": entry.spectral_type,
        "distance_pc": entry.distance_pc,
        "description": entry.description,
        "wavelength_min_nm": float(np.nanmin(spectrum["wavelength_nm"])),
        "wavelength_max_nm": float(np.nanmax(spectrum["wavelength_nm"])),
        "wavelength_sample_count": int(spectrum["wavelength_nm"].size),
    }

    payload: Dict[str, Any] = {
        "wavelength_nm": spectrum["wavelength_nm"].tolist(),
        "intensity": spectrum["flux"].tolist(),
        "meta": meta,
    }

    if spectrum["stat_uncertainty"] is not None:
        payload["uncertainty_stat"] = spectrum["stat_uncertainty"].tolist()
    if spectrum["sys_uncertainty"] is not None:
        payload["uncertainty_sys"] = spectrum["sys_uncertainty"].tolist()

    return payload


def _resolve_target(target: str) -> CalSpecTarget:
    key = _normalise_token(target)
    entry = _ALIAS_LOOKUP.get(key)
    if entry is None:
        known = ", ".join(sorted({t.canonical_name for t in _CALSPEC_TARGETS}))
        raise MastFetchError(
            f"No CALSPEC source configured for '{target}'. Known targets: {known}."
        )
    return entry


def _resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir)
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "providers" / "mast"


def _choose_remote_filename(entry: CalSpecTarget, preferred_mode: str = "") -> str:
    files = _list_remote_files()
    prefix = entry.prefix.lower()

    modes: Sequence[str] = ()
    preferred_normalised = _normalise_token(preferred_mode) if preferred_mode else ""
    if preferred_normalised:
        modes = (preferred_normalised,)
    elif entry.preferred_modes:
        modes = entry.preferred_modes

    filename = _select_filename_from_modes(prefix, files, modes)
    if filename:
        return filename

    filename = _select_filename_from_modes(prefix, files, entry.fallback_modes)
    if filename:
        return filename

    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)\.fits$", re.IGNORECASE)
    matches = _collect_matches(pattern, files)
    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]

    raise MastFetchError(
        f"Unable to locate a CALSPEC FITS product for {entry.canonical_name} (prefix '{entry.prefix}')."
    )


def _select_filename_from_modes(prefix: str, files: Iterable[str], modes: Sequence[str]) -> Optional[str]:
    for mode in modes:
        if not mode:
            continue
        normalised = mode.lower()
        pattern = re.compile(
            rf"^{re.escape(prefix)}_{re.escape(normalised)}_(\d+)\.fits$",
            re.IGNORECASE,
        )
        matches = _collect_matches(pattern, files)
        if matches:
            matches.sort(key=lambda item: item[0], reverse=True)
            return matches[0][1]
    return None


def _collect_matches(pattern: re.Pattern[str], files: Iterable[str]) -> List[Tuple[int, str]]:
    results: List[Tuple[int, str]] = []
    for filename in files:
        match = pattern.match(filename)
        if match:
            try:
                version = int(match.group(1))
            except (TypeError, ValueError):
                continue
            results.append((version, filename))
    return results


def _list_remote_files() -> List[str]:
    global _CACHED_INDEX
    if _CACHED_INDEX is None:
        html = _download_index_html()
        filenames = set(re.findall(r'href="([^"]+\.fits)"', html, flags=re.IGNORECASE))
        _CACHED_INDEX = sorted(filenames)
    return list(_CACHED_INDEX)


def _download_index_html() -> str:
    response = requests.get(CALSPEC_INDEX_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)


def _parse_calspec_spectrum(path: Path) -> Dict[str, np.ndarray]:
    with fits.open(path) as hdul:
        if len(hdul) < 2 or getattr(hdul[1], "data", None) is None:
            raise MastFetchError(f"CALSPEC file {path} does not contain a spectral table.")

        table = hdul[1].data
        names = {name.upper() for name in getattr(table, "names", [])}

        if "WAVELENGTH" not in names or "FLUX" not in names:
            raise MastFetchError(
                f"CALSPEC file {path} is missing required WAVELENGTH/FLUX columns."
            )

        wavelength = np.array(table["WAVELENGTH"], dtype=float)
        flux = np.array(table["FLUX"], dtype=float)

        stat_unc: Optional[np.ndarray]
        sys_unc: Optional[np.ndarray]

        if "STATERROR" in names:
            stat_unc = np.array(table["STATERROR"], dtype=float)
        else:
            stat_unc = None

        if "SYSERROR" in names:
            sys_unc = np.array(table["SYSERROR"], dtype=float)
        else:
            sys_unc = None

        wavelength_nm = (wavelength * u.AA).to(u.nm).value
        flux_unit = 1.0 * u.erg / (u.s * u.cm ** 2 * u.AA)
        flux_converted = (flux * flux_unit).to(u.erg / (u.s * u.cm ** 2 * u.nm)).value

        if stat_unc is not None:
            stat_converted = (stat_unc * flux_unit).to(
                u.erg / (u.s * u.cm ** 2 * u.nm)
            ).value
        else:
            stat_converted = None

        if sys_unc is not None:
            sys_converted = (sys_unc * flux_unit).to(
                u.erg / (u.s * u.cm ** 2 * u.nm)
            ).value
        else:
            sys_converted = None

        return {
            "wavelength_nm": np.asarray(wavelength_nm, dtype=float),
            "flux": np.asarray(flux_converted, dtype=float),
            "stat_uncertainty": None if stat_converted is None else np.asarray(stat_converted, dtype=float),
            "sys_uncertainty": None if sys_converted is None else np.asarray(sys_converted, dtype=float),
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def reset_index_cache() -> None:
    """Testing hook that clears the cached CALSPEC index."""

    global _CACHED_INDEX
    _CACHED_INDEX = None
