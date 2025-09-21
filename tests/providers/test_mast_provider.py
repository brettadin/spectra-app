from __future__ import annotations

from typing import List

import pytest

from app.providers.base import ProviderQuery
from app.providers import mast as provider


def _fake_available_targets():
    return (
        {
            "canonical_name": "Sirius A",
            "aliases": ("Sirius", "Alpha CMa"),
            "instrument_label": "HST/STIS",
            "spectral_type": "A1 V",
            "distance_pc": 2.64,
            "description": "Bright primary CALSPEC standard",
            "preferred_modes": ("stis",),
            "fallback_modes": ("mod",),
        },
    )


def _fake_payload():
    return {
        "wavelength_nm": [400.0, 410.0, 420.0],
        "intensity": [1.0, 0.95, 1.05],
        "meta": {
            "archive": "MAST CALSPEC",
            "target_name": "Sirius A",
            "instrument": "HST/STIS",
            "obs_id": "sirius_stis_003.fits",
            "doi": "10.1088/0004-6256/147/6/127",
            "access_url": "https://example.test/sirius",
            "fetched_at_utc": "2025-01-01T00:00:00Z",
            "file_hash_sha256": "abc123",
            "units_original": {"wavelength": "Å", "flux": "erg s^-1 cm^-2 Å^-1"},
            "units_converted": {"wavelength": "nm", "flux": "erg s^-1 cm^-2 nm^-1"},
            "app_version": "v1.2.3",
            "cache_path": "/tmp/sirius.fits",
            "cache_hit": False,
            "spectral_type": "A1 V",
            "distance_pc": 2.64,
            "description": "Bright primary CALSPEC standard",
            "wavelength_min_nm": 115.0,
            "wavelength_max_nm": 2400.0,
        },
    }


def test_search_fetches_calspec_data(monkeypatch):
    fetch_calls: List[tuple[str, str]] = []

    def fake_fetch(target: str, instrument: str = "", **kwargs):
        fetch_calls.append((target, instrument))
        return _fake_payload()

    monkeypatch.setattr(provider.mast_fetcher, "available_targets", _fake_available_targets)
    monkeypatch.setattr(provider.mast_fetcher, "fetch", fake_fetch)
    provider.refresh_targets()

    query = ProviderQuery(target="Sirius", instrument="STIS", limit=1)
    hits = list(provider.search(query))

    assert len(hits) == 1
    hit = hits[0]
    assert hit.provider == "MAST"
    assert hit.metadata["target_name"] == "Sirius A"
    assert hit.summary.startswith("CALSPEC")
    assert hit.provenance["archive"] == "MAST CALSPEC"
    assert hit.provenance["query"]["instrument"] == "STIS"
    assert fetch_calls == [("Sirius A", "STIS")]


def test_partial_target_and_limit(monkeypatch):
    fetch_calls: List[str] = []

    def fake_fetch(target: str, instrument: str = "", **kwargs):
        fetch_calls.append(target)
        return _fake_payload()

    monkeypatch.setattr(provider.mast_fetcher, "available_targets", _fake_available_targets)
    monkeypatch.setattr(provider.mast_fetcher, "fetch", fake_fetch)
    provider.refresh_targets()

    query = ProviderQuery(target="sir", limit=1)
    hits = list(provider.search(query))

    assert len(hits) == 1
    assert hits[0].identifier == "sirius_stis_003.fits"
    assert fetch_calls == ["Sirius A"]


def test_unknown_target_raises(monkeypatch):
    monkeypatch.setattr(provider.mast_fetcher, "available_targets", _fake_available_targets)

    def fake_fetch(*args, **kwargs):  # pragma: no cover - defensive
        raise AssertionError("Fetch should not be called when target is unknown")

    monkeypatch.setattr(provider.mast_fetcher, "fetch", fake_fetch)
    provider.refresh_targets()

    query = ProviderQuery(target="Unknown")
    with pytest.raises(provider.mast_fetcher.MastFetchError):
        list(provider.search(query))


def teardown_module(module):  # pragma: no cover - test cleanup
    provider.refresh_targets()

