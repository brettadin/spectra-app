from __future__ import annotations

import json
from typing import List, Tuple

from app.server import fetch_archives
from app.server.fetchers import mast


def test_materialise_curated_mast_library(monkeypatch, tmp_path):
    fake_targets = (
        {
            "canonical_name": "Sirius A",
            "instrument_label": "HST/STIS",
            "spectral_type": "A1 V",
            "distance_pc": 2.64,
            "preferred_modes": ("stis",),
        },
    )

    fetch_calls: List[Tuple[str, str, bool]] = []

    monkeypatch.setattr(mast, "available_targets", lambda: fake_targets)

    def fake_fetch(target: str, instrument: str = "", force_refresh: bool = False, **kwargs):
        fetch_calls.append((target, instrument, force_refresh))
        return {
            "wavelength_nm": [100.0, 110.0],
            "intensity": [1.0, 0.9],
            "meta": {
                "archive": mast.ARCHIVE_LABEL,
                "target_name": target,
                "instrument": "HST/STIS",
                "obs_id": "sirius_stis_003.fits",
                "fetched_at_utc": "2025-10-02T00:00:00Z",
                "cache_path": "/tmp/cache/sirius_stis_003.fits",
                "download_agent": "astroquery.utils.download_file",
            },
        }

    monkeypatch.setattr(mast, "fetch", fake_fetch)

    manifest_path = fetch_archives.materialise_curated_mast_library(tmp_path, force_refresh=True)
    manifest = json.loads(manifest_path.read_text())

    assert manifest_path.name == "mast_curated_library.json"
    assert manifest.get("targets")
    target_entry = manifest["targets"][0]
    assert target_entry["canonical_name"] == "Sirius A"
    assert target_entry["instrument_request"] == "stis"
    assert target_entry["wavelength_points"] == 2
    assert target_entry["provenance"]["archive"] == mast.ARCHIVE_LABEL
    assert target_entry["provenance"]["obs_id"] == "sirius_stis_003.fits"

    assert fetch_calls == [("Sirius A", "stis", True)]
