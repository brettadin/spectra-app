from __future__ import annotations

"""Similarity metrics and memoisation for overlay traces."""

from dataclasses import dataclass
import math
import threading
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

Viewport = Tuple[float | None, float | None]


@dataclass(frozen=True)
class TraceVectors:
    """Numeric representation of a trace used for similarity calculations."""

    trace_id: str
    label: str
    wavelengths_nm: np.ndarray
    flux: np.ndarray
    kind: str = "spectrum"
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "wavelengths_nm", np.asarray(self.wavelengths_nm, dtype=float))
        object.__setattr__(self, "flux", np.asarray(self.flux, dtype=float))

    def cleaned(self) -> "TraceVectors":
        mask = np.isfinite(self.wavelengths_nm) & np.isfinite(self.flux)
        return TraceVectors(
            trace_id=self.trace_id,
            label=self.label,
            wavelengths_nm=self.wavelengths_nm[mask],
            flux=self.flux[mask],
            kind=self.kind,
            fingerprint=self.fingerprint,
        )


@dataclass(frozen=True)
class SimilarityOptions:
    metrics: Tuple[str, ...]
    normalization: str = "unit"
    line_match_top_n: int = 8
    primary_metric: str = "cosine"
    reference_id: str | None = None

    def __post_init__(self) -> None:
        metrics = tuple(metric for metric in self.metrics if metric)
        if not metrics:
            metrics = ("cosine",)
        object.__setattr__(self, "metrics", metrics)


class SimilarityCache:
    """Thread-safe memoisation of pairwise similarity metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[Tuple[str, str, Tuple[float | None, float | None], Tuple[str, ...], str, int], Dict[str, float]] = {}

    def _pair_key(
        self,
        trace_a: TraceVectors,
        trace_b: TraceVectors,
        viewport: Viewport,
        options: SimilarityOptions,
    ) -> Tuple[str, str, Tuple[float | None, float | None], Tuple[str, ...], str, int]:
        identity_a = trace_a.fingerprint or trace_a.trace_id
        identity_b = trace_b.fingerprint or trace_b.trace_id
        ordered = tuple(sorted((identity_a, identity_b)))
        low, high = viewport
        viewport_key = (_normalise_float(low), _normalise_float(high))
        metrics_key = tuple(sorted(options.metrics))
        return ordered + (viewport_key, metrics_key, options.normalization, options.line_match_top_n)

    def compute(
        self,
        trace_a: TraceVectors,
        trace_b: TraceVectors,
        viewport: Viewport,
        options: SimilarityOptions,
    ) -> Dict[str, float]:
        key = self._pair_key(trace_a, trace_b, viewport, options)
        with self._lock:
            cached = self._store.get(key)
        if cached is not None:
            return dict(cached)
        result = _compute_metrics(trace_a, trace_b, viewport, options)
        with self._lock:
            self._store[key] = dict(result)
        return result

    def reset(self) -> None:
        with self._lock:
            self._store.clear()


# ---------------------------------------------------------------------------

def _normalise_float(value: float | None) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value):
        return None
    return round(float(value), 6)


def _prepare_vectors(
    trace_a: TraceVectors,
    trace_b: TraceVectors,
    viewport: Viewport,
) -> Tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    cleaned_a = trace_a.cleaned()
    cleaned_b = trace_b.cleaned()
    if cleaned_a.wavelengths_nm.size == 0 or cleaned_b.wavelengths_nm.size == 0:
        return None, None, None

    wavelengths = np.union1d(cleaned_a.wavelengths_nm, cleaned_b.wavelengths_nm)
    if viewport[0] is not None:
        wavelengths = wavelengths[wavelengths >= viewport[0]]
    if viewport[1] is not None:
        wavelengths = wavelengths[wavelengths <= viewport[1]]
    if wavelengths.size == 0:
        return None, None, None

    values_a = np.interp(
        wavelengths,
        cleaned_a.wavelengths_nm,
        cleaned_a.flux,
        left=np.nan,
        right=np.nan,
    )
    values_b = np.interp(
        wavelengths,
        cleaned_b.wavelengths_nm,
        cleaned_b.flux,
        left=np.nan,
        right=np.nan,
    )
    mask = np.isfinite(values_a) & np.isfinite(values_b)
    wavelengths = wavelengths[mask]
    values_a = values_a[mask]
    values_b = values_b[mask]
    if wavelengths.size == 0:
        return None, None, None
    return wavelengths, values_a, values_b


def apply_normalization(values: np.ndarray, mode: str) -> np.ndarray:
    if values.size == 0:
        return values
    mode = (mode or "none").lower()
    if mode in {"unit", "l2"}:
        norm = float(np.linalg.norm(values))
        if norm > 0:
            return values / norm
        return values
    if mode in {"max", "peak"}:
        peak = float(np.max(np.abs(values)))
        if peak > 0:
            return values / peak
        return values
    if mode in {"zscore", "z", "standard"}:
        mean = float(np.mean(values))
        std = float(np.std(values))
        if std > 0:
            return (values - mean) / std
        return values - mean
    return values


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return float("nan")
    value = float(np.dot(a, b) / denom)
    return max(min(value, 1.0), -1.0)


def _rmse(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean((a - b) ** 2)))


def _xcorr(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0:
        return float("nan")
    a_zero = a - np.mean(a)
    b_zero = b - np.mean(b)
    denom = float(np.linalg.norm(a_zero) * np.linalg.norm(b_zero))
    if denom == 0:
        return float("nan")
    value = float(np.dot(a_zero, b_zero) / denom)
    return max(min(value, 1.0), -1.0)


def _line_match(axis: np.ndarray, a: np.ndarray, b: np.ndarray, top_n: int) -> float:
    if axis.size == 0 or top_n <= 0:
        return float("nan")
    k = min(top_n, axis.size)
    idx_a = np.argsort(np.abs(a))[-k:]
    idx_b = np.argsort(np.abs(b))[-k:]
    peaks_a = axis[idx_a]
    peaks_b = axis[idx_b]
    if peaks_a.size == 0 or peaks_b.size == 0:
        return float("nan")
    span = float(axis.max() - axis.min()) or 1.0
    distances: List[float] = []
    for value in peaks_a:
        distances.append(float(np.min(np.abs(peaks_b - value))))
    for value in peaks_b:
        distances.append(float(np.min(np.abs(peaks_a - value))))
    if not distances:
        return float("nan")
    mean_distance = float(np.mean(distances))
    score = 1.0 - min(1.0, mean_distance / span)
    return max(min(score, 1.0), 0.0)


def _compute_metrics(
    trace_a: TraceVectors,
    trace_b: TraceVectors,
    viewport: Viewport,
    options: SimilarityOptions,
) -> Dict[str, float]:
    axis, values_a, values_b = _prepare_vectors(trace_a, trace_b, viewport)
    result: Dict[str, float] = {metric: float("nan") for metric in options.metrics}
    if axis is None or values_a is None or values_b is None:
        result["points"] = 0.0
        return result

    norm_a = apply_normalization(values_a, options.normalization)
    norm_b = apply_normalization(values_b, options.normalization)
    for metric in options.metrics:
        if metric == "cosine":
            result[metric] = _cosine_similarity(norm_a, norm_b)
        elif metric == "rmse":
            result[metric] = _rmse(norm_a, norm_b)
        elif metric in {"xcorr", "corr", "correlation"}:
            result[metric] = _xcorr(norm_a, norm_b)
        elif metric in {"line_match", "lines"}:
            result[metric] = _line_match(axis, norm_a, norm_b, options.line_match_top_n)
        else:
            # Unknown metric: leave NaN but keep key predictable
            result.setdefault(metric, float("nan"))
    result["points"] = float(axis.size)
    return result


def build_metric_frames(
    traces: Sequence[TraceVectors],
    viewport: Viewport,
    options: SimilarityOptions,
    cache: SimilarityCache,
) -> Dict[str, pd.DataFrame]:
    if len(traces) < 2:
        return {}
    labels = [trace.label for trace in traces]
    frames: Dict[str, pd.DataFrame] = {}
    for metric in options.metrics:
        diag_value = 1.0 if metric != "rmse" else 0.0
        frames[metric] = pd.DataFrame(
            diag_value,
            index=labels,
            columns=labels,
            dtype=float,
        )
    for i, trace_a in enumerate(traces):
        for j in range(i + 1, len(traces)):
            trace_b = traces[j]
            metrics = cache.compute(trace_a, trace_b, viewport, options)
            for metric in options.metrics:
                value = metrics.get(metric, float("nan"))
                frames[metric].iat[i, j] = value
                frames[metric].iat[j, i] = value
    return frames


def viewport_alignment(
    trace_a: TraceVectors,
    trace_b: TraceVectors,
    viewport: Viewport,
) -> Tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    return _prepare_vectors(trace_a, trace_b, viewport)
