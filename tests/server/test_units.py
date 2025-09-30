import sys
from pathlib import Path

import numpy as np
import pytest
from astropy import units as u

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.server.units import canonical_unit, to_nm


@pytest.mark.parametrize(
    "raw_unit, values, expected, canonical",
    [
        (" NM", [1.0, 2.0], [1.0, 2.0], "nm"),
        ("Angstrom ", [10.0, 20.0], [1.0, 2.0], "Angstrom"),
        ("Å ", [10.0, 20.0], [1.0, 2.0], "Angstrom"),
        ("µm", [0.1, 0.2], [100.0, 200.0], "um"),
        ("inch", [1.0], [25400000.0], "inch"),
    ],
)
def test_to_nm_accepts_units_with_whitespace(raw_unit, values, expected, canonical):
    converted, unit_label = to_nm(values, raw_unit)
    assert unit_label == canonical
    assert converted.unit.is_equivalent("nm")
    assert converted.value == pytest.approx(expected)


@pytest.mark.parametrize(
    "raw_unit, expected",
    [
        (" NM", "nm"),
        ("Angstrom ", "Angstrom"),
        ("Å ", "Angstrom"),
        ("µm", "um"),
        ("inch", "inch"),
    ],
)
def test_canonical_unit_normalizes_spacing(raw_unit, expected):
    assert canonical_unit(raw_unit) == expected


def test_to_nm_accepts_numpy_arrays():
    samples = np.array([0.1, 0.2, 0.3], dtype=float)
    converted, unit_label = to_nm(samples, u.um)
    assert unit_label == "um"
    assert isinstance(converted, u.Quantity)
    assert converted.unit.is_equivalent(u.nm)
    assert converted.to_value(u.nm) == pytest.approx(samples * 1000.0)


def test_to_nm_converts_wavenumber_with_equivalency():
    values = np.array([1e4, 2e4], dtype=float)
    converted, unit_label = to_nm(values, "cm-1")
    assert unit_label == "cm-1"
    assert converted.unit.is_equivalent(u.nm)
    expected = (1.0 / (values * u.cm**-1)).to_value(u.nm)
    assert converted.value == pytest.approx(expected)


def test_to_nm_zero_wavenumber_raises():
    with pytest.raises(ValueError):
        to_nm([0.0], "cm^-1")


def test_to_nm_invalid_unit_raises():
    with pytest.raises(ValueError):
        to_nm([1.0], "not-a-unit")
