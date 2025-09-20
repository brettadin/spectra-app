from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.server.differential import resample_to_common_grid


def test_resample_sorts_descending_inputs():
    wl_a = [5, 3, 1]
    fl_a = [50, 30, 10]
    wl_b = [4, 2]
    fl_b = [40, 20]

    grid, fa, fb = resample_to_common_grid(wl_a, fl_a, wl_b, fl_b, n=3)

    assert grid == pytest.approx([2.0, 3.0, 4.0])
    assert fa == pytest.approx([20.0, 30.0, 40.0])
    assert fb == pytest.approx([20.0, 30.0, 40.0])


def test_resample_raises_when_no_overlap():
    wl_a = [1, 2, 3]
    fl_a = [10, 20, 30]
    wl_b = [4, 5, 6]
    fl_b = [40, 50, 60]

    with pytest.raises(ValueError, match="Wavelength ranges do not overlap"):
        resample_to_common_grid(wl_a, fl_a, wl_b, fl_b)
