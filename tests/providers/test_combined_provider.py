from __future__ import annotations

import logging
from typing import Iterable

from app.providers.base import ProviderHit, ProviderQuery
from app.providers import combined


def _make_hit(provider: str, identifier: str) -> ProviderHit:
    return ProviderHit(
        provider=provider,
        identifier=identifier,
        label=f"{provider} {identifier}",
        summary=f"Summary for {identifier}",
        wavelengths_nm=(500.0, 510.0),
        flux=(1.0, 0.9),
        metadata={"archive": provider, "identifier": identifier},
        provenance={"archive": provider, "access_url": "https://example.test"},
    )


def test_search_yields_hits_from_each_provider(monkeypatch):
    query = ProviderQuery(target="Vega", limit=2)

    monkeypatch.setattr(combined.mast, "search", lambda q: [_make_hit("MAST", "mast-1")])
    monkeypatch.setattr(combined.eso, "search", lambda q: [_make_hit("ESO", "eso-1")])
    monkeypatch.setattr(combined.sdss, "search", lambda q: [_make_hit("SDSS", "sdss-1")])

    hits = list(combined.search(query))

    assert [hit.provider for hit in hits] == ["MAST", "ESO", "SDSS"]
    assert all(hit.metadata["identifier"].endswith("-1") for hit in hits)


def test_search_continues_when_provider_fails(monkeypatch, caplog):
    query = ProviderQuery(target="Vega", limit=1)

    def failing_search(_query: ProviderQuery) -> Iterable[ProviderHit]:
        raise RuntimeError("MAST offline")

    monkeypatch.setattr(combined.mast, "search", failing_search)
    monkeypatch.setattr(combined.eso, "search", lambda q: [_make_hit("ESO", "eso-2")])
    monkeypatch.setattr(combined.sdss, "search", lambda q: [_make_hit("SDSS", "sdss-2")])

    with caplog.at_level(logging.WARNING):
        hits = list(combined.search(query))

    assert [hit.provider for hit in hits] == ["ESO", "SDSS"]
    assert "MAST offline" in caplog.text
