import numpy as np
import pytest
from pathlib import Path

from ml.ir_group_classifier import IRGroupClassifier
from ml.ir_group_data import LABEL_NAMES_EXTENDED


class DummyModel:
    def __init__(self, values):
        self.values = np.asarray([values], dtype=np.float32)
        self.calls = 0

    def predict(self, data, verbose=0):
        self.calls += 1
        self.last_input_shape = data.shape
        return self.values


def test_preprocess_shapes_resample():
    classifier = IRGroupClassifier(
        model=DummyModel(np.zeros(37)),
        thresholds={index: 0.5 for index in range(37)},
    )
    wavenumbers = np.linspace(4000, 400, 1200)
    intensities = np.sin(np.linspace(0, np.pi, 1200))
    processed = classifier._preprocess(wavenumbers, intensities)
    assert processed.shape == (1, 600, 1)
    assert np.isfinite(processed).all()


def test_predict_groups_applies_thresholds_sorted():
    probabilities = np.array([
        0.1,
        0.9,
        0.2,
        0.8,
        *(0.0 for _ in range(33)),
    ])
    thresholds = {index: 0.5 for index in range(len(probabilities))}
    model = DummyModel(probabilities)
    classifier = IRGroupClassifier(
        model=model,
        thresholds=thresholds,
        label_names=[f"Label {i}" for i in range(len(probabilities))],
    )
    wn = np.linspace(4000, 400, 600)
    intensities = np.linspace(0.0, 1.0, 600)
    results = classifier.predict_groups((wn, intensities))
    assert model.calls == 1
    assert results[0].name == "Label 1"
    assert results[0].present is True
    assert results[1].name == "Label 3"
    assert results[1].present is True
    assert all(0.0 <= item.probability <= 1.0 for item in results)


def test_coerce_from_wavelength_mapping():
    classifier = IRGroupClassifier(
        model=DummyModel(np.zeros(37)),
        thresholds={index: 0.5 for index in range(37)},
    )
    spectrum = {
        "wavelengths": np.linspace(2500, 250, 600),
        "intensity": np.linspace(0, 1, 600),
    }
    wavenumbers, intensities = classifier._coerce_spectrum(spectrum)
    assert wavenumbers.shape == intensities.shape
    assert np.all(wavenumbers > 0)


def test_fallback_model_detects_carbonyl_peak(tmp_path):
    model_path = tmp_path / "missing_model.h5"
    thresholds_path = tmp_path / "missing_thresholds.pkl"
    classifier = IRGroupClassifier(
        model_path=model_path,
        thresholds_path=thresholds_path,
        surrogate_bundle_path=tmp_path / "missing_bundle.b64",
        normalise=True,
    )
    wavenumbers = np.linspace(4000, 400, 600)
    intensities = np.zeros_like(wavenumbers)
    mask = (wavenumbers <= 1750) & (wavenumbers >= 1680)
    intensities[mask] = 1.0
    results = classifier.predict_groups((wavenumbers, intensities))
    lookup = {item.name: item for item in results}
    assert lookup["Ketone"].present is True
    assert classifier.backend_name == "heuristic"


def test_linear_model_loaded_from_hdf5(tmp_path):
    try:
        import h5py  # type: ignore
    except Exception:  # pragma: no cover - h5py missing
        pytest.skip("h5py not available")

    model_path = tmp_path / "linear_model.h5"
    with h5py.File(model_path, "w") as handle:
        handle.attrs["model_type"] = "linear"
        group = handle.create_group("linear")
        weights = np.zeros((len(LABEL_NAMES_EXTENDED), 600), dtype=np.float32)
        weights[:, :10] = 0.5
        bias = np.full(len(LABEL_NAMES_EXTENDED), -0.75, dtype=np.float32)
        group.create_dataset("weights", data=weights)
        group.create_dataset("bias", data=bias)

    classifier = IRGroupClassifier(model_path=model_path)
    wn = np.linspace(4000, 400, 600)
    intensities = np.ones_like(wn)
    results = classifier.predict_groups((wn, intensities))
    assert classifier.backend_name == "linear"
    assert len(results) == len(LABEL_NAMES_EXTENDED)
    assert all(0.0 <= item.probability <= 1.0 for item in results)


def test_linear_model_loaded_from_bundle(tmp_path):
    bundle_path = tmp_path / "linear_surrogate.json.gz.b64"
    thresholds_path = tmp_path / "optimal_thresholds.json"
    bundle_path.write_text(Path("ml_models/ir_groups/linear_surrogate.json.gz.b64").read_text())
    thresholds_path.write_text(Path("ml_models/ir_groups/optimal_thresholds.json").read_text())

    classifier = IRGroupClassifier(
        model_path=tmp_path / "missing_model.h5",
        thresholds_path=thresholds_path,
        surrogate_bundle_path=bundle_path,
    )
    wn = np.linspace(4000, 400, 600)
    intensities = np.ones_like(wn)
    results = classifier.predict_groups((wn, intensities))

    assert classifier.backend_name == "linear"
    assert len(results) == len(LABEL_NAMES_EXTENDED)
