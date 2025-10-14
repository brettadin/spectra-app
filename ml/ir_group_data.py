"""Shared metadata for IR functional-group classification."""
from __future__ import annotations

from typing import Dict, Tuple

LabelName = str
BandSpec = Tuple[float, float, str, str]


LABEL_NAMES_EXTENDED: Tuple[LabelName, ...] = (
    "Alkane",
    "Alkene",
    "Alkyne",
    "Arene",
    "Haloalkane",
    "Alcohol",
    "Aldehyde",
    "Ketone",
    "Carboxylic acid",
    "Acid anhydride",
    "Acyl halide",
    "Ester",
    "Ether",
    "Amine",
    "Amide",
    "Nitrile",
    "Imide",
    "Imine",
    "Azo compound",
    "Thiol",
    "Thial",
    "Sulfone",
    "Sulfonic acid",
    "Enol",
    "Phenol",
    "Hydrazine",
    "Enamine",
    "Isocyanate",
    "Isothiocyanate",
    "Phosphine",
    "Sulfonamide",
    "Sulfonate",
    "Sulfoxide",
    "Thioamide",
    "Hydrazone",
    "Carbamate",
    "Sulfide",
)


CORRELATION_BANDS: Dict[LabelName, Tuple[BandSpec, ...]] = {
    "Alkane": (
        (3000.0, 2850.0, "C–H stretch", "sp3 C–H"),
        (1470.0, 1370.0, "C–H bend", "methyl deformation"),
    ),
    "Alkene": (
        (1680.0, 1620.0, "C=C stretch", ""),
        (1000.0, 650.0, "=C–H bend", ""),
    ),
    "Alkyne": (
        (2260.0, 2100.0, "C≡C stretch", ""),
        (3330.0, 3260.0, "≡C–H stretch", ""),
    ),
    "Arene": (
        (1600.0, 1400.0, "Aromatic C=C", ""),
        (900.0, 670.0, "Out-of-plane C–H", ""),
    ),
    "Haloalkane": (
        (800.0, 600.0, "C–Cl stretch", ""),
        (650.0, 500.0, "C–Br stretch", ""),
    ),
    "Alcohol": (
        (3650.0, 3200.0, "O–H stretch", "broad hydrogen bonding"),
        (1260.0, 1000.0, "C–O stretch", ""),
    ),
    "Aldehyde": (
        (1740.0, 1690.0, "C=O stretch", ""),
        (2830.0, 2695.0, "Fermi doublet", ""),
    ),
    "Ketone": (
        (1750.0, 1680.0, "C=O stretch", ""),
    ),
    "Carboxylic acid": (
        (3550.0, 2500.0, "O–H stretch", "very broad"),
        (1725.0, 1700.0, "C=O stretch", ""),
    ),
    "Acid anhydride": (
        (1850.0, 1770.0, "Asymmetric C=O", ""),
        (1780.0, 1710.0, "Symmetric C=O", ""),
    ),
    "Acyl halide": (
        (1820.0, 1770.0, "C=O stretch", ""),
        (800.0, 600.0, "C–Cl stretch", ""),
    ),
    "Ester": (
        (1750.0, 1730.0, "C=O stretch", ""),
        (1300.0, 1000.0, "C–O stretch", ""),
    ),
    "Ether": (
        (1200.0, 1020.0, "C–O stretch", ""),
    ),
    "Amine": (
        (3500.0, 3250.0, "N–H stretch", ""),
        (1250.0, 1000.0, "C–N stretch", ""),
    ),
    "Amide": (
        (1700.0, 1630.0, "Amide I", ""),
        (1570.0, 1510.0, "Amide II", ""),
    ),
    "Nitrile": (
        (2260.0, 2220.0, "C≡N stretch", ""),
    ),
    "Imide": (
        (1775.0, 1700.0, "Symmetric C=O", ""),
    ),
    "Imine": (
        (1690.0, 1640.0, "C=N stretch", ""),
    ),
    "Azo compound": (
        (1600.0, 1500.0, "N=N stretch", ""),
    ),
    "Thiol": (
        (2600.0, 2550.0, "S–H stretch", ""),
    ),
    "Thial": (
        (1200.0, 1040.0, "C=S stretch", ""),
    ),
    "Sulfone": (
        (1350.0, 1290.0, "S=O stretch", ""),
    ),
    "Sulfonic acid": (
        (1350.0, 1180.0, "S=O stretch", ""),
    ),
    "Enol": (
        (3600.0, 3200.0, "O–H stretch", ""),
    ),
    "Phenol": (
        (3650.0, 3200.0, "O–H stretch", ""),
    ),
    "Hydrazine": (
        (3500.0, 3150.0, "N–H stretch", ""),
    ),
    "Enamine": (
        (1640.0, 1600.0, "C=C stretch", ""),
    ),
    "Isocyanate": (
        (2280.0, 2230.0, "N=C=O stretch", ""),
    ),
    "Isothiocyanate": (
        (2160.0, 2090.0, "N=C=S stretch", ""),
    ),
    "Phosphine": (
        (2400.0, 2300.0, "P–H stretch", ""),
    ),
    "Sulfonamide": (
        (1360.0, 1290.0, "S=O stretch", ""),
        (3400.0, 3200.0, "N–H stretch", ""),
    ),
    "Sulfonate": (
        (1350.0, 1180.0, "S=O stretch", ""),
    ),
    "Sulfoxide": (
        (1070.0, 1030.0, "S=O stretch", ""),
    ),
    "Thioamide": (
        (1200.0, 1120.0, "C=S stretch", ""),
    ),
    "Hydrazone": (
        (1660.0, 1600.0, "C=N stretch", ""),
    ),
    "Carbamate": (
        (1740.0, 1700.0, "C=O stretch", ""),
    ),
    "Sulfide": (
        (740.0, 570.0, "C–S stretch", ""),
    ),
}


_FALLBACK_BASELINE = 0.35
FALLBACK_THRESHOLDS: Dict[LabelName, float] = {
    name: _FALLBACK_BASELINE for name in LABEL_NAMES_EXTENDED
}
FALLBACK_THRESHOLDS.update(
    {
        "Alkane": 0.32,
        "Alkene": 0.32,
        "Alkyne": 0.3,
        "Arene": 0.3,
        "Haloalkane": 0.28,
        "Alcohol": 0.34,
        "Aldehyde": 0.38,
        "Ketone": 0.38,
        "Carboxylic acid": 0.36,
        "Acid anhydride": 0.4,
        "Acyl halide": 0.38,
        "Ester": 0.36,
        "Amine": 0.33,
        "Amide": 0.37,
        "Nitrile": 0.34,
        "Imide": 0.37,
        "Imine": 0.34,
        "Azo compound": 0.33,
        "Thiol": 0.32,
        "Thial": 0.32,
        "Sulfone": 0.32,
        "Sulfonic acid": 0.33,
        "Enol": 0.34,
        "Phenol": 0.34,
        "Hydrazine": 0.33,
        "Enamine": 0.33,
        "Isocyanate": 0.34,
        "Isothiocyanate": 0.34,
        "Phosphine": 0.31,
        "Sulfonamide": 0.35,
        "Sulfonate": 0.33,
        "Sulfoxide": 0.33,
        "Thioamide": 0.33,
        "Hydrazone": 0.34,
        "Carbamate": 0.35,
        "Sulfide": 0.3,
    }
)


__all__ = [
    "LABEL_NAMES_EXTENDED",
    "CORRELATION_BANDS",
    "FALLBACK_THRESHOLDS",
]
