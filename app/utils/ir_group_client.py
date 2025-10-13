"""Client helper for IR functional-group classification."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterable, Sequence

import requests

from ml import FunctionalGroupPrediction, IRGroupClassifier

_API_URL_ENV = "SPECTRA_IR_GROUP_API_URL"
_ENDPOINT = "/api/ir-groups"
_LAST_BACKEND = "uninitialised"


@lru_cache(maxsize=4)
def _classifier(normalise: bool = True) -> IRGroupClassifier:
    return IRGroupClassifier(normalise=normalise)


def _call_remote(
    base_url: str,
    wavenumbers: Sequence[float],
    intensities: Sequence[float],
    *,
    normalise: bool,
) -> Sequence[FunctionalGroupPrediction] | None:
    url = base_url.rstrip("/") + _ENDPOINT
    try:
        response = requests.post(
            url,
            json={
                "wavenumber_cm_1": list(float(v) for v in wavenumbers),
                "intensity": list(float(v) for v in intensities),
                "normalise": normalise,
            },
            timeout=20,
        )
        response.raise_for_status()
    except Exception:
        return None
    data = response.json()
    predictions = []
    for item in data.get("predictions", []):
        try:
            predictions.append(
                FunctionalGroupPrediction(
                    name=str(item.get("name", "")),
                    probability=float(item.get("probability", 0.0)),
                    threshold=float(item.get("threshold", 0.0)),
                    present=bool(item.get("present", False)),
                )
            )
        except Exception:
            continue
    global _LAST_BACKEND
    _LAST_BACKEND = str(data.get("backend", "remote"))
    return predictions


def identify_functional_groups(
    *,
    wavenumbers: Iterable[float],
    intensities: Iterable[float],
    normalise: bool = True,
) -> Sequence[FunctionalGroupPrediction]:
    """Return functional-group predictions using the configured backend."""

    wn = list(float(v) for v in wavenumbers)
    it = list(float(v) for v in intensities)
    if len(wn) != len(it):
        raise ValueError("Wavenumber and intensity arrays must match in length")

    global _LAST_BACKEND
    base_url = os.environ.get(_API_URL_ENV)
    if base_url:
        remote = _call_remote(base_url, wn, it, normalise=normalise)
        if remote is not None:
            return remote

    classifier = _classifier(normalise)
    predictions = classifier.predict_groups({"wavenumber": wn, "intensity": it})
    _LAST_BACKEND = getattr(classifier, "backend_name", "local")
    return predictions


def ir_group_backend() -> str:
    """Return the backend used for the most recent IR classification."""

    return _LAST_BACKEND


__all__ = ["identify_functional_groups", "ir_group_backend"]
