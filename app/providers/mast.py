from __future__ import annotations

"""MAST provider adapter that serves live CALSPEC spectra via the fetcher."""

from dataclasses import dataclass
import re
import unicodedata
from typing import Dict, Iterable, List, Tuple

from app.server.fetchers import mast as mast_fetcher

from .base import ProviderHit, ProviderQuery


@dataclass(frozen=True)
class _TargetInfo:
    canonical_name: str
    instrument_label: str
    spectral_type: str
    distance_pc: float
    description: str
    search_tokens: Tuple[str, ...]


_TARGETS: Tuple[_TargetInfo, ...] = ()


def refresh_targets() -> None:
    """Reload cached CALSPEC target metadata from the fetcher."""

    global _TARGETS
    _TARGETS = _load_targets()


def _load_targets() -> Tuple[_TargetInfo, ...]:
    records: List[_TargetInfo] = []
    for entry in mast_fetcher.available_targets():
        tokens = {_normalise_token(entry.get("canonical_name", ""))}
        for alias in entry.get("aliases", ()):  # type: ignore[assignment]
            tokens.add(_normalise_token(alias))
        tokens.discard("")
        records.append(
            _TargetInfo(
                canonical_name=entry.get("canonical_name", ""),
                instrument_label=entry.get("instrument_label", ""),
                spectral_type=entry.get("spectral_type", ""),
                distance_pc=float(entry.get("distance_pc") or 0.0),
                description=entry.get("description", ""),
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

    search_terms: List[str] = []
    for value in (query.target, query.text):
        if value:
            search_terms.append(value)

    if not search_terms:
        return list(_TARGETS)

    matches: List[_TargetInfo] = []
    seen: set[str] = set()
    for term in search_terms:
        token = _normalise_token(term)
        if not token:
            continue
        for target in _TARGETS:
            for alias in target.search_tokens:
                if not alias:
                    continue
                if alias == token or alias.startswith(token) or token.startswith(alias):
                    if target.canonical_name not in seen:
                        matches.append(target)
                        seen.add(target.canonical_name)
                    break
    return matches


def _safe_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None



def _coerce_range(value: object) -> Tuple[float, float] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        low = _safe_float(value[0])
        high = _safe_float(value[1])
        if low is not None and high is not None:
            return float(low), float(high)
    return None


def _build_summary(meta: Dict[str, object], target: _TargetInfo) -> str:
    parts: List[str] = ["CALSPEC flux standard"]

    spectral = meta.get("spectral_type") or target.spectral_type
    if spectral:
        parts.append(str(spectral))

    distance = meta.get("distance_pc") or target.distance_pc
    if isinstance(distance, (int, float)) and distance > 0:
        parts.append(f"{float(distance):.2f} pc")


    w_min = _safe_float(meta.get("wavelength_min_nm"))
    w_max = _safe_float(meta.get("wavelength_max_nm"))
    if w_min is not None and w_max is not None:
        parts.append(f"{w_min:.0f}–{w_max:.0f} nm")

    effective_range = _coerce_range(meta.get("wavelength_effective_range_nm"))
    if effective_range is not None:
        parts.append(f"{effective_range[0]:.0f}–{effective_range[1]:.0f} nm")
    else:
        w_min = _safe_float(meta.get("wavelength_min_nm"))
        w_max = _safe_float(meta.get("wavelength_max_nm"))
        if w_min is not None and w_max is not None:
            parts.append(f"{w_min:.0f}–{w_max:.0f} nm")


    return " • ".join(parts)


def _build_metadata(meta: Dict[str, object], target: _TargetInfo, instrument_label: str) -> Dict[str, object]:
    metadata: Dict[str, object] = {
        "target_name": meta.get("target_name") or target.canonical_name,
        "instrument": instrument_label,
    }

    spectral = meta.get("spectral_type") or target.spectral_type
    if spectral:
        metadata["spectral_type"] = spectral

    distance = meta.get("distance_pc") or target.distance_pc
    if isinstance(distance, (int, float)) and distance > 0:
        metadata["distance_pc"] = float(distance)

    description = meta.get("description") or target.description
    if description:
        metadata["description"] = description

    doi = meta.get("doi")
    if doi:
        metadata["doi"] = doi

    w_min = _safe_float(meta.get("wavelength_min_nm"))
    w_max = _safe_float(meta.get("wavelength_max_nm"))
    if w_min is not None and w_max is not None:
        metadata["wavelength_range_nm"] = [w_min, w_max]

    w_range = _coerce_range(meta.get("wavelength_range_nm"))
    if w_range is None:
        w_min = _safe_float(meta.get("wavelength_min_nm"))
        w_max = _safe_float(meta.get("wavelength_max_nm"))
        if w_min is not None and w_max is not None:
            w_range = (w_min, w_max)
    if w_range is not None:
        metadata["wavelength_range_nm"] = [float(w_range[0]), float(w_range[1])]

    effective_range = _coerce_range(meta.get("wavelength_effective_range_nm"))
    if effective_range is not None:
        metadata["wavelength_effective_range_nm"] = [
            float(effective_range[0]),
            float(effective_range[1]),
        ]


    return metadata


def _build_provenance(meta: Dict[str, object], query: ProviderQuery) -> Dict[str, object]:
    provenance: Dict[str, object] = {
        "archive": meta.get("archive"),
        "access_url": meta.get("access_url"),
        "fetched_at_utc": meta.get("fetched_at_utc"),
        "app_version": meta.get("app_version"),
        "file_hash_sha256": meta.get("file_hash_sha256"),
        "cache_path": meta.get("cache_path"),
        "cache_hit": meta.get("cache_hit"),
        "units_original": meta.get("units_original"),
        "units_converted": meta.get("units_converted"),
        "query": query.as_dict(),
        "meta": meta,
    }
    return {key: value for key, value in provenance.items() if value is not None}


def _build_hit(payload: Dict[str, object], query: ProviderQuery, target: _TargetInfo) -> ProviderHit:
    wavelengths = payload.get("wavelength_nm") or []
    flux = payload.get("intensity") or []
    meta = dict(payload.get("meta") or {})

    target_name = meta.get("target_name") or target.canonical_name
    instrument_label = meta.get("instrument") or query.instrument or target.instrument_label or "MAST"

    summary = _build_summary(meta, target)
    metadata = _build_metadata(meta, target, str(instrument_label))
    provenance = _build_provenance(meta, query)

    identifier = str(meta.get("obs_id") or meta.get("target_name") or target.canonical_name)

    return ProviderHit(
        provider="MAST",
        identifier=identifier,
        label=f"{target_name} • {instrument_label}",
        summary=summary,
        wavelengths_nm=[float(value) for value in wavelengths],
        flux=[float(value) for value in flux],
        metadata=metadata,
        provenance=provenance,
    )


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    """Return CALSPEC spectra matching the query, fetching live data as needed."""

    targets = _match_targets(query)
    if not targets:
        search_value = query.target or query.text or ""
        known = ", ".join(target.canonical_name for target in _TARGETS)
        raise mast_fetcher.MastFetchError(
            f"No CALSPEC targets matched '{search_value}'. Known targets: {known}."
        )

    limit = max(1, int(query.limit or 1))
    yielded = 0
    errors: List[str] = []

    for target in targets:
        try:
            payload = mast_fetcher.fetch(
                target=target.canonical_name,
                instrument=query.instrument or "",
            )
        except mast_fetcher.MastFetchError as exc:
            errors.append(str(exc))
            continue

        yield _build_hit(payload, query, target)
        yielded += 1
        if yielded >= limit:
            break

    if yielded == 0 and errors:
        raise mast_fetcher.MastFetchError(errors[0])


# Initialise target cache on import so interactive sessions have data immediately.
refresh_targets()

