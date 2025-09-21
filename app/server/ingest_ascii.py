from __future__ import annotations

import hashlib
from typing import Dict, Iterable

import pandas as pd

from .units import canonical_unit, to_nm


def checksum_bytes(content: bytes) -> str:
    """Return a stable SHA-256 digest for the provided payload."""

    return hashlib.sha256(content).hexdigest()


def _detect_columns(columns: Iterable[str]) -> tuple[str, str]:
    wavelength = next((name for name in columns if "wave" in name.lower()), None)
    flux = next(
        (
            name
            for name in columns
            if "intensity" in name.lower() or "flux" in name.lower()
        ),
        None,
    )
    if wavelength is None or flux is None:
        raise ValueError("Missing wavelength or intensity/flux column in ASCII data")
    return wavelength, flux


def _infer_unit(column: str, assumed_unit: str) -> str:
    label = column.lower()
    if "nm" in label:
        return "nm"
    if "ang" in label or "å" in label:
        return "Å"
    return assumed_unit


def parse_ascii(fp, content_bytes: bytes, assumed_unit: str = "nm") -> Dict[str, object]:
    """Parse a CSV/TXT spectrum into the normalised overlay payload format."""

    df = pd.read_csv(fp)
    wavelength_col, flux_col = _detect_columns(df.columns)
    unit = _infer_unit(wavelength_col, assumed_unit)

    wavelengths = to_nm(df[wavelength_col].tolist(), unit)
    flux = df[flux_col].tolist()

    return {
        "wavelength": wavelengths,
        "flux": flux,
        "unit_wavelength": "nm",
        "unit_flux": "arb",
        "meta": {"original_unit_wavelength": canonical_unit(unit)},
        "checksum": checksum_bytes(content_bytes),
    }
