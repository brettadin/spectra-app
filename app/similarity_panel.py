from __future__ import annotations

"""Streamlit rendering helpers for similarity metrics."""

import math
from typing import Dict, List, Sequence

import pandas as pd
import streamlit as st

from app.similarity import (
    SimilarityCache,
    SimilarityOptions,
    TraceVectors,
    build_metric_frames,
)


def _format_value(value: float, metric: str) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if metric == "rmse":
        return f"{value:.4f}"
    if metric in {"line_match", "lines"}:
        return f"{value*100:.1f}%"
    return f"{value:.3f}"


def render_similarity_panel(
    traces: Sequence[TraceVectors],
    viewport,
    options: SimilarityOptions,
    cache: SimilarityCache,
) -> Dict[str, pd.DataFrame]:
    if len(traces) < 2:
        st.info("Add at least two visible traces to compute similarity metrics.")
        return {}

    frames, label_lookup = build_metric_frames(traces, viewport, options, cache)
    if not frames:
        st.warning("No overlapping data in the selected viewport.")
        return {}

    st.markdown("### Similarity analysis")
    reference = _resolve_reference(traces, options.reference_id)
    _render_ribbon(reference, traces, viewport, options, cache)
    ordered = _order_frames(frames, options.primary_metric)
    _render_matrices(ordered, label_lookup)
    return frames


def _resolve_reference(traces: Sequence[TraceVectors], reference_id: str | None) -> TraceVectors:
    if reference_id:
        for trace in traces:
            if trace.trace_id == reference_id:
                return trace
    return traces[0]


def _render_ribbon(
    reference: TraceVectors,
    traces: Sequence[TraceVectors],
    viewport,
    options: SimilarityOptions,
    cache: SimilarityCache,
) -> None:
    others = [trace for trace in traces if trace.trace_id != reference.trace_id]
    if not others:
        return

    st.markdown(f"#### Ribbon — reference: **{reference.label}**")
    columns = st.columns(len(others))
    for column, trace in zip(columns, others):
        metrics = cache.compute(reference, trace, viewport, options)
        column.markdown(f"**{trace.label}**")
        for metric in options.metrics:
            label = metric.replace("_", " ").title()
            column.metric(label, _format_value(metrics.get(metric), metric))
        if "points" in metrics:
            column.caption(f"{int(metrics['points'])} shared samples")


def _order_frames(frames: Dict[str, pd.DataFrame], primary: str | None) -> List[tuple[str, pd.DataFrame]]:
    ordered = list(frames.items())
    if primary and primary in frames:
        ordered.sort(key=lambda item: (0 if item[0] == primary else 1, item[0]))
    return ordered


def _display_labels(keys: Sequence[str], lookup: Dict[str, str]) -> List[str]:
    counts: Dict[str, int] = {}
    labels: List[str] = []
    for key in keys:
        base = lookup.get(key, key)
        count = counts.get(base, 0) + 1
        counts[base] = count
        if count == 1:
            labels.append(base)
        else:
            labels.append(f"{base} ({count})")
    return labels


def _render_matrices(
    frames: Sequence[tuple[str, pd.DataFrame]],
    label_lookup: Dict[str, str],
) -> None:
    tab_labels = [name.replace("_", " ").title() for name, _ in frames]
    tabs = st.tabs(tab_labels)
    for tab, (metric, frame) in zip(tabs, frames):
        with tab:
            display = frame.copy()
            display.index = _display_labels(display.index.tolist(), label_lookup)
            display.columns = _display_labels(display.columns.tolist(), label_lookup)
            styled = display.style.format(lambda v, m=metric: _format_value(v, m))
            st.dataframe(styled, width="stretch")
            st.caption("Diagonal entries show self-similarity. NaN indicates insufficient overlap in the viewport.")
