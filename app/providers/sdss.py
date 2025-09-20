from __future__ import annotations

"""SDSS provider adapter returning coarse-resolution synthetic spectra."""

from typing import Iterable

import numpy as np

from .base import ProviderHit, ProviderQuery


def _synthetic_sdss(seed: int) -> tuple[list[float], list[float]]:
    rng = np.random.default_rng(seed)
    wavelengths = np.linspace(360.0, 890.0, 220)
    continuum = 0.8 + 0.15 * np.sin(wavelengths / 85.0 + seed)
    absorption = 0.3 * np.exp(-0.5 * ((wavelengths - (515 + 30 * seed)) / 18.0) ** 2)
    emission = 0.4 * np.exp(-0.5 * ((wavelengths - 656.0) / 9.0) ** 2)
    noise = 0.06 * rng.normal(size=wavelengths.size)
    flux = continuum - absorption + emission + noise
    flux -= flux.min()
    return wavelengths.tolist(), flux.tolist()


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    target = query.target or query.text or "SDSS Source"
    for idx in range(min(max(query.limit, 1), 4)):
        wavelengths, flux = _synthetic_sdss(idx + 21)
        identifier = f"SDSS-{target[:6].upper()}-{idx+1:02d}"
        summary = "Synthetic SDSS DR18-style preview"
        metadata = {
            "target": target,
            "plate": 4000 + idx,
            "mjd": 59000 + idx,
            "fiber": 200 + idx,
        }
        provenance = {
            "archive": "SDSS",
            "query": query.as_dict(),
        }
        yield ProviderHit(
            provider="SDSS",
            identifier=identifier,
            label=f"{target} • plate {metadata['plate']}",
            summary=summary,
            wavelengths_nm=wavelengths,
            flux=flux,
            metadata=metadata,
            provenance=provenance,
        )
