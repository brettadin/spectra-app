import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.server.units import canonical_unit, to_nm


@pytest.mark.parametrize(
    "raw_unit, values, expected",
    [
        (" NM", [1.0, 2.0], [1.0, 2.0]),
        ("Angstrom ", [10.0, 20.0], [1.0, 2.0]),
        ("Å ", [10.0, 20.0], [1.0, 2.0]),
    ],
)
def test_to_nm_accepts_units_with_whitespace(raw_unit, values, expected):
    converted = to_nm(values, raw_unit)
    assert converted == pytest.approx(expected)


@pytest.mark.parametrize(
    "raw_unit, expected",
    [
        (" NM", "nm"),
        ("Angstrom ", "Å"),
        ("Å ", "Å"),
    ],
)
def test_canonical_unit_normalizes_spacing(raw_unit, expected):
    assert canonical_unit(raw_unit) == expected
