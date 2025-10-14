import numpy as np
import streamlit as st

from app.ui.main import OverlayTrace, _trace_ir_vectors


def test_trace_ir_vectors_converts_transmittance_to_absorbance():
    st.session_state.clear()
    wavelengths_cm_1 = np.linspace(2400.0, 2200.0, 5)
    wavelengths_nm = tuple(float(1e7 / value) for value in wavelengths_cm_1)
    transmittance = (0.92, 0.55, 0.12, 0.58, 0.95)

    trace = OverlayTrace(
        trace_id="trans",
        label="Transmittance",
        wavelength_nm=wavelengths_nm,
        flux=transmittance,
        metadata={
            "original_wavelength_unit": "cm^-1",
            "flux_unit_input": "Transmittance",
        },
        flux_unit="Transmittance",
        axis="transmission",
    )

    wavenumbers, intensities = _trace_ir_vectors(trace)

    assert np.all(np.isfinite(intensities))
    assert np.argmax(intensities) == 2  # strongest absorption becomes tallest peak
    assert float(intensities[2]) > float(intensities[0])


def test_trace_ir_vectors_inverts_negative_absorbance():
    st.session_state.clear()
    wavelengths_nm = (4000.0, 3500.0, 3000.0)
    absorbance = (-0.2, -0.5, -0.3)

    trace = OverlayTrace(
        trace_id="abs",
        label="Absorbance",
        wavelength_nm=wavelengths_nm,
        flux=absorbance,
        metadata={"flux_unit_input": "Absorbance"},
        flux_unit="Absorbance",
        axis="absorbance",
    )

    _, intensities = _trace_ir_vectors(trace)
    assert max(intensities) > 0
    assert min(intensities) >= 0
