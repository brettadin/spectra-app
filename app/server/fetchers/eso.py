# app/server/fetchers/eso.py
# Minimal ESO fetcher stub for v1.1.4
from typing import Dict, Any
def fetch(target: str = '', instrument: str = '', **kwargs) -> Dict[str, Any]:
    return {
        "wavelength_nm": [],
        "intensity": [],
        "meta": {
            "source_type": "fetch",
            "archive": "ESO",
            "target_name": target,
            "instrument": instrument or None,
            "obs_id": None,
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
