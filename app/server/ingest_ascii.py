import hashlib, pandas as pd
from .units import to_nm, canonical_unit

def checksum_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def parse_ascii(fp, content_bytes: bytes, assumed_unit='nm'):
    df = pd.read_csv(fp)
    wl_col = next((c for c in df.columns if 'wave' in c.lower()), None)
    fl_col = next((c for c in df.columns if 'intensity' in c.lower() or 'flux' in c.lower()), None)
    if wl_col is None or fl_col is None:
        raise ValueError('Missing wavelength or intensity/flux column')
    unit = 'nm' if 'nm' in wl_col.lower() else ('Å' if 'å' in wl_col.lower() or 'ang' in wl_col.lower() else assumed_unit)
    wl_nm = to_nm(df[wl_col].tolist(), unit)
    data = {
        'wavelength': wl_nm,
        'flux': df[fl_col].tolist(),
        'unit_wavelength': 'nm',
        'unit_flux': 'arb',
        'meta': {'original_unit_wavelength': canonical_unit(unit)},
        'checksum': checksum_bytes(content_bytes),
    }
    return data
