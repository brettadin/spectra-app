"""Helpers for rendering IR functional-group predictions in the UI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

import plotly.graph_objects as go

from ml import FunctionalGroupPrediction
from ml.ir_group_data import CORRELATION_BANDS


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
    group: [
        FunctionalGroupRange(
            group,
            band_name,
            float(high),
            float(low),
            notes,
        )
        for high, low, band_name, notes in bands
    ]
    for group, bands in CORRELATION_BANDS.items()
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
