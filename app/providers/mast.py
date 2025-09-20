from __future__ import annotations

"""Synthetic MAST adapter delivering deterministic preview spectra."""

from typing import Iterable

import numpy as np

from .base import ProviderHit, ProviderQuery


def _synthetic_spectrum(seed: int, center_nm: float = 550.0) -> tuple[list[float], list[float]]:
    rng = np.random.default_rng(seed)
    wavelengths = np.linspace(350.0, 950.0, 320)
    envelope = np.exp(-0.5 * ((wavelengths - center_nm) / 90.0) ** 2)
    modulation = 0.35 * np.sin(wavelengths / 35.0 + seed)
    noise = 0.05 * rng.normal(size=wavelengths.size)
    flux = envelope * (1.2 + modulation) + noise
    flux -= flux.min()
    return wavelengths.tolist(), flux.tolist()


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    target = query.target or query.text or "Target"
    for idx in range(min(max(query.limit, 1), 5)):
        center = 520.0 + 25.0 * idx
        wavelengths, flux = _synthetic_spectrum(idx + 3, center)
        identifier = f"MAST-{target[:6].upper()}-{idx+1:02d}"
        summary = f"Synthetic preview for {target} centred at {center:.0f} nm"
        metadata = {
            "target": target,
            "instrument": query.instrument or "STIS",
            "exposure": 1200 + 120 * idx,
            "preview_center_nm": center,
        }
        provenance = {
            "archive": "MAST",
            "query": query.as_dict(),
        }
        yield ProviderHit(
            provider="MAST",
            identifier=identifier,
            label=f"{target} • STIS • {center:.0f} nm",
            summary=summary,
            wavelengths_nm=wavelengths,
            flux=flux,
            metadata=metadata,
            provenance=provenance,
        )
