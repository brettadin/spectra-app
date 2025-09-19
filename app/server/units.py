from dataclasses import dataclass

SUPPORTED = {'nm':1.0, 'Å':0.1, 'A':0.1, 'um':1000.0, 'µm':1000.0}

def to_nm(values, unit: str):
    u = unit.replace('Angstrom','Å').replace('angstrom','Å')
    u = 'Å' if u in ['Å','A'] else u
    if u not in SUPPORTED:
        raise ValueError(f'Unsupported wavelength unit: {unit}')
    scale = SUPPORTED[u]
    return [v*scale for v in values]

def canonical_unit(unit: str) -> str:
    u = unit.replace('Angstrom','Å').replace('angstrom','Å')
    return 'Å' if u in ['Å','A'] else u

