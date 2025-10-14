"""Helpers for rendering IR functional-group predictions in the UI."""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np
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
    peak_fraction: float | None = None
    peak_cm_1: float | None = None
    score: float | None = None

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


def _normalise_spectrum(
    wavenumbers: Sequence[float], intensities: Sequence[float]
) -> tuple[np.ndarray, np.ndarray]:
    arr_w = np.asarray(wavenumbers, dtype=float)
    arr_f = np.asarray(intensities, dtype=float)
    mask = np.isfinite(arr_w) & np.isfinite(arr_f)
    arr_w = arr_w[mask]
    arr_f = arr_f[mask]
    if arr_w.size == 0:
        return arr_w, arr_f
    return arr_w, arr_f


def _refine_range_with_spectrum(
    entry: FunctionalGroupRange,
    wavenumbers: np.ndarray,
    intensities: np.ndarray,
    *,
    max_intensity: float,
) -> tuple[FunctionalGroupRange | None, float]:
    if max_intensity <= 0 or wavenumbers.size == 0:
        return None, 0.0

    span_low = min(entry.low_cm_1, entry.high_cm_1)
    span_high = max(entry.low_cm_1, entry.high_cm_1)
    mask = (wavenumbers >= span_low) & (wavenumbers <= span_high)
    if not np.any(mask):
        return None, 0.0

    local_w = wavenumbers[mask]
    local_i = np.abs(intensities[mask])
    if local_w.size == 0:
        return None, 0.0

    peak = float(np.max(local_i))
    if peak <= 0:
        return None, 0.0

    peak_fraction = float(min(peak / max_intensity, 1.0)) if max_intensity > 0 else 0.0
    peak_idx = int(np.argmax(local_i))
    peak_cm_1 = float(local_w[peak_idx])

    half_height = peak * 0.45
    width_mask = local_i >= half_height
    if not np.any(width_mask):
        width_mask = local_i >= peak * 0.3

    width_w = local_w[width_mask]
    if width_w.size == 0:
        width_w = np.array([peak_cm_1])

    refined_low = float(np.min(width_w))
    refined_high = float(np.max(width_w))

    refined_low = max(refined_low, span_low)
    refined_high = min(refined_high, span_high)

    if refined_high <= refined_low:
        refined_high = span_high
        refined_low = span_low
    else:
        original_span = span_high - span_low
        refined_span = refined_high - refined_low
        min_span = max(original_span * 0.1, 6.0)
        if refined_span < min_span:
            pad = (min_span - refined_span) / 2
            refined_high = min(refined_high + pad, span_high)
            refined_low = max(refined_low - pad, span_low)

    high_cm_1 = max(refined_high, refined_low)
    low_cm_1 = min(refined_high, refined_low)

    probability = entry.probability or 0.0
    score = float(probability * math.sqrt(peak_fraction)) if probability > 0 else 0.0

    refined = replace(
        entry,
        high_cm_1=high_cm_1,
        low_cm_1=low_cm_1,
        peak_fraction=peak_fraction,
        peak_cm_1=peak_cm_1,
        score=score,
    )
    return refined, peak_fraction


def shaded_ranges_for_predictions(
    predictions: Sequence[FunctionalGroupPrediction],
    *,
    probability_floor: float = 0.25,
    shrink_ratio: float = 0.18,
    wavenumbers: Sequence[float] | None = None,
    intensities: Sequence[float] | None = None,
    min_peak_fraction: float = 0.18,
    top_ranges: int = 10,
    cluster_window: float = 28.0,
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

    if not shaded:
        return []

    if wavenumbers is None or intensities is None:
        shaded.sort(key=lambda item: item.probability or 0.0, reverse=True)
        if top_ranges:
            shaded = shaded[:top_ranges]
        return shaded

    arr_w, arr_f = _normalise_spectrum(wavenumbers, intensities)
    if arr_w.size == 0:
        shaded.sort(key=lambda item: item.probability or 0.0, reverse=True)
        if top_ranges:
            shaded = shaded[:top_ranges]
        return shaded

    max_intensity = float(np.max(np.abs(arr_f))) if arr_f.size else 0.0
    refined: List[FunctionalGroupRange] = []
    for entry in shaded:
        updated, peak_fraction = _refine_range_with_spectrum(
            entry, arr_w, arr_f, max_intensity=max_intensity
        )
        probability = entry.probability or 0.0
        if updated is None:
            continue
        if peak_fraction < min_peak_fraction:
            if probability < 0.9:
                continue
        refined.append(updated)

    if not refined:
        shaded.sort(key=lambda item: item.probability or 0.0, reverse=True)
        if top_ranges:
            shaded = shaded[:top_ranges]
        return shaded

    refined.sort(
        key=lambda item: (
            item.score or 0.0,
            item.peak_fraction or 0.0,
            item.probability or 0.0,
        ),
        reverse=True,
    )

    if cluster_window and cluster_window > 0:
        clustered: List[FunctionalGroupRange] = []
        seen: Dict[int, FunctionalGroupRange] = {}
        width = max(float(cluster_window), 1.0)
        for entry in refined:
            peak = entry.peak_cm_1 or (entry.high_cm_1 + entry.low_cm_1) / 2.0
            bucket = int(round(peak / width))
            if bucket in seen:
                continue
            seen[bucket] = entry
            clustered.append(entry)
        refined = clustered

    if top_ranges:
        refined = refined[:top_ranges]

    return refined


def _color_for_entry(entry: FunctionalGroupRange) -> str:
    probability = max(0.0, min(entry.probability or 0.0, 1.0))
    intensity = max(0.0, min(entry.peak_fraction or probability, 1.0))
    blend = min(1.0, 0.6 * math.sqrt(probability) + 0.4 * math.sqrt(intensity))
    start = (120, 144, 156)
    end = (21, 101, 192)
    red = int(start[0] + (end[0] - start[0]) * blend)
    green = int(start[1] + (end[1] - start[1]) * blend)
    blue = int(start[2] + (end[2] - start[2]) * blend)
    alpha = 0.06 + 0.24 * blend
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
        sequence[idx].score or 0.0,
        sequence[idx].peak_fraction or 0.0,
        sequence[idx].probability or 0.0,
    )
    annotate_indices = {
        idx for idx in sorted(range(len(sequence)), key=sort_key, reverse=True)[:max_annotations]
    }

    for index, entry in enumerate(sequence):
        x0, x1 = entry.high_cm_1, entry.low_cm_1
        if axis_reversed:
            x0, x1 = x1, x0
        fillcolor = _color_for_entry(entry)
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
