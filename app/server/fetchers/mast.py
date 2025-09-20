# app/server/fetchers/mast.py
# Minimal MAST fetcher stub for v1.1.4; replace with astroquery.mast logic when wired.
from typing import Dict, Any
def fetch(target: str = '', instrument: str = '', obs_id: str = '', **kwargs) -> Dict[str, Any]:
    # Placeholder that returns a shape-compatible structure
    # Real implementation should download, parse, unit-normalize to nm, and fill provenance.
    return {
        "wavelength_nm": [],
        "intensity": [],
        "meta": {
            "source_type": "fetch",
            "archive": "MAST",
            "target_name": target,
            "instrument": instrument or None,
            "obs_id": obs_id or None,
            "program_id": None,
            "doi": None,
            "access_url": None,
            "citation_text": None,
            "fetched_at_utc": None,
            "file_hash_sha256": None,
            "units_original": None,
            "app_version": "v1.1.4"
        }
    }
