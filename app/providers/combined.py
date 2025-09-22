from __future__ import annotations

"""Aggregated provider that queries multiple archives in a single pass."""

import logging
from typing import Iterable, Tuple

from .base import ProviderHit, ProviderQuery
from . import eso, mast, sdss

_LOG = logging.getLogger(__name__)

_PROVIDER_SEQUENCE: Tuple[Tuple[str, object], ...] = (
    ("MAST", mast),
    ("ESO", eso),
    ("SDSS", sdss),
)


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    """Yield hits from all archive providers, skipping failures."""

    for provider_name, module in _PROVIDER_SEQUENCE:
        try:
            for hit in module.search(query):
                yield hit
        except Exception as exc:
            _LOG.warning(
                "Combined provider failed to fetch results from %s: %s",
                provider_name,
                exc,
                exc_info=True,
            )
            continue

    # Future work: when the SIMBAD resolver is implemented the combined provider
    # will call it here if no curated targets match the query. This keeps the
    # integration point centralised for upcoming patches.
