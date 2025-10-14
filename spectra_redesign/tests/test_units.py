"""Unit tests for the UnitsService."""

import numpy as np
import pytest

from app.services.units_service import UnitsService
from app.services.spectrum import Spectrum


def test_wavelength_conversion_nm_to_cm_inv():
    service = UnitsService()
    # create a dummy spectrum with nm units
    x = np.array([500.0, 1000.0])
    y = np.array([0.1, 0.2])
    spec = Spectrum(x=x, y=y, x_unit="nm", y_unit="absorbance")
    new_x, new_y, metadata = service.convert(spec, "cm^-1", "absorbance")
    # 1/cm values: 1e7/nm
    expected = np.array([1e7/500.0, 1e7/1000.0])
    assert np.allclose(new_x, expected)
    # y should be unchanged
    assert np.allclose(new_y, y)
    assert metadata["x_conversion"] == "nm→cm^-1"


def test_intensity_conversion_absorbance_transmittance():
    service = UnitsService()
    x = np.array([500.0])
    y = np.array([1.0])  # A = 1
    spec = Spectrum(x=x, y=y, x_unit="nm", y_unit="absorbance")
    # A=1 corresponds to T=10^-1 = 0.1
    new_x, new_y, metadata = service.convert(spec, "nm", "transmittance")
    assert np.allclose(new_y, np.array([0.1]))
    assert metadata["y_conversion"] == "absorbance→transmittance"
    # Convert back
    spec2 = Spectrum(x=new_x, y=new_y, x_unit="nm", y_unit="transmittance")
    new_x2, new_y2, metadata2 = service.convert(spec2, "nm", "absorbance")
    assert np.allclose(new_y2, y)


def test_no_conversion_returns_copy():
    service = UnitsService()
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([0.1, 0.2, 0.3])
    spec = Spectrum(x=x, y=y)
    new_x, new_y, metadata = service.convert(spec, "nm", "absorbance")
    assert np.allclose(new_x, x)
    assert np.allclose(new_y, y)
    # metadata should be empty dict
    assert metadata == {}