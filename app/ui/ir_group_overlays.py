"""Helpers for rendering IR functional-group predictions in the UI."""
from __future__ import annotations

from dataclasses import dataclass, replace
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
    probability: float | None = None

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


def _shrink_range(entry: FunctionalGroupRange, *, shrink_ratio: float) -> tuple[float, float]:
    span = entry.high_cm_1 - entry.low_cm_1
    if span <= 0:
        return entry.high_cm_1, entry.low_cm_1
    shrink = span * min(max(shrink_ratio, 0.0), 0.8)
    adjustment = shrink / 2
    high = entry.high_cm_1 - adjustment
    low = entry.low_cm_1 + adjustment
    if high <= low:
        return entry.high_cm_1, entry.low_cm_1
    return high, low


def shaded_ranges_for_predictions(
    predictions: Sequence[FunctionalGroupPrediction],
    *,
    probability_floor: float = 0.25,
    shrink_ratio: float = 0.18,
) -> List[FunctionalGroupRange]:
    """Return the correlation ranges to visualise for the predicted groups."""

    shaded: List[FunctionalGroupRange] = []
    for item in predictions:
        if item.probability < probability_floor:
            continue
        ranges = FUNCTIONAL_GROUP_RANGES.get(item.name)
        if not ranges:
            continue
        for base in ranges:
            high, low = _shrink_range(base, shrink_ratio=shrink_ratio)
            shaded.append(
                replace(
                    base,
                    high_cm_1=high,
                    low_cm_1=low,
                    probability=item.probability,
                )
            )
    return shaded


def _color_for_probability(probability: float | None) -> str:
    base = 0.0 if probability is None else max(0.0, min(probability, 1.0)) ** 0.5
    start = (120, 144, 156)  # blue grey for lower confidence
    end = (30, 136, 229)  # rich blue for confident hits
    red = int(start[0] + (end[0] - start[0]) * base)
    green = int(start[1] + (end[1] - start[1]) * base)
    blue = int(start[2] + (end[2] - start[2]) * base)
    alpha = 0.08 + 0.22 * base
    return f"rgba({red}, {green}, {blue}, {alpha:.3f})"


def apply_shaded_ranges(
    fig: go.Figure,
    ranges: Iterable[FunctionalGroupRange],
    *,
    axis_reversed: bool = True,
    max_annotations: int = 6,
) -> None:
    """Add shaded rectangles for each functional-group correlation range."""

    sequence = list(ranges)
    if not sequence:
        return

    sort_key = lambda idx: (
        sequence[idx].probability or 0.0,
        -(sequence[idx].high_cm_1 - sequence[idx].low_cm_1),
    )
    annotate_indices = {
        idx for idx in sorted(range(len(sequence)), key=sort_key, reverse=True)[:max_annotations]
    }

    for index, entry in enumerate(sequence):
        x0, x1 = entry.high_cm_1, entry.low_cm_1
        if axis_reversed:
            x0, x1 = x1, x0
        fillcolor = _color_for_probability(entry.probability)
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=0,
            y1=1,
            yref="paper",
            fillcolor=fillcolor,
            line=dict(width=0),
            layer="below",
        )
        if index not in annotate_indices or (entry.probability or 0.0) < 0.25:
            continue
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=1.04,
            text=f"{entry.group} • {entry.band}",
            showarrow=False,
            xref="x",
            yref="paper",
            font=dict(size=10),
            opacity=0.9,
            textangle=-45,
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
