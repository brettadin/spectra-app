from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import pytest

from app.server.fetchers import mast


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self._text = text
        self.status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - trivial
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    @property
    def text(self) -> str:  # pragma: no cover - simple accessor
        return self._text


def _prepare_index_stub() -> _FakeResponse:
    sample_html = '<html><a href="sirius_stis_003.fits">sirius_stis_003.fits</a></html>'
    return _FakeResponse(text=sample_html)


def _prepare_download_stub(
    sample_path: Path,
    calls: List[Tuple[str, str | None, str | None, bool]],
):
    sample_bytes = sample_path.read_bytes()

    def fake_download(
        filename: str,
        *,
        base_url: str | None = None,
        local_path: str | None = None,
        cache: bool = True,
        verbose: bool = False,
    ) -> Tuple[str, None, None]:
        calls.append((filename, base_url, local_path, cache))
        assert base_url == mast.CALSPEC_INDEX_URL
        target_dir = Path(local_path or ".")
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / filename
        dest.write_bytes(sample_bytes)
        return ("COMPLETE", None, None)

    return fake_download


def test_fetch_sirius_from_cached_directory(monkeypatch, tmp_path):
    mast.reset_index_cache()
    download_calls: List[Tuple[str, str | None, str | None, bool]] = []
    sample_file = Path(__file__).resolve().parent.parent / "data" / "calspec" / "sirius_stis_003_subset.fits"
    monkeypatch.setattr(mast.requests, "get", lambda url, *args, **kwargs: _prepare_index_stub())
    monkeypatch.setattr(
        mast.Observations,
        "download_file",
        _prepare_download_stub(sample_file, download_calls),
    )

    result = mast.fetch(target="Sirius", cache_dir=tmp_path)

    assert result["meta"]["archive"] == mast.ARCHIVE_LABEL
    assert result["meta"]["target_name"] == "Sirius A"
    assert result["meta"]["units_original"]["wavelength"] == mast.ORIGINAL_WAVELENGTH_UNIT
    assert result["meta"]["units_converted"]["flux"] == mast.CANONICAL_FLUX_UNIT
    assert result["intensity"][0] > 0.0
    assert len(result["wavelength_nm"]) == 20
    cached_file = tmp_path / mast._resolve_target("Sirius").cache_key / "sirius_stis_003.fits"
    assert cached_file.exists()
    assert download_calls == [
        (
            "sirius_stis_003.fits",
            mast.CALSPEC_INDEX_URL,
            str(cached_file.parent),
            True,
        )
    ]

    download_calls.clear()
    second = mast.fetch(target="Sirius", cache_dir=tmp_path)
    assert second["meta"]["cache_hit"] is True
    assert download_calls == []


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

    def fake_download(url, destination, *, force_refresh: bool = False):
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

