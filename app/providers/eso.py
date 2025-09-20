from __future__ import annotations

"""ESO provider adapter producing deterministic high-resolution previews."""

from typing import Iterable

import numpy as np

from .base import ProviderHit, ProviderQuery


def _synthetic_eso(seed: int, resolution: float = 0.2) -> tuple[list[float], list[float]]:
    rng = np.random.default_rng(seed)
    wavelengths = np.linspace(380.0, 920.0, int((920.0 - 380.0) / resolution))
    base = 0.6 + 0.2 * np.cos(wavelengths / 22.0 + seed / 3.0)
    features = sum(
        np.exp(-0.5 * ((wavelengths - (450 + offset)) / (8 + idx)) ** 2)
        for idx, offset in enumerate(range(0, 180, 45))
    )
    noise = 0.03 * rng.normal(size=wavelengths.size)
    flux = base + 0.5 * features + noise
    flux -= flux.min()
    return wavelengths.tolist(), flux.tolist()


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    target = query.target or query.text or "ESO Source"
    for idx in range(min(max(query.limit, 1), 3)):
        resolution = 0.25 - idx * 0.05
        wavelengths, flux = _synthetic_eso(idx + 11, resolution)
        identifier = f"ESO-{target[:6].upper()}-{idx+1:02d}"
        summary = f"ESO X-SHOOTER synthetic segment @R~{int(1000/resolution)}"
        metadata = {
            "target": target,
            "instrument": query.instrument or "X-SHOOTER",
            "resolution_nm": resolution,
            "segment": idx + 1,
        }
        provenance = {
            "archive": "ESO",
            "query": query.as_dict(),
        }
        yield ProviderHit(
            provider="ESO",
            identifier=identifier,
            label=f"{target} • X-SHOOTER seg {idx + 1}",
            summary=summary,
            wavelengths_nm=wavelengths,
            flux=flux,
            metadata=metadata,
            provenance=provenance,
        )
