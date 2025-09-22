import pytest

from app.providers.base import ProviderQuery
from app.providers import eso as provider


def _fake_available_spectra():
    return (
        {
            "identifier": "SZ71-UVB",
            "target_name": "Sz 71",
            "label": "Sz 71 • X-Shooter UVB",
            "mode": "UVB",
            "instrument": "VLT/X-Shooter",
            "program": "PENELLOPE",
            "description": "Mock description",
            "spectral_type": "M1.5e",
            "distance_pc": 155.2,
            "doi": "10.5281/zenodo.test",
            "citation": "Example citation",
            "aliases": ("Sz71",),
        },
    )


def _fake_payload():
    return {
        "wavelength_nm": [300.0, 301.0, 302.0],
        "intensity": [1.0, 0.9, 1.1],
        "meta": {
            "archive": "ESO",
            "target_name": "Sz 71",
            "instrument": "VLT/X-Shooter",
            "mode": "UVB",
            "program": "PENELLOPE",
            "doi": "10.5281/zenodo.test",
            "wavelength_min_nm": 300.0,
            "wavelength_max_nm": 302.0,
            "wavelength_effective_range_nm": [300.0, 302.0],
        },
    }


def test_search_fetches_eso_data(monkeypatch):
    fetch_calls: list[str] = []

    def fake_fetch(*, target: str, identifier: str, **kwargs):
        fetch_calls.append(identifier)
        return _fake_payload()

    monkeypatch.setattr(provider.eso_fetcher, "available_spectra", _fake_available_spectra)
    monkeypatch.setattr(provider.eso_fetcher, "fetch", fake_fetch)
    provider.refresh_spectra()

    query = ProviderQuery(target="Sz 71", limit=1)
    hits = list(provider.search(query))

    assert len(hits) == 1
    hit = hits[0]
    assert hit.provider == "ESO"
    assert hit.identifier == "SZ71-UVB"
    assert "X-Shooter" in hit.summary
    assert hit.metadata["program"] == "PENELLOPE"
    assert hit.metadata["wavelength_range_nm"] == [300.0, 302.0]
    assert hit.provenance["archive"] == "ESO"
    assert fetch_calls == ["SZ71-UVB"]


def test_unknown_target(monkeypatch):
    monkeypatch.setattr(provider.eso_fetcher, "available_spectra", _fake_available_spectra)

    def fake_fetch(**kwargs):  # pragma: no cover - defensive
        raise AssertionError("fetch should not run")

    monkeypatch.setattr(provider.eso_fetcher, "fetch", fake_fetch)
    provider.refresh_spectra()

    with pytest.raises(provider.eso_fetcher.EsoFetchError):
        list(provider.search(ProviderQuery(target="Unknown")))


def teardown_module(module):  # pragma: no cover - cleanup
    provider.refresh_spectra()
