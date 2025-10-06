from __future__ import annotations

"""SDSS provider adapter returning curated Sloan spectra via the fetcher."""

from dataclasses import dataclass
import unicodedata
import re
from typing import Dict, Iterable, List, Tuple

from app.server.fetchers import sdss as sdss_fetcher

from .base import ProviderHit, ProviderQuery


@dataclass(frozen=True)
class _TargetInfo:
    canonical_name: str
    label: str
    plate: int
    mjd: int
    fiber: int
    subclass: str
    sn_median_r: float
    instrument: str
    data_release: str
    ra_deg: float
    dec_deg: float
    search_tokens: Tuple[str, ...]


_TARGETS: Tuple[_TargetInfo, ...] = ()


def refresh_targets() -> None:
    global _TARGETS
    _TARGETS = _load_targets()


def _load_targets() -> Tuple[_TargetInfo, ...]:
    records: List[_TargetInfo] = []
    for entry in sdss_fetcher.available_targets():
        tokens = set(entry.get("search_tokens", ()))  # type: ignore[arg-type]
        tokens.add(_normalise_token(entry.get("canonical_name", "")))
        tokens.add(_normalise_token(entry.get("label", "")))
        tokens.discard("")
        records.append(
            _TargetInfo(
                canonical_name=str(entry.get("canonical_name", "")),
                label=str(entry.get("label", "")),
                plate=int(entry.get("plate", 0) or 0),
                mjd=int(entry.get("mjd", 0) or 0),
                fiber=int(entry.get("fiber", 0) or 0),
                subclass=str(entry.get("subclass", "")),
                sn_median_r=float(entry.get("sn_median_r") or 0.0),
                instrument=str(entry.get("instrument", "SDSS")),
                data_release=str(entry.get("data_release", "SDSS")),
                ra_deg=float(entry.get("ra_deg") or 0.0),
                dec_deg=float(entry.get("dec_deg") or 0.0),
                search_tokens=tuple(sorted(tokens)),
            )
        )
    return tuple(records)


def _normalise_token(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_only.lower())


def _match_targets(query: ProviderQuery) -> List[_TargetInfo]:
    if not _TARGETS:
        return []

    catalog_filter = query.catalog.lower() if query.catalog else ""

    search_terms: List[str] = []
    for value in (query.target, query.text):
        if value:
            search_terms.append(value)

    if not search_terms:
        matches = list(_TARGETS)
    else:
        matches = []
        seen: set[str] = set()
        for term in search_terms:
            token = _normalise_token(term)
            if not token:
                continue
            for target in _TARGETS:
                for alias in target.search_tokens:
                    if not alias:
                        continue
                    if alias.startswith(token) or token.startswith(alias):
                        if target.canonical_name not in seen:
                            matches.append(target)
                            seen.add(target.canonical_name)
                        break

    if catalog_filter:
        matches = [
            target
            for target in matches
            if catalog_filter in target.data_release.lower()
        ]
    return matches


def _build_summary(meta: dict, target: _TargetInfo) -> str:
    parts: List[str] = []
    instrument = meta.get("instrument") or target.instrument
    if instrument:
        parts.append(str(instrument))
    parts.append(target.data_release)
    if target.subclass:
        parts.append(target.subclass)
    snr = meta.get("sn_median_r") or target.sn_median_r
    if isinstance(snr, (int, float)) and snr > 0:
        parts.append(f"S/N_r {float(snr):.1f}")
    w_range = meta.get("wavelength_effective_range_nm") or meta.get("wavelength_range_nm")
    if isinstance(w_range, (list, tuple)) and len(w_range) == 2:
        try:
            low = float(w_range[0])
            high = float(w_range[1])
        except (TypeError, ValueError):  # pragma: no cover - defensive
            low = high = None  # type: ignore[assignment]
        else:
            parts.append(f"{low:.0f}–{high:.0f} nm")
    return " • ".join(part for part in parts if part)


def _build_metadata(meta: dict, target: _TargetInfo) -> dict:
    metadata = {
        "target_name": meta.get("target_name") or target.canonical_name,
        "plate": target.plate,
        "mjd": target.mjd,
        "fiber": target.fiber,
        "instrument": meta.get("instrument") or target.instrument,
        "data_release": meta.get("data_release") or target.data_release,
        "subclass": meta.get("subclass") or target.subclass,
        "sn_median_r": meta.get("sn_median_r") or target.sn_median_r,
        "coordinates": {
            "ra_deg": target.ra_deg,
            "dec_deg": target.dec_deg,
        },
    }
    if "wavelength_min_nm" in meta and "wavelength_max_nm" in meta:
        metadata["wavelength_range_nm"] = [
            float(meta.get("wavelength_min_nm")),
            float(meta.get("wavelength_max_nm")),
        ]
    if "wavelength_effective_range_nm" in meta:
        metadata["wavelength_effective_range_nm"] = list(
            meta["wavelength_effective_range_nm"]
        )
    if meta.get("doi"):
        metadata["doi"] = meta["doi"]
    return metadata


def _build_provenance(meta: dict, query: ProviderQuery) -> dict:
    provenance = {
        "archive": meta.get("archive", "SDSS"),
        "access_url": meta.get("access_url"),
        "doi": meta.get("doi"),
        "citation_text": meta.get("citation_text"),
        "query": query.as_dict(),
        "cache_path": meta.get("cache_path"),
        "cache_hit": meta.get("cache_hit"),
        "file_hash_sha256": meta.get("file_hash_sha256"),
        "fetched_at_utc": meta.get("fetched_at_utc"),
        "app_version": meta.get("app_version"),
        "units_original": meta.get("units_original"),
        "units_converted": meta.get("units_converted"),
    }
    return {key: value for key, value in provenance.items() if value is not None}


def _build_hit(payload: dict, query: ProviderQuery, target: _TargetInfo) -> ProviderHit:
    wavelengths = payload.get("wavelength_nm") or []
    flux = payload.get("intensity") or []
    meta = dict(payload.get("meta") or {})

    summary = _build_summary(meta, target)
    metadata = _build_metadata(meta, target)
    provenance = _build_provenance(meta, query)
    identifier = f"{target.plate}-{target.mjd}-{target.fiber:04d}"

    return ProviderHit(
        provider="SDSS",
        identifier=identifier,
        label=f"{target.label}",
        summary=summary,
        wavelengths_nm=[float(value) for value in wavelengths],
        flux=[float(value) for value in flux],
        metadata=metadata,
        provenance=provenance,
    )


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    targets = _match_targets(query)
    if not targets:
        raise sdss_fetcher.SdssFetchError(
            "No SDSS targets matched the query. Try plate/mjd/fiber identifiers."
        )

    limit = max(1, int(query.limit or 1))
    yielded = 0
    aggregate_errors: List[Dict[str, object]] = []

    for target in targets:
        try:
            payload = sdss_fetcher.fetch(
                target=target.canonical_name,
                plate=target.plate,
                mjd=target.mjd,
                fiber=target.fiber,
            )
        except sdss_fetcher.SdssFetchError as exc:
            aggregate_errors.append(
                {
                    "target": target.canonical_name,
                    "plate": target.plate,
                    "mjd": target.mjd,
                    "fiber": target.fiber,
                    "error": str(exc),
                }
            )
            continue
        hit = _build_hit(payload, query, target)
        if query.catalog:
            hit.metadata.setdefault("requested_catalog", query.catalog)
        if query.diagnostics and aggregate_errors:
            hit.provenance.setdefault("diagnostics", list(aggregate_errors))
        yield hit
        yielded += 1
        if yielded >= limit:
            break

    if yielded == 0 and aggregate_errors:
        details = "\n".join(
            f"- {error.get('target')} plate {error.get('plate')}/{error.get('mjd')}/{error.get('fiber')}: {error.get('error')}"
            for error in aggregate_errors
        )
        raise sdss_fetcher.SdssFetchError(
            "SDSS fetch attempts failed for all requested targets.\n" + details
        )


refresh_targets()
