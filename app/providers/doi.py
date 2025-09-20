from __future__ import annotations

"""DOI provider adapter stub that fabricates provenance-rich spectra."""

from typing import Iterable

import numpy as np

from .base import ProviderHit, ProviderQuery


def _synthetic_doi(seed: int) -> tuple[list[float], list[float]]:
    wavelengths = np.linspace(400.0, 800.0, 180)
    baseline = 1.0 + 0.1 * np.cos(wavelengths / 45.0)
    line = 0.7 * np.exp(-0.5 * ((wavelengths - 486.1) / 4.0) ** 2)
    line += 0.5 * np.exp(-0.5 * ((wavelengths - 656.3) / 5.0) ** 2)
    ripple = 0.1 * np.sin(wavelengths / 18.0 + seed)
    flux = baseline + line + ripple
    flux -= flux.min()
    return wavelengths.tolist(), flux.tolist()


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    doi_value = query.doi or query.text or "10.0000/example"
    title = query.text or "Literature trace"
    wavelengths, flux = _synthetic_doi(7)
    metadata = {
        "doi": doi_value,
        "citation": f"{title} et al. (2022)",
        "journal": "Astronomical Journal",
    }
    provenance = {
        "archive": "DOI",
        "query": query.as_dict(),
        "doi": doi_value,
    }
    yield ProviderHit(
        provider="DOI",
        identifier=doi_value,
        label=f"{title} • DOI {doi_value}",
        summary="DOI-linked synthetic spectrum",
        wavelengths_nm=wavelengths,
        flux=flux,
        metadata=metadata,
        provenance=provenance,
    )
