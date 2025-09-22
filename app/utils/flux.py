from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple

import numpy as np

__all__ = ["flux_percentile_range"]


def flux_percentile_range(
    wavelength_nm: Sequence[float] | np.ndarray,
    flux: Sequence[float] | np.ndarray,
    *,
    coverage: float = 0.99,
) -> Optional[Tuple[float, float]]:
    """Return the flux-weighted percentile wavelength bounds.

    The percentile window is calculated using the trapezoidal integral of the
    absolute flux and trimmed symmetrically until the requested coverage of the
    cumulative weight remains.
    """

    if not 0.0 < coverage < 1.0:
        coverage = 0.99

    wavelengths = np.asarray(wavelength_nm, dtype=float)
    flux_values = np.asarray(flux, dtype=float)
    mask = np.isfinite(wavelengths) & np.isfinite(flux_values)
    if mask.sum() < 2:
        return None

    wavelengths = wavelengths[mask]
    flux_values = np.abs(flux_values[mask])
    order = np.argsort(wavelengths)
    wavelengths = wavelengths[order]
    flux_values = flux_values[order]

    wavelengths, unique_idx = np.unique(wavelengths, return_index=True)
    flux_values = flux_values[unique_idx]
    if wavelengths.size < 2:
        return None

    baseline = wavelengths[0]
    shifted = wavelengths - baseline
    span = shifted[-1]
    if not math.isfinite(span) or span <= 0.0:
        return None

    scaled = shifted / span
    segment_weights = 0.5 * (flux_values[:-1] + flux_values[1:]) * np.diff(scaled)
    total_weight = float(segment_weights.sum())
    if not math.isfinite(total_weight) or total_weight <= 0.0:
        return None

    cumulative = np.concatenate([[0.0], np.cumsum(segment_weights)])
    lower_weight = max(0.0, (1.0 - coverage) / 2.0 * total_weight)
    upper_weight = min(total_weight, total_weight - lower_weight)

    lower_scaled = float(np.interp(lower_weight, cumulative, scaled))
    upper_scaled = float(np.interp(upper_weight, cumulative, scaled))

    low = baseline + lower_scaled * span
    high = baseline + upper_scaled * span
    if not (math.isfinite(low) and math.isfinite(high)):
        return None
    return (min(low, high), max(low, high))
