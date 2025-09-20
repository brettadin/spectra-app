import numpy as np


def _to_sorted_arrays(wavelengths, fluxes):
    wavelengths = np.asarray(wavelengths, dtype=float)
    fluxes = np.asarray(fluxes, dtype=float)

    order = np.argsort(wavelengths)
    return wavelengths[order], fluxes[order]


def resample_to_common_grid(wl_a, fl_a, wl_b, fl_b, n=2000):
    wl_a, fl_a = _to_sorted_arrays(wl_a, fl_a)
    wl_b, fl_b = _to_sorted_arrays(wl_b, fl_b)

    lo = max(wl_a.min(), wl_b.min())
    hi = min(wl_a.max(), wl_b.max())

    if lo >= hi:
        raise ValueError(
            "Wavelength ranges do not overlap; cannot resample to a common grid."
        )

    grid = np.linspace(lo, hi, n)
    fa = np.interp(grid, wl_a, fl_a)
    fb = np.interp(grid, wl_b, fl_b)
    return grid.tolist(), fa.tolist(), fb.tolist()

def subtract(a, b):
    return (np.array(a) - np.array(b)).tolist()

def ratio(a, b, eps=1e-12):
    b = np.array(b)
    return (np.array(a) / (b + eps)).tolist()
