from __future__ import annotations

from pathlib import Path
from typing import List

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
