# app/server/fetch_archives.py
# Spectra App v1.1.4
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .fetchers import doi, eso, mast, nist, sdss, simbad

class FetchError(Exception):
    pass

def fetch_spectrum(archive: str, **kwargs) -> Dict[str, Any]:
    archive = (archive or '').lower()
    if archive == 'mast':
        return mast.fetch(**kwargs)
    if archive == 'simbad':
        return simbad.fetch(**kwargs)
    if archive == 'eso':
        return eso.fetch(**kwargs)
    if archive == 'sdss':
        return sdss.fetch(**kwargs)
    if archive == 'nist':
        return nist.fetch(**kwargs)
    if archive == 'doi':
        return doi.fetch(**kwargs)
    raise FetchError(f'Unsupported archive: {archive}')


def materialise_curated_mast_library(
    base: Path | str,
    *,
    force_refresh: bool = False,
) -> Path:
    """Download the curated CALSPEC spectra and record their provenance."""

    base_path = Path(base)
    output_dir = base_path / "data" / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "targets": [],
    }

    for entry in mast.available_targets():
        canonical_name = entry.get("canonical_name", "")
        if not canonical_name:
            continue
        preferred_modes = entry.get("preferred_modes", ())
        instrument_hint = ""
        if isinstance(preferred_modes, (list, tuple)) and preferred_modes:
            instrument_hint = str(preferred_modes[0])

        payload = mast.fetch(
            target=canonical_name,
            instrument=instrument_hint,
            force_refresh=force_refresh,
        )

        wavelengths = payload.get("wavelength_nm") or []
        intensities = payload.get("intensity") or []
        metadata = dict(payload.get("meta") or {})

        manifest["targets"].append(
            {
                "canonical_name": canonical_name,
                "instrument_request": instrument_hint or entry.get("instrument_label"),
                "spectral_type": entry.get("spectral_type"),
                "distance_pc": entry.get("distance_pc"),
                "wavelength_points": len(wavelengths),
                "intensity_points": len(intensities),
                "provenance": metadata,
            }
        )

    output_path = output_dir / "mast_curated_library.json"
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output_path
