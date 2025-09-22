from __future__ import annotations

"""Provider registry and helper functions for archive integration."""

from types import ModuleType
from typing import Dict, List, Optional, Sequence

from .base import ProviderHit, ProviderQuery
from . import doi, eso, mast, sdss

_PROVIDER_MAP: Dict[str, Optional[ModuleType]] = {
    "ALL": None,
    "MAST": mast,
    "ESO": eso,
    "SDSS": sdss,
    "DOI": doi,
}


def providers() -> Sequence[str]:
    """Return the list of available provider identifiers."""

    return list(_PROVIDER_MAP.keys())


def get_provider(name: str):  # type: ignore[override]
    key = (name or "").upper()
    if key not in _PROVIDER_MAP:
        raise KeyError(f"Unknown provider: {name!r}")
    provider_module = _PROVIDER_MAP[key]
    if provider_module is None:
        from . import combined

        provider_module = combined
        _PROVIDER_MAP[key] = provider_module
    return provider_module


def search(name: str, query: ProviderQuery) -> List[ProviderHit]:
    """Run a provider search returning inline spectra hits."""

    provider = get_provider(name)
    return list(provider.search(query))


def provider_labels() -> Dict[str, str]:
    """Human readable provider titles used in the UI."""

    return {
        "ALL": "All Archives",
        "MAST": "MAST",  # Mikulski Archive for Space Telescopes
        "ESO": "ESO",  # European Southern Observatory
        "SDSS": "SDSS",  # Sloan Digital Sky Survey
        "DOI": "DOI",  # DOI-based ingest
    }

__all__ = [
    "ProviderHit",
    "ProviderQuery",
    "providers",
    "provider_labels",
    "search",
    "get_provider",
]
