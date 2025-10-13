"""Helpers for rendering IR functional-group predictions in the UI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

import plotly.graph_objects as go

from ml import FunctionalGroupPrediction


@dataclass(frozen=True)
class FunctionalGroupRange:
    group: str
    band: str
    high_cm_1: float
    low_cm_1: float
    notes: str = ""

    @property
    def range_tuple(self) -> tuple[float, float]:
        return (self.high_cm_1, self.low_cm_1)


# Representative correlation ranges compiled from common NIST and SDBS IR charts.
# Values are approximate and provide visual guidance for the ML predictions.
FUNCTIONAL_GROUP_RANGES: Dict[str, List[FunctionalGroupRange]] = {
    "Alkane": [
        FunctionalGroupRange("Alkane", "C–H stretch", 3000, 2850, "sp3 C–H"),
        FunctionalGroupRange("Alkane", "C–H bend", 1470, 1370, "methyl deformation"),
    ],
    "Alkene": [
        FunctionalGroupRange("Alkene", "C=C stretch", 1680, 1620),
        FunctionalGroupRange("Alkene", "=C–H bend", 1000, 650),
    ],
    "Alkyne": [
        FunctionalGroupRange("Alkyne", "C≡C stretch", 2260, 2100),
        FunctionalGroupRange("Alkyne", "≡C–H stretch", 3330, 3260),
    ],
    "Arene": [
        FunctionalGroupRange("Arene", "Aromatic C=C", 1600, 1400),
        FunctionalGroupRange("Arene", "Out-of-plane C–H", 900, 670),
    ],
    "Haloalkane": [
        FunctionalGroupRange("Haloalkane", "C–Cl", 800, 600),
        FunctionalGroupRange("Haloalkane", "C–Br", 650, 500),
    ],
    "Alcohol": [
        FunctionalGroupRange("Alcohol", "O–H stretch", 3650, 3200, "broad hydrogen bonding"),
        FunctionalGroupRange("Alcohol", "C–O stretch", 1260, 1000),
    ],
    "Aldehyde": [
        FunctionalGroupRange("Aldehyde", "C=O stretch", 1740, 1690),
        FunctionalGroupRange("Aldehyde", "Fermi doublet", 2830, 2695),
    ],
    "Ketone": [
        FunctionalGroupRange("Ketone", "C=O stretch", 1750, 1680),
    ],
    "Carboxylic acid": [
        FunctionalGroupRange("Carboxylic acid", "O–H stretch", 3550, 2500, "very broad"),
        FunctionalGroupRange("Carboxylic acid", "C=O stretch", 1725, 1700),
    ],
    "Acid anhydride": [
        FunctionalGroupRange("Acid anhydride", "Asymmetric C=O", 1850, 1770),
        FunctionalGroupRange("Acid anhydride", "Symmetric C=O", 1780, 1710),
    ],
    "Acyl halide": [
        FunctionalGroupRange("Acyl halide", "C=O stretch", 1820, 1770),
        FunctionalGroupRange("Acyl halide", "C–Cl stretch", 800, 600),
    ],
    "Ester": [
        FunctionalGroupRange("Ester", "C=O stretch", 1750, 1730),
        FunctionalGroupRange("Ester", "C–O stretch", 1300, 1000),
    ],
    "Ether": [
        FunctionalGroupRange("Ether", "C–O stretch", 1200, 1020),
    ],
    "Amine": [
        FunctionalGroupRange("Amine", "N–H stretch", 3500, 3250),
        FunctionalGroupRange("Amine", "C–N stretch", 1250, 1000),
    ],
    "Amide": [
        FunctionalGroupRange("Amide", "Amide I", 1700, 1630),
        FunctionalGroupRange("Amide", "Amide II", 1570, 1510),
    ],
    "Nitrile": [
        FunctionalGroupRange("Nitrile", "C≡N stretch", 2260, 2220),
    ],
    "Imide": [
        FunctionalGroupRange("Imide", "Symmetric C=O", 1775, 1700),
    ],
    "Imine": [
        FunctionalGroupRange("Imine", "C=N stretch", 1690, 1640),
    ],
    "Azo compound": [
        FunctionalGroupRange("Azo compound", "N=N stretch", 1600, 1500),
    ],
    "Thiol": [
        FunctionalGroupRange("Thiol", "S–H stretch", 2600, 2550),
    ],
    "Thial": [
        FunctionalGroupRange("Thial", "C=S stretch", 1200, 1040),
    ],
    "Sulfone": [
        FunctionalGroupRange("Sulfone", "S=O stretch", 1350, 1290),
    ],
    "Sulfonic acid": [
        FunctionalGroupRange("Sulfonic acid", "S=O stretch", 1350, 1180),
    ],
    "Enol": [
        FunctionalGroupRange("Enol", "O–H stretch", 3600, 3200),
    ],
    "Phenol": [
        FunctionalGroupRange("Phenol", "O–H stretch", 3650, 3200),
    ],
    "Hydrazine": [
        FunctionalGroupRange("Hydrazine", "N–H stretch", 3500, 3150),
    ],
    "Enamine": [
        FunctionalGroupRange("Enamine", "C=C stretch", 1640, 1600),
    ],
    "Isocyanate": [
        FunctionalGroupRange("Isocyanate", "N=C=O stretch", 2280, 2230),
    ],
    "Isothiocyanate": [
        FunctionalGroupRange("Isothiocyanate", "N=C=S stretch", 2160, 2090),
    ],
    "Phosphine": [
        FunctionalGroupRange("Phosphine", "P–H stretch", 2400, 2300),
    ],
    "Sulfonamide": [
        FunctionalGroupRange("Sulfonamide", "S=O stretch", 1360, 1290),
        FunctionalGroupRange("Sulfonamide", "N–H stretch", 3400, 3200),
    ],
    "Sulfonate": [
        FunctionalGroupRange("Sulfonate", "S=O stretch", 1350, 1180),
    ],
    "Sulfoxide": [
        FunctionalGroupRange("Sulfoxide", "S=O stretch", 1070, 1030),
    ],
    "Thioamide": [
        FunctionalGroupRange("Thioamide", "C=S stretch", 1200, 1120),
    ],
    "Hydrazone": [
        FunctionalGroupRange("Hydrazone", "C=N stretch", 1660, 1600),
    ],
    "Carbamate": [
        FunctionalGroupRange("Carbamate", "C=O stretch", 1740, 1700),
    ],
    "Sulfide": [
        FunctionalGroupRange("Sulfide", "C–S stretch", 740, 570),
    ],
}


def shaded_ranges_for_predictions(
    predictions: Sequence[FunctionalGroupPrediction],
    *,
    probability_floor: float = 0.25,
) -> List[FunctionalGroupRange]:
    """Return the correlation ranges to visualise for the predicted groups."""

    shaded: List[FunctionalGroupRange] = []
    for item in predictions:
        if item.probability < probability_floor:
            continue
        ranges = FUNCTIONAL_GROUP_RANGES.get(item.name)
        if not ranges:
            continue
        shaded.extend(ranges)
    return shaded


def apply_shaded_ranges(
    fig: go.Figure,
    ranges: Iterable[FunctionalGroupRange],
    *,
    axis_reversed: bool = True,
) -> None:
    """Add shaded rectangles for each functional-group correlation range."""

    for index, entry in enumerate(ranges):
        x0, x1 = entry.high_cm_1, entry.low_cm_1
        if axis_reversed:
            x0, x1 = x1, x0
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=0,
            y1=1,
            yref="paper",
            fillcolor="rgba(255, 196, 45, 0.15)",
            line=dict(width=0),
            layer="below",
        )
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=1.02,
            text=f"{entry.group}: {entry.band}",
            showarrow=False,
            xref="x",
            yref="paper",
            font=dict(size=11),
            opacity=0.85,
        )


def build_prediction_table(
    predictions: Sequence[FunctionalGroupPrediction],
    *,
    probability_floor: float = 0.05,
) -> List[Mapping[str, object]]:
    """Convert predictions into table rows for Streamlit."""

    rows: List[Mapping[str, object]] = []
    for item in predictions:
        if item.probability < probability_floor:
            continue
        ranges = FUNCTIONAL_GROUP_RANGES.get(item.name) or []
        if not ranges:
            notes = f"Threshold {item.threshold:.2f}"
            rows.append(
                {
                    "Band (cm⁻¹)": "—",
                    "Range (cm⁻¹)": "—",
                    "Group": item.name,
                    "Confidence": f"{item.probability:.2f}",
                    "Source": "ML",
                    "Notes": notes,
                }
            )
            continue

        for band in ranges:
            notes_parts: List[str] = []
            if band.notes:
                notes_parts.append(band.notes)
            notes_parts.append(f"Threshold {item.threshold:.2f}")
            notes = "; ".join(notes_parts)
            rows.append(
                {
                    "Band (cm⁻¹)": band.band,
                    "Range (cm⁻¹)": f"{band.high_cm_1:.0f}–{band.low_cm_1:.0f}",
                    "Group": item.name,
                    "Confidence": f"{item.probability:.2f}",
                    "Source": "ML + Range",
                    "Notes": notes,
                }
            )
    return rows


__all__ = [
    "FUNCTIONAL_GROUP_RANGES",
    "FunctionalGroupRange",
    "apply_shaded_ranges",
    "build_prediction_table",
    "shaded_ranges_for_predictions",
]
