import pytest

from app.providers.base import ProviderQuery
from app.providers import doi as provider


def _fake_available_spectra():
    return (
        {
            "doi": "10.0000/example",
            "label": "Example Spectrum",
            "target_name": "Example Target",
            "instrument": "Example Instrument",
            "description": "Example description",
            "citation": "Example citation",
            "archive": "Zenodo",
            "aliases": ("Example",),
        },
    )


def _fake_payload():
    return {
        "wavelength_nm": [500.0, 501.0, 502.0],
        "intensity": [1.0, 1.1, 0.9],
        "meta": {
            "archive": "Zenodo",
            "target_name": "Example Target",
            "instrument": "Example Instrument",
            "description": "Example description",
            "doi": "10.0000/example",
            "wavelength_min_nm": 500.0,
            "wavelength_max_nm": 502.0,
            "wavelength_effective_range_nm": [500.0, 502.0],
        },
    }


def test_search_fetches_doi_spectrum(monkeypatch):
    fetch_calls: list[str] = []

    def fake_fetch(*, doi: str, **kwargs):
        fetch_calls.append(doi)
        return _fake_payload()

    monkeypatch.setattr(provider.doi_fetcher, "available_spectra", _fake_available_spectra)
    monkeypatch.setattr(provider.doi_fetcher, "fetch", fake_fetch)
    provider.refresh_spectra()

    query = ProviderQuery(doi="10.0000/example")
    hits = list(provider.search(query))

    assert len(hits) == 1
    hit = hits[0]
    assert hit.provider == "DOI"
    assert hit.identifier == "10.0000/example"
    assert "Example Instrument" in hit.summary
    assert hit.metadata["description"] == "Example description"
    assert hit.provenance["archive"] == "Zenodo"
    assert fetch_calls == ["10.0000/example"]


def test_doi_partial_match(monkeypatch):
    monkeypatch.setattr(provider.doi_fetcher, "available_spectra", _fake_available_spectra)

    def fake_fetch(*, doi: str, **kwargs):
        return _fake_payload()

    monkeypatch.setattr(provider.doi_fetcher, "fetch", fake_fetch)
    provider.refresh_spectra()

    hits = list(provider.search(ProviderQuery(text="example")))
    assert len(hits) == 1


def teardown_module(module):  # pragma: no cover - cleanup
    provider.refresh_spectra()
