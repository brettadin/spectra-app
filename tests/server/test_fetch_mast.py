from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import pytest

from app.server.fetchers import mast


class _FakeResponse:
    def __init__(self, *, text: str | None = None, content: bytes | None = None) -> None:
        self._text = text
        self._content = content or b""
        self.status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - trivial
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size: int = 8192):  # pragma: no cover - trivial
        data = self._content
        if not data:
            return
        start = 0
        length = len(data)
        while start < length:
            end = min(length, start + chunk_size)
            yield data[start:end]
            start = end

    def __enter__(self):  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - trivial
        return False

    @property
    def text(self) -> str:  # pragma: no cover - simple accessor
        if self._text is None:
            raise AttributeError("No text payload")
        return self._text


def _prepare_fakes(sample_path: Path, urls: List[str]):
    sample_html = '<html><a href="sirius_stis_003.fits">sirius_stis_003.fits</a></html>'
    sample_bytes = sample_path.read_bytes()

    def fake_get(url: str, *args, **kwargs):
        urls.append(url)
        if url == mast.CALSPEC_INDEX_URL:
            return _FakeResponse(text=sample_html)
        if url == mast.CALSPEC_INDEX_URL + "sirius_stis_003.fits":
            return _FakeResponse(content=sample_bytes)
        raise AssertionError(f"Unexpected URL requested: {url}")

    return fake_get


def test_fetch_sirius_from_cached_directory(monkeypatch, tmp_path):
    mast.reset_index_cache()
    calls: List[str] = []
    sample_file = Path(__file__).resolve().parent.parent / "data" / "calspec" / "sirius_stis_003_subset.fits"
    monkeypatch.setattr(mast.requests, "get", _prepare_fakes(sample_file, calls))

    result = mast.fetch(target="Sirius", cache_dir=tmp_path)

    assert result["meta"]["archive"] == mast.ARCHIVE_LABEL
    assert result["meta"]["target_name"] == "Sirius A"
    assert result["meta"]["units_original"]["wavelength"] == mast.ORIGINAL_WAVELENGTH_UNIT
    assert result["meta"]["units_converted"]["flux"] == mast.CANONICAL_FLUX_UNIT
    assert result["intensity"][0] > 0.0
    assert len(result["wavelength_nm"]) == 20
    cached_file = tmp_path / mast._resolve_target("Sirius").cache_key / "sirius_stis_003.fits"
    assert cached_file.exists()
    assert mast.CALSPEC_INDEX_URL in calls
    assert mast.CALSPEC_INDEX_URL + "sirius_stis_003.fits" in calls

    calls.clear()
    second = mast.fetch(target="Sirius", cache_dir=tmp_path)
    assert second["meta"]["cache_hit"] is True
    assert calls == []


def test_unknown_target_raises():
    mast.reset_index_cache()
    with pytest.raises(mast.MastFetchError):
        mast.fetch(target="Unknown Star")


def test_available_targets_metadata():
    targets = mast.available_targets()
    assert {entry["canonical_name"] for entry in targets} >= {"Sirius A", "Vega", "18 Sco"}
    sirius = next(entry for entry in targets if entry["canonical_name"] == "Sirius A")
    assert "sirius" in {alias.lower() for alias in sirius["aliases"]}
    assert sirius["instrument_label"].startswith("HST")



def test_fetch_computes_effective_range(monkeypatch, tmp_path):
    mast.reset_index_cache()
    monkeypatch.setattr(mast, "_list_remote_files", lambda: ["sirius_stis_003.fits"])

    def fake_download(url, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"stub")

    monkeypatch.setattr(mast, "_download_file", fake_download)

    def fake_parse(path):
        return {
            "wavelength_nm": np.array([100.0, 200.0, 250.0, 1000.0, 4000.0]),
            "flux": np.array([1.0, 0.8, 0.9, 0.001, 0.0]),
            "stat_uncertainty": None,
            "sys_uncertainty": None,
        }

    monkeypatch.setattr(mast, "_parse_calspec_spectrum", fake_parse)

    result = mast.fetch(target="Sirius", cache_dir=tmp_path)

    effective = result["meta"].get("wavelength_effective_range_nm")
    assert effective is not None
    assert 90.0 < effective[0] < 150.0
    assert 900.0 < effective[1] < 2000.0

