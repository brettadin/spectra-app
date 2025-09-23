"""Downsampling utilities for dense spectral traces."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

import numpy as np

__all__ = [
    "DownsampleResult",
    "build_lttb_downsample",
    "build_minmax_envelope",
    "build_downsample_tiers",
]


@dataclass(frozen=True)
class DownsampleResult:
    """Container describing a downsampled spectrum."""

    wavelength_nm: Tuple[float, ...]
    flux: Tuple[float, ...]

    @property
    def points(self) -> int:
        return len(self.wavelength_nm)


def _as_float_array(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError("Downsampling requires 1-D sequences")
    mask = np.isfinite(array)
    if not np.all(mask):
        array = array[mask]
    return array.astype(float, copy=False)


def _ensure_sorted_unique(
    wavelength_nm: Sequence[float], flux: Sequence[float]
) -> Tuple[np.ndarray, np.ndarray]:
    x = _as_float_array(wavelength_nm)
    y = _as_float_array(flux)
    if x.size != y.size:
        raise ValueError("Wavelength and flux sequences must be equal length")
    if x.size == 0:
        return x, y
    order = np.argsort(x, kind="mergesort")
    x = x[order]
    y = y[order]
    x, unique_idx = np.unique(x, return_index=True)
    y = y[unique_idx]
    return x, y


def build_lttb_downsample(
    wavelength_nm: Sequence[float], flux: Sequence[float], target_points: int
) -> DownsampleResult:
    """Return a Largest-Triangle-Three-Buckets downsample of ``target_points``."""

    x, y = _ensure_sorted_unique(wavelength_nm, flux)
    n = int(target_points)
    if n <= 0:
        raise ValueError("target_points must be positive")
    if x.size <= n:
        return DownsampleResult(tuple(x.tolist()), tuple(y.tolist()))
    if n == 1:
        return DownsampleResult((float(x[len(x) // 2]),), (float(y[len(y) // 2]),))

    bucket_size = (x.size - 2) / float(n - 2)

    sampled_x: List[float] = [float(x[0])]
    sampled_y: List[float] = [float(y[0])]

    a_idx = 0
    for i in range(n - 2):
        range_start = int(math.floor((i + 0) * bucket_size)) + 1
        range_end = int(math.floor((i + 1) * bucket_size)) + 1
        range_end = min(range_end, x.size - 1)
        if range_end <= range_start:
            range_end = range_start + 1
        range_end = min(range_end, x.size)

        avg_start = int(math.floor((i + 1) * bucket_size)) + 1
        avg_end = int(math.floor((i + 2) * bucket_size)) + 1
        avg_end = min(avg_end, x.size)
        if avg_end <= avg_start:
            avg_start = max(avg_start - 1, 1)
            avg_end = min(avg_start + 1, x.size)
        avg_x = float(np.mean(x[avg_start:avg_end])) if avg_end > avg_start else float(x[avg_start - 1])
        avg_y = float(np.mean(y[avg_start:avg_end])) if avg_end > avg_start else float(y[avg_start - 1])

        segment_x = x[range_start:range_end]
        segment_y = y[range_start:range_end]

        if segment_x.size == 0:
            break

        area = np.abs(
            (x[a_idx] - segment_x) * (segment_y - avg_y)
            - (y[a_idx] - segment_y) * (segment_x - avg_x)
        )
        chosen_relative = int(np.argmax(area))
        chosen = range_start + chosen_relative
        sampled_x.append(float(x[chosen]))
        sampled_y.append(float(y[chosen]))
        a_idx = chosen

    sampled_x.append(float(x[-1]))
    sampled_y.append(float(y[-1]))

    return DownsampleResult(tuple(sampled_x), tuple(sampled_y))


def build_minmax_envelope(
    wavelength_nm: Sequence[float],
    flux: Sequence[float],
    target_points: int,
) -> DownsampleResult:
    """Return a min/max envelope downsampled to ``target_points`` samples."""

    x, y = _ensure_sorted_unique(wavelength_nm, flux)
    n = int(target_points)
    if n <= 0:
        raise ValueError("target_points must be positive")
    if x.size <= n:
        return DownsampleResult(tuple(x.tolist()), tuple(y.tolist()))

    bucket_count = max(1, n // 2)
    bucket_width = max(1, int(math.ceil(x.size / bucket_count)))

    sampled_indices: List[int] = [0]
    for start in range(0, x.size, bucket_width):
        end = min(start + bucket_width, x.size)
        segment = slice(start, end)
        seg_x = x[segment]
        seg_y = y[segment]
        if seg_x.size == 0:
            continue
        local_min = int(np.argmin(seg_y)) + start
        local_max = int(np.argmax(seg_y)) + start
        sampled_indices.extend(sorted({local_min, local_max}))
    sampled_indices.append(x.size - 1)

    indices = np.unique(np.asarray(sampled_indices, dtype=int))
    return DownsampleResult(tuple(x[indices].tolist()), tuple(y[indices].tolist()))


def build_downsample_tiers(
    wavelength_nm: Sequence[float],
    flux: Sequence[float],
    tiers: Sequence[int] = (500, 2000, 8000),
    *,
    strategy: str = "hybrid",
) -> Mapping[int, DownsampleResult]:
    """Return downsampled representations for the requested ``tiers``."""

    if not tiers:
        return {}
    x, y = _ensure_sorted_unique(wavelength_nm, flux)
    results: Dict[int, DownsampleResult] = {}
    for tier in sorted({int(value) for value in tiers if int(value) > 0}):
        if strategy == "minmax":
            result = build_minmax_envelope(x, y, tier)
        elif strategy == "lttb":
            result = build_lttb_downsample(x, y, tier)
        else:
            # Hybrid: use an envelope for coarse tiers, LTTB otherwise
            if tier <= 2000:
                result = build_minmax_envelope(x, y, tier)
            else:
                result = build_lttb_downsample(x, y, tier)
        results[tier] = result
    return results

