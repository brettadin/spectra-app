import pytest

from app.providers.base import ProviderQuery
from app.providers import sdss as provider


def _fake_available_targets():
    return (
        {
            "canonical_name": "SDSS J234828.73+164429.3",
            "label": "SDSS J234828.73+164429.3 (F3/F5V)",
            "plate": 6138,
            "mjd": 56598,
            "fiber": 934,
            "subclass": "F3/F5V",
            "sn_median_r": 171.8,
            "ra_deg": 357.1197,
            "dec_deg": 16.74147,
            "instrument": "SDSS/BOSS",
            "data_release": "SDSS DR17",
            "aliases": ("SDSS J234828.73+164429.3", "6138-56598-0934"),
        },
    )


def _fake_payload():
    return {
        "wavelength_nm": [360.0, 361.0, 362.0],
        "intensity": [1.0, 0.95, 1.02],
        "meta": {
            "archive": "SDSS DR17",
            "target_name": "SDSS J234828.73+164429.3",
            "instrument": "SDSS/BOSS",
            "plate": 6138,
            "mjd": 56598,
            "fiber": 934,
            "subclass": "F3/F5V",
            "sn_median_r": 171.8,
            "wavelength_min_nm": 360.0,
            "wavelength_max_nm": 362.0,
            "wavelength_effective_range_nm": [360.0, 362.0],
        },
    }


def test_search_fetches_sdss_data(monkeypatch):
    fetch_calls: list[tuple[int, int, int]] = []

    def fake_fetch(*, target: str, plate: int, mjd: int, fiber: int, **kwargs):
        fetch_calls.append((plate, mjd, fiber))
        return _fake_payload()

    monkeypatch.setattr(provider.sdss_fetcher, "available_targets", _fake_available_targets)
    monkeypatch.setattr(provider.sdss_fetcher, "fetch", fake_fetch)
    provider.refresh_targets()

    query = ProviderQuery(target="SDSS J234828")
    hits = list(provider.search(query))

    assert len(hits) == 1
    hit = hits[0]
    assert hit.provider == "SDSS"
    assert hit.identifier == "6138-56598-0934"
    assert "SDSS/BOSS" in hit.summary
    assert "171.8" in hit.summary
    assert hit.metadata["plate"] == 6138
    assert hit.metadata["wavelength_range_nm"] == [360.0, 362.0]
    assert hit.provenance["archive"] == "SDSS DR17"
    assert fetch_calls == [(6138, 56598, 934)]


def test_unknown_target_raises(monkeypatch):
    monkeypatch.setattr(provider.sdss_fetcher, "available_targets", _fake_available_targets)

    def fake_fetch(**kwargs):  # pragma: no cover - defensive
        raise AssertionError("fetch should not be called")

    monkeypatch.setattr(provider.sdss_fetcher, "fetch", fake_fetch)
    provider.refresh_targets()

    with pytest.raises(provider.sdss_fetcher.SdssFetchError):
        list(provider.search(ProviderQuery(target="Unknown")))


def teardown_module(module):  # pragma: no cover - cleanup
    provider.refresh_targets()
