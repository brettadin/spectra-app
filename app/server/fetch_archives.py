# Stubs for archive fetch; real implementation should use astroquery and save provenance.json
from pathlib import Path
import json, time

def save_provenance(base: Path, dataset: str, prov: dict):
    p = base / 'data' / dataset
    p.mkdir(parents=True, exist_ok=True)
    (p/'provenance.json').write_text(json.dumps(prov, indent=2, sort_keys=True))

def fetch_sample_mast(base: Path):
    prov = {
        'target_name': 'Vega',
        'instrument': 'SampleStub',
        'facility': 'MAST',
        'program_id': 'stub',
        'doi': None,
        'source_url': 'https://archive.stsci.edu/',
        'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'original_units': {'wavelength':'nm','flux':'arb'},
        'converted_units': {'wavelength':'nm','flux':'arb'},
        'transformations': [],
        'point_count': 2,
        'wavelength_range': [400, 700]
    }
    save_provenance(base, 'vega_stub', prov)
    return str((base/'data'/'vega_stub'/'provenance.json').resolve())
