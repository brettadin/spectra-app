SUPPORTED = {'nm':1.0, 'Å':0.1, 'A':0.1, 'um':1000.0, 'µm':1000.0}

_ANGSTROM_WORDS = {'angstrom', 'ångström', 'ångstrom'}
_ANGSTROM_SYMBOLS = {'Å', 'A', 'å'}


def _normalize_unit(unit: str) -> str:
    """Return the canonical key used for wavelength unit comparisons."""
    trimmed = unit.strip()
    casefolded = trimmed.casefold()
    casefolded = casefolded.replace('μ', 'µ')
    if casefolded in _ANGSTROM_WORDS or trimmed in _ANGSTROM_SYMBOLS or casefolded == 'å':
        return 'Å'
    return casefolded

def to_nm(values, unit: str):
    u = _normalize_unit(unit)
    if u not in SUPPORTED:
        raise ValueError(f'Unsupported wavelength unit: {unit}')
    scale = SUPPORTED[u]
    return [v*scale for v in values]

def canonical_unit(unit: str) -> str:
    return _normalize_unit(unit)

