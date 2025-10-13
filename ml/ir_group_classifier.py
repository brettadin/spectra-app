"""IR functional-group classifier integration."""
from __future__ import annotations

from dataclasses import dataclass
import math
import pickle
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, Sequence, Tuple, Union, List

import numpy as np

try:  # Optional dependency used for baseline correction
    from scipy.signal import savgol_filter  # type: ignore
except Exception:  # pragma: no cover - SciPy unavailable in constrained envs
    savgol_filter = None  # type: ignore


Number = Union[int, float, np.floating]
VectorLike = Union[Sequence[Number], np.ndarray]
SpectrumInput = Union[
    Mapping[str, Union[VectorLike, Number]],
    Tuple[VectorLike, VectorLike],
    List[Tuple[Number, Number]],
    np.ndarray,
]


_LABEL_NAMES_EXTENDED: Tuple[str, ...] = (
    "Alkane",
    "Alkene",
    "Alkyne",
    "Arene",
    "Haloalkane",
    "Alcohol",
    "Aldehyde",
    "Ketone",
    "Carboxylic acid",
    "Acid anhydride",
    "Acyl halide",
    "Ester",
    "Ether",
    "Amine",
    "Amide",
    "Nitrile",
    "Imide",
    "Imine",
    "Azo compound",
    "Thiol",
    "Thial",
    "Sulfone",
    "Sulfonic acid",
    "Enol",
    "Phenol",
    "Hydrazine",
    "Enamine",
    "Isocyanate",
    "Isothiocyanate",
    "Phosphine",
    "Sulfonamide",
    "Sulfonate",
    "Sulfoxide",
    "Thioamide",
    "Hydrazone",
    "Carbamate",
    "Sulfide",
)


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


class IRGroupClassifier:
    """Interface to the IR functional-group classifier."""

    DEFAULT_MODEL_PATH = Path("ml_models/ir_groups/0_model_extended.h5")
    DEFAULT_THRESHOLDS_PATH = Path("ml_models/ir_groups/optimal_thresholds.pkl")

    def __init__(
        self,
        *,
        model: Optional[object] = None,
        model_path: Optional[Union[str, Path]] = None,
        thresholds: Optional[Mapping[int, float]] = None,
        thresholds_path: Optional[Union[str, Path]] = None,
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
        self._label_names: Tuple[str, ...] = (
            tuple(label_names) if label_names else _LABEL_NAMES_EXTENDED
        )
        self._baseline_window = max(3, int(baseline_window))
        self._baseline_poly = max(1, int(baseline_poly_order))
        self._normalise = bool(normalise)

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_model(self) -> object:
        if self._model is not None:
            return self._model
        try:
            from tensorflow import keras  # type: ignore
        except Exception as exc:  # pragma: no cover - TensorFlow missing in tests
            raise ImportError(
                "TensorFlow is required to load the IR functional-group model"
            ) from exc
        model_path = self._model_path.expanduser()
        if not model_path.exists():
            raise FileNotFoundError(
                f"IR functional-group model not found: {model_path}"
            )
        self._model = keras.models.load_model(model_path)
        return self._model

    def _ensure_thresholds(self) -> Mapping[int, float]:
        if self._thresholds:
            return self._thresholds
        path = self._thresholds_path.expanduser()
        if not path.exists():
            raise FileNotFoundError(
                f"IR functional-group thresholds not found: {path}"
            )
        with path.open("rb") as handle:
            loaded = pickle.load(handle)
        if isinstance(loaded, Mapping):
            self._thresholds = {int(k): float(v) for k, v in loaded.items()}
        else:
            raise ValueError("Threshold file does not contain a mapping")
        return self._thresholds

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
