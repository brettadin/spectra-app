"""Regression tests for FTIR overlay helpers."""

from __future__ import annotations

import numpy as np

from app.ui.ir_group_overlays import FUNCTIONAL_GROUP_RANGES, shaded_ranges_for_predictions
from ml import FunctionalGroupPrediction


def _gaussian(center: float, sigma: float, wavenumbers: np.ndarray, scale: float) -> np.ndarray:
    return scale * np.exp(-0.5 * ((wavenumbers - center) / sigma) ** 2)


def test_shaded_ranges_prioritise_high_intensity_peaks() -> None:
    wavenumbers = np.linspace(4000.0, 400.0, 2000)
    intensities = (
        _gaussian(3300.0, 35.0, wavenumbers, 0.9)
        + _gaussian(1720.0, 28.0, wavenumbers, 0.75)
        + 0.02 * np.random.RandomState(0).randn(wavenumbers.size)
    )

    predictions = [
        FunctionalGroupPrediction("Alcohol", 0.92, 0.30, True),
        FunctionalGroupPrediction("Aldehyde", 0.86, 0.28, True),
        FunctionalGroupPrediction("Alkyne", 0.55, 0.22, True),
    ]

    ranges = shaded_ranges_for_predictions(
        predictions,
        wavenumbers=wavenumbers,
        intensities=intensities,
        top_ranges=5,
    )

    assert ranges

    ranked = sorted(ranges, key=lambda entry: entry.score or 0.0, reverse=True)
    top_groups = [entry.group for entry in ranked[:2]]
    assert top_groups[0] == "Alcohol"
    assert top_groups[1] == "Aldehyde"

    for entry in ranges:
        assert entry.peak_fraction is not None and entry.peak_fraction > 0
        assert entry.score is not None and entry.score >= 0
        assert entry.high_cm_1 > entry.low_cm_1
        origin = next(
            band for band in FUNCTIONAL_GROUP_RANGES[entry.group] if band.band == entry.band
        )
        assert origin.high_cm_1 >= entry.high_cm_1 >= entry.low_cm_1 >= origin.low_cm_1


def test_shaded_ranges_trim_when_spectrum_absent() -> None:
    predictions = [
        FunctionalGroupPrediction("Alcohol", 0.9, 0.3, True),
        FunctionalGroupPrediction("Aldehyde", 0.8, 0.25, True),
        FunctionalGroupPrediction("Amine", 0.7, 0.2, True),
        FunctionalGroupPrediction("Amide", 0.6, 0.2, True),
    ]

    ranges = shaded_ranges_for_predictions(predictions, top_ranges=3)
    assert len(ranges) <= 3

    probabilities = [entry.probability for entry in ranges]
    assert probabilities == sorted(probabilities, reverse=True)
