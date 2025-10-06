from __future__ import annotations

"""ESO provider adapter serving real VLT/X-Shooter spectra."""

from dataclasses import dataclass
import unicodedata
import re
from typing import Dict, Iterable, List, Tuple

from app.server.fetchers import eso as eso_fetcher

from .base import ProviderHit, ProviderQuery


@dataclass(frozen=True)
class _SpectrumInfo:
    identifier: str
    target_name: str
    label: str
    mode: str
    instrument: str
    program: str
    description: str
    spectral_type: str
    distance_pc: float
    doi: str
    citation: str
    search_tokens: Tuple[str, ...]


_SPECTRA: Tuple[_SpectrumInfo, ...] = ()


def refresh_spectra() -> None:
    global _SPECTRA
    _SPECTRA = _load_spectra()


def _load_spectra() -> Tuple[_SpectrumInfo, ...]:
    records: List[_SpectrumInfo] = []
    for entry in eso_fetcher.available_spectra():
        tokens = set(entry.get("aliases", ()))  # type: ignore[arg-type]
        tokens.add(_normalise_token(entry.get("identifier", "")))
        tokens.add(_normalise_token(entry.get("target_name", "")))
        tokens.add(_normalise_token(entry.get("label", "")))
        tokens.discard("")
        records.append(
            _SpectrumInfo(
                identifier=str(entry.get("identifier", "")),
                target_name=str(entry.get("target_name", "")),
                label=str(entry.get("label", "")),
                mode=str(entry.get("mode", "")),
                instrument=str(entry.get("instrument", "X-Shooter")),
                program=str(entry.get("program", "ESO")),
                description=str(entry.get("description", "")),
                spectral_type=str(entry.get("spectral_type", "")),
                distance_pc=float(entry.get("distance_pc") or 0.0),
                doi=str(entry.get("doi", "")),
                citation=str(entry.get("citation", "")),
                search_tokens=tuple(sorted(_normalise_token(token) for token in tokens if token)),
            )
        )
    return tuple(records)


def _normalise_token(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_only.lower())


def _match_spectra(query: ProviderQuery) -> List[_SpectrumInfo]:
    if not _SPECTRA:
        return []

    if query.catalog and query.catalog.lower() not in {"eso", "xshooter", "eso_xshooter"}:
        return []

    search_terms: List[str] = []
    for value in (query.target, query.text):
        if value:
            search_terms.append(value)

    if not search_terms:
        matches = list(_SPECTRA)
    else:
        matches = []
        seen: set[str] = set()
        for term in search_terms:
            token = _normalise_token(term)
            if not token:
                continue
            for spec in _SPECTRA:
                for alias in spec.search_tokens:
                    if not alias:
                        continue
                    if alias.startswith(token) or token.startswith(alias):
                        if spec.identifier not in seen:
                            matches.append(spec)
                            seen.add(spec.identifier)
                        break

    if query.programs:
        programs = {program.lower() for program in query.programs}
        matches = [spec for spec in matches if spec.program.lower() in programs]
    return matches


def _build_summary(meta: dict, spec: _SpectrumInfo) -> str:
    parts: List[str] = [spec.instrument]
    if spec.mode:
        parts.append(spec.mode)
    w_range = meta.get("wavelength_effective_range_nm") or meta.get("wavelength_range_nm")
    if isinstance(w_range, (list, tuple)) and len(w_range) == 2:
        try:
            low = float(w_range[0])
            high = float(w_range[1])
        except (TypeError, ValueError):  # pragma: no cover - defensive
            low = high = None  # type: ignore[assignment]
        else:
            parts.append(f"{low:.0f}–{high:.0f} nm")
    if spec.program:
        parts.append(spec.program)
    return " • ".join(part for part in parts if part)


def _build_metadata(meta: dict, spec: _SpectrumInfo) -> dict:
    metadata = {
        "target_name": meta.get("target_name") or spec.target_name,
        "identifier": meta.get("identifier") or spec.identifier,
        "instrument": meta.get("instrument") or spec.instrument,
        "mode": meta.get("mode") or spec.mode,
        "program": meta.get("program") or spec.program,
        "spectral_type": meta.get("spectral_type") or spec.spectral_type,
        "distance_pc": meta.get("distance_pc") or spec.distance_pc,
        "description": meta.get("description") or spec.description,
        "doi": meta.get("doi") or spec.doi,
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
    return metadata


def _build_provenance(meta: dict, query: ProviderQuery) -> dict:
    provenance = {
        "archive": meta.get("archive", "ESO"),
        "access_url": meta.get("access_url"),
        "record_id": meta.get("record_id"),
        "filename": meta.get("filename"),
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


def _build_hit(payload: dict, query: ProviderQuery, spec: _SpectrumInfo) -> ProviderHit:
    wavelengths = payload.get("wavelength_nm") or []
    flux = payload.get("intensity") or []
    meta = dict(payload.get("meta") or {})

    summary = _build_summary(meta, spec)
    metadata = _build_metadata(meta, spec)
    provenance = _build_provenance(meta, query)

    return ProviderHit(
        provider="ESO",
        identifier=spec.identifier,
        label=f"{spec.label}",
        summary=summary,
        wavelengths_nm=[float(value) for value in wavelengths],
        flux=[float(value) for value in flux],
        metadata=metadata,
        provenance=provenance,
    )


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    spectra = _match_spectra(query)
    if not spectra:
        raise eso_fetcher.EsoFetchError("No ESO spectra matched the query.")

    limit = max(1, int(query.limit or 1))
    yielded = 0
    aggregate_errors: List[Dict[str, object]] = []

    for spec in spectra:
        try:
            payload = eso_fetcher.fetch(target=spec.target_name, identifier=spec.identifier)
        except eso_fetcher.EsoFetchError as exc:
            aggregate_errors.append(
                {
                    "identifier": spec.identifier,
                    "program": spec.program,
                    "error": str(exc),
                }
            )
            continue
        hit = _build_hit(payload, query, spec)
        if query.programs:
            hit.metadata.setdefault("requested_programs", list(query.programs))
        if query.diagnostics and aggregate_errors:
            hit.provenance.setdefault("diagnostics", list(aggregate_errors))
        yield hit
        yielded += 1
        if yielded >= limit:
            break

    if yielded == 0 and aggregate_errors:
        details = "\n".join(
            f"- {error.get('identifier')} ({error.get('program')}): {error.get('error')}"
            for error in aggregate_errors
        )
        raise eso_fetcher.EsoFetchError(
            "ESO fetch attempts failed for all matching programs.\n" + details
        )


refresh_spectra()
