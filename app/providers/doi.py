from __future__ import annotations

"""DOI provider adapter returning published spectra from Zenodo records."""

from dataclasses import dataclass
import unicodedata
import re
from typing import Dict, Iterable, List, Tuple

from app.server.fetchers import doi as doi_fetcher

from .base import ProviderHit, ProviderQuery


@dataclass(frozen=True)
class _DoiInfo:
    doi: str
    label: str
    target_name: str
    instrument: str
    description: str
    citation: str
    archive: str
    search_tokens: Tuple[str, ...]


_SPECTRA: Tuple[_DoiInfo, ...] = ()


def refresh_spectra() -> None:
    global _SPECTRA
    _SPECTRA = _load_spectra()


def _load_spectra() -> Tuple[_DoiInfo, ...]:
    records: List[_DoiInfo] = []
    for entry in doi_fetcher.available_spectra():
        tokens = set(entry.get("aliases", ()))  # type: ignore[arg-type]
        tokens.add(_normalise_token(entry.get("doi", "")))
        tokens.add(_normalise_token(entry.get("label", "")))
        tokens.add(_normalise_token(entry.get("target_name", "")))
        tokens.discard("")
        records.append(
            _DoiInfo(
                doi=str(entry.get("doi", "")),
                label=str(entry.get("label", "")),
                target_name=str(entry.get("target_name", "")),
                instrument=str(entry.get("instrument", "")),
                description=str(entry.get("description", "")),
                citation=str(entry.get("citation", "")),
                archive=str(entry.get("archive", "DOI")),
                search_tokens=tuple(sorted(_normalise_token(token) for token in tokens if token)),
            )
        )
    return tuple(records)


def _normalise_token(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_only.lower())


def _match_spectra(query: ProviderQuery) -> List[_DoiInfo]:
    if not _SPECTRA:
        return []

    catalog_filter = query.catalog.lower() if query.catalog else ""

    search_terms: List[str] = []
    for value in (query.doi, query.target, query.text):
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
                        if spec.doi not in seen:
                            matches.append(spec)
                            seen.add(spec.doi)
                        break

    if catalog_filter:
        matches = [
            spec for spec in matches if catalog_filter in spec.archive.lower()
        ]
    return matches


def _build_summary(meta: dict, spec: _DoiInfo) -> str:
    parts: List[str] = [spec.instrument or "Spectrum"]
    w_range = meta.get("wavelength_effective_range_nm") or meta.get("wavelength_range_nm")
    if isinstance(w_range, (list, tuple)) and len(w_range) == 2:
        try:
            low = float(w_range[0])
            high = float(w_range[1])
        except (TypeError, ValueError):  # pragma: no cover - defensive
            low = high = None  # type: ignore[assignment]
        else:
            parts.append(f"{low:.0f}–{high:.0f} nm")
    parts.append(spec.archive)
    return " • ".join(part for part in parts if part)


def _build_metadata(meta: dict, spec: _DoiInfo) -> dict:
    metadata = {
        "target_name": meta.get("target_name") or spec.target_name,
        "instrument": meta.get("instrument") or spec.instrument,
        "description": meta.get("description") or spec.description,
        "doi": meta.get("doi") or spec.doi,
        "citation": meta.get("citation_text") or spec.citation,
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
        "archive": meta.get("archive"),
        "access_url": meta.get("access_url"),
        "doi": meta.get("doi"),
        "record_id": meta.get("record_id"),
        "filename": meta.get("filename"),
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


def _build_hit(payload: dict, query: ProviderQuery, spec: _DoiInfo) -> ProviderHit:
    wavelengths = payload.get("wavelength_nm") or []
    flux = payload.get("intensity") or []
    meta = dict(payload.get("meta") or {})

    summary = _build_summary(meta, spec)
    metadata = _build_metadata(meta, spec)
    provenance = _build_provenance(meta, query)

    return ProviderHit(
        provider="DOI",
        identifier=spec.doi,
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
        raise doi_fetcher.DoiFetchError("No DOI spectra matched the query.")

    limit = max(1, int(query.limit or 1))
    yielded = 0
    aggregate_errors: List[Dict[str, object]] = []

    for spec in spectra:
        try:
            payload = doi_fetcher.fetch(doi=spec.doi, target=spec.target_name)
        except doi_fetcher.DoiFetchError as exc:
            aggregate_errors.append(
                {
                    "doi": spec.doi,
                    "archive": spec.archive,
                    "error": str(exc),
                }
            )
            continue
        hit = _build_hit(payload, query, spec)
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
            f"- {error.get('doi')} ({error.get('archive')}): {error.get('error')}"
            for error in aggregate_errors
        )
        raise doi_fetcher.DoiFetchError(
            "DOI fetch attempts failed for all matching records.\n" + details
        )


refresh_spectra()
