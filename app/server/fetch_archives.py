# app/server/fetch_archives.py
# Spectra App v1.1.4
from typing import Dict, Any
from .fetchers import mast, simbad, eso

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
    raise FetchError(f'Unsupported archive: {archive}')
