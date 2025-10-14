"""IR functional-group classifier integration."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import gzip
import json
import math
import pickle
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, Sequence, Tuple, Union, List

import numpy as np

try:  # Optional dependency used for baseline correction
    from scipy.signal import savgol_filter  # type: ignore
except Exception:  # pragma: no cover - SciPy unavailable in constrained envs
    savgol_filter = None  # type: ignore


from .ir_group_data import (
    LABEL_NAMES_EXTENDED,
    CORRELATION_BANDS,
    FALLBACK_THRESHOLDS,
)

Number = Union[int, float, np.floating]
VectorLike = Union[Sequence[Number], np.ndarray]
SpectrumInput = Union[
    Mapping[str, Union[VectorLike, Number]],
    Tuple[VectorLike, VectorLike],
    List[Tuple[Number, Number]],
    np.ndarray,
]


@dataclass(frozen=True)
class FunctionalGroupPrediction:
    """Container describing a model prediction for a functional group."""

    name: str
    probability: float
    threshold: float
    present: bool

    def to_dict(self) -> Mapping[str, object]:
        """Return a serialisable representation."""

        return {
            "name": self.name,
            "probability": float(self.probability),
            "threshold": float(self.threshold),
            "present": bool(self.present),
        }


class _FallbackIRModel:
    """Rule-based approximation when the TensorFlow model is unavailable."""

    def __init__(self, label_names: Sequence[str]) -> None:
        self._label_names: Tuple[str, ...] = tuple(label_names)
        self._grid = np.linspace(4000.0, 400.0, 600)

    def predict(self, data: np.ndarray, verbose: int = 0) -> np.ndarray:  # pragma: no cover - simple wrapper
        batch = np.asarray(data, dtype=float)
        if batch.ndim == 1:
            batch = batch.reshape(1, batch.size)
        elif batch.ndim == 3:
            batch = batch.reshape(batch.shape[0], batch.shape[1])
        scores = np.zeros((batch.shape[0], len(self._label_names)), dtype=np.float32)
        for row_index, row in enumerate(batch):
            finite = row[np.isfinite(row)]
            if finite.size == 0:
                continue
            minimum = float(np.min(finite))
            maximum = float(np.max(finite))
            if math.isclose(maximum, minimum):
                normalised = np.zeros_like(row, dtype=float)
            else:
                normalised = (row - minimum) / (maximum - minimum)
            for label_index, name in enumerate(self._label_names):
                bands = CORRELATION_BANDS.get(name)
                if not bands:
                    continue
                responses: List[float] = []
                for high, low, _band_name, _notes in bands:
                    mask = (self._grid <= float(high)) & (self._grid >= float(low))
                    if not mask.any():
                        continue
                    band_values = normalised[mask]
                    if band_values.size == 0:
                        continue
                    responses.append(float(np.nanmax(band_values)))
                if responses:
                    scores[row_index, label_index] = min(1.0, max(responses))
        return scores


class _LinearIRModel:
    """Lightweight linear model stored in HDF5 when TensorFlow weights are unavailable."""

    def __init__(self, weights: np.ndarray, bias: np.ndarray) -> None:
        self._weights = np.asarray(weights, dtype=np.float32)
        self._bias = np.asarray(bias, dtype=np.float32)

    def predict(self, data: np.ndarray, verbose: int = 0) -> np.ndarray:  # pragma: no cover - simple wrapper
        batch = np.asarray(data, dtype=np.float32)
        if batch.ndim == 1:
            batch = batch.reshape(1, batch.size)
        elif batch.ndim == 3:
            batch = batch.reshape(batch.shape[0], batch.shape[1])
        normalised = np.zeros_like(batch)
        for index, row in enumerate(batch):
            finite = row[np.isfinite(row)]
            if finite.size == 0:
                continue
            minimum = float(np.min(finite))
            maximum = float(np.max(finite))
            if math.isclose(maximum, minimum):
                continue
            normalised[index] = (row - minimum) / (maximum - minimum)
        logits = normalised @ self._weights.T + self._bias
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        return probabilities


class IRGroupClassifier:
    """Interface to the IR functional-group classifier."""

    DEFAULT_MODEL_PATH = Path("ml_models/ir_groups/0_model_extended.h5")
    DEFAULT_THRESHOLDS_PATH = Path("ml_models/ir_groups/optimal_thresholds.pkl")
    DEFAULT_THRESHOLDS_JSON_PATH = Path("ml_models/ir_groups/optimal_thresholds.json")
    DEFAULT_LINEAR_BUNDLE_PATH = Path(
        "ml_models/ir_groups/linear_surrogate.json.gz.b64"
    )

    def __init__(
        self,
        *,
        model: Optional[object] = None,
        model_path: Optional[Union[str, Path]] = None,
        thresholds: Optional[Mapping[int, float]] = None,
        thresholds_path: Optional[Union[str, Path]] = None,
        surrogate_bundle_path: Optional[Union[str, Path]] = None,
        label_names: Optional[Sequence[str]] = None,
        baseline_window: int = 51,
        baseline_poly_order: int = 3,
        normalise: bool = True,
    ) -> None:
        self._model = model
        self._model_path = Path(model_path) if model_path else self.DEFAULT_MODEL_PATH
        self._thresholds: MutableMapping[int, float] = dict(thresholds or {})
        self._thresholds_path = (
            Path(thresholds_path) if thresholds_path else self.DEFAULT_THRESHOLDS_PATH
        )
        self._thresholds_json_path = (
            Path(thresholds_path)
            if thresholds_path and str(thresholds_path).endswith(".json")
            else self.DEFAULT_THRESHOLDS_JSON_PATH
        )
        self._surrogate_bundle_path = (
            Path(surrogate_bundle_path)
            if surrogate_bundle_path
            else self.DEFAULT_LINEAR_BUNDLE_PATH
        )
        self._label_names: Tuple[str, ...] = (
            tuple(label_names) if label_names else LABEL_NAMES_EXTENDED
        )
        self._baseline_window = max(3, int(baseline_window))
        self._baseline_poly = max(1, int(baseline_poly_order))
        self._normalise = bool(normalise)
        self._backend_name = "provided" if model is not None else "uninitialised"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict_groups(
        self,
        spectrum: SpectrumInput,
    ) -> List[FunctionalGroupPrediction]:
        """Return functional-group predictions for the provided spectrum."""

        wavenumbers, intensities = self._coerce_spectrum(spectrum)
        processed = self._preprocess(wavenumbers, intensities)
        model = self._ensure_model()
        raw = model.predict(processed, verbose=0)  # type: ignore[attr-defined]
        probabilities = np.asarray(raw, dtype=np.float64).ravel()
        thresholds = self._ensure_thresholds()

        results: List[FunctionalGroupPrediction] = []
        for index, name in enumerate(self._label_names):
            prob = float(probabilities[index]) if index < probabilities.size else 0.0
            threshold = float(thresholds.get(index, 0.5))
            present = prob >= threshold
            results.append(
                FunctionalGroupPrediction(
                    name=name,
                    probability=prob,
                    threshold=threshold,
                    present=present,
                )
            )
        results.sort(key=lambda item: item.probability, reverse=True)
        return results

    @property
    def backend_name(self) -> str:
        """Return the backend used for inference (tensorflow/heuristic/provided)."""

        return self._backend_name

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_model(self) -> object:
        if self._model is not None:
            return self._model
        model_path = self._model_path.expanduser()
        if not model_path.exists():
            bundle_model = self._load_linear_bundle()
            if bundle_model is not None:
                self._model = bundle_model
                self._backend_name = "linear"
                return self._model
            return self._fallback_model()

        keras_model = self._load_keras_model(model_path)
        if keras_model is not None:
            self._model = keras_model
            self._backend_name = "tensorflow"
            return self._model

        linear_model = self._load_linear_model(model_path)
        if linear_model is not None:
            self._model = linear_model
            self._backend_name = "linear"
            return self._model

        bundle_model = self._load_linear_bundle()
        if bundle_model is not None:
            self._model = bundle_model
            self._backend_name = "linear"
            return self._model

        return self._fallback_model()

    def _fallback_model(self) -> object:
        self._model = _FallbackIRModel(self._label_names)
        self._backend_name = "heuristic"
        return self._model

    @staticmethod
    def _load_keras_model(path: Path) -> Optional[object]:
        try:
            from tensorflow import keras  # type: ignore
        except Exception:  # pragma: no cover - TensorFlow missing in constrained envs
            return None
        try:
            return keras.models.load_model(path)
        except Exception:  # pragma: no cover - propagate fallback when load fails
            return None

    def _load_linear_model(self, path: Path) -> Optional[_LinearIRModel]:
        try:
            import h5py  # type: ignore
        except Exception:  # pragma: no cover - h5py unavailable in constrained envs
            return None
        try:
            with h5py.File(path, "r") as handle:
                if "linear" not in handle:
                    return None
                group = handle["linear"]
                if "weights" not in group or "bias" not in group:
                    return None
                weights = np.asarray(group["weights"], dtype=np.float32)
                bias = np.asarray(group["bias"], dtype=np.float32)
        except Exception:
            return None
        if weights.shape[0] != len(self._label_names):
            return None
        return _LinearIRModel(weights, bias)

    def _load_linear_bundle(self) -> Optional[_LinearIRModel]:
        path = self._surrogate_bundle_path.expanduser()
        if not path.exists():
            return None
        try:
            encoded = path.read_text().encode("ascii")
            payload = gzip.decompress(base64.b64decode(encoded))
            data = json.loads(payload.decode("utf-8"))
        except Exception:
            return None
        weights = np.asarray(data.get("weights"), dtype=np.float32)
        bias = np.asarray(data.get("bias"), dtype=np.float32)
        if weights.shape != (len(self._label_names), 600):
            return None
        if bias.shape != (len(self._label_names),):
            return None
        return _LinearIRModel(weights, bias)

    def _ensure_thresholds(self) -> Mapping[int, float]:
        if self._thresholds:
            return self._thresholds
        loaded = None
        path = self._thresholds_path.expanduser()
        if path.exists():
            try:
                with path.open("rb") as handle:
                    loaded = pickle.load(handle)
            except Exception:
                loaded = None
        if loaded is None:
            json_path = self._thresholds_json_path.expanduser()
            if json_path.exists():
                try:
                    loaded = json.loads(json_path.read_text())
                except Exception:
                    loaded = None
        if loaded is None:
            self._thresholds = self._fallback_thresholds()
            return self._thresholds
        if isinstance(loaded, Mapping):
            thresholds = {int(k): float(v) for k, v in loaded.items()}
        elif isinstance(loaded, Sequence):
            thresholds = {index: float(value) for index, value in enumerate(loaded)}
        else:
            thresholds = {}
        if not thresholds:
            thresholds = self._fallback_thresholds()
        else:
            for index, name in enumerate(self._label_names):
                thresholds.setdefault(index, float(FALLBACK_THRESHOLDS.get(name, 0.35)))
        self._thresholds = thresholds
        return self._thresholds

    def _fallback_thresholds(self) -> MutableMapping[int, float]:
        """Return heuristic probability thresholds for each functional group."""

        return {
            index: float(FALLBACK_THRESHOLDS.get(name, 0.35))
            for index, name in enumerate(self._label_names)
        }

    @staticmethod
    def _as_array(values: VectorLike) -> np.ndarray:
        return np.asarray(values, dtype=float)

    def _coerce_spectrum(
        self, spectrum: SpectrumInput
    ) -> Tuple[np.ndarray, np.ndarray]:
        if isinstance(spectrum, Mapping):
            lower = {str(k).lower(): v for k, v in spectrum.items()}
            wav = None
            for key in ("wavenumbers", "wavenumber", "wavenumber_cm_1", "cm^-1", "cm_1"):
                if key in lower:
                    wav = self._as_array(lower[key])
                    break
            intensities = None
            for key in (
                "intensity",
                "intensities",
                "absorbance",
                "transmittance",
                "flux",
                "y",
            ):
                if key in lower:
                    intensities = self._as_array(lower[key])
                    break
            if wav is None and "wavelengths" in lower:
                wav = self._wavelength_nm_to_wavenumber(lower.get("wavelengths"))
            if wav is None:
                raise ValueError("Spectrum mapping must include wavenumber or wavelength data")
            if intensities is None:
                raise ValueError("Spectrum mapping must include intensity data")
            return wav, intensities

        if isinstance(spectrum, (tuple, list)):
            if len(spectrum) == 2 and all(
                isinstance(component, (Sequence, np.ndarray)) for component in spectrum
            ):
                return (
                    self._as_array(spectrum[0]),
                    self._as_array(spectrum[1]),
                )

        arr = np.asarray(spectrum, dtype=float)
        if arr.ndim == 2 and arr.shape[1] >= 2:
            return (
                self._as_array(arr[:, 0]),
                self._as_array(arr[:, 1]),
            )
        raise ValueError("Unable to coerce spectrum into (wavenumbers, intensities)")

    @staticmethod
    def _wavelength_nm_to_wavenumber(values: Optional[VectorLike]) -> np.ndarray:
        if values is None:
            raise ValueError("Wavelength data not provided")
        arr = np.asarray(values, dtype=float)
        safe = np.where(arr > 0, arr, np.nan)
        return 1e7 / safe

    def _preprocess(
        self,
        wavenumbers: np.ndarray,
        intensities: np.ndarray,
    ) -> np.ndarray:
        if wavenumbers.size == 0:
            raise ValueError("Empty wavenumber array")
        if intensities.size == 0:
            raise ValueError("Empty intensity array")
        if wavenumbers.size != intensities.size:
            raise ValueError("Wavenumber and intensity arrays must be the same length")

        order = np.argsort(wavenumbers)[::-1]  # descending order
        sorted_wn = np.asarray(wavenumbers, dtype=float)[order]
        sorted_intensity = np.asarray(intensities, dtype=float)[order]
        mask = np.isfinite(sorted_wn) & np.isfinite(sorted_intensity)
        sorted_wn = sorted_wn[mask]
        sorted_intensity = sorted_intensity[mask]
        if sorted_wn.size == 0 or sorted_intensity.size == 0:
            raise ValueError("Spectrum contains no finite values after cleaning")

        target_desc = np.linspace(4000.0, 400.0, 600)
        target_asc = target_desc[::-1]
        interp_x = np.asarray(sorted_wn[::-1], dtype=float)
        interp_y = np.asarray(sorted_intensity[::-1], dtype=float)
        resampled_asc = np.interp(
            target_asc,
            interp_x,
            interp_y,
            left=float(interp_y[0]),
            right=float(interp_y[-1]),
        )
        resampled = resampled_asc[::-1]

        processed = resampled.astype(np.float64)
        if self._normalise:
            processed = self._apply_baseline(processed)
            processed = self._scale_unit_interval(processed)
        processed = processed.reshape(1, processed.size, 1).astype(np.float32)
        return processed

    def _apply_baseline(self, values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=float)
        if savgol_filter is not None and arr.size > self._baseline_poly:
            window = min(self._baseline_window, arr.size if arr.size % 2 == 1 else arr.size - 1)
            window = max(window, self._baseline_poly + 2)
            if window % 2 == 0:
                window += 1
            if window > arr.size:
                window = arr.size if arr.size % 2 == 1 else arr.size - 1
            try:
                baseline = savgol_filter(arr, window_length=window, polyorder=self._baseline_poly)
            except Exception:
                baseline = np.nanmin(arr)
        else:
            baseline = np.nanmin(arr)
        corrected = arr - baseline
        return corrected

    @staticmethod
    def _scale_unit_interval(values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=float)
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            return np.zeros_like(arr)
        minimum = float(np.min(finite))
        maximum = float(np.max(finite))
        if math.isclose(maximum, minimum):
            return np.zeros_like(arr)
        scaled = (arr - minimum) / (maximum - minimum)
        return scaled


__all__ = ["IRGroupClassifier", "FunctionalGroupPrediction"]
