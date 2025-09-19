import numpy as np

def resample_to_common_grid(wl_a, fl_a, wl_b, fl_b, n=2000):
    lo = max(min(wl_a), min(wl_b))
    hi = min(max(wl_a), max(wl_b))
    grid = np.linspace(lo, hi, n)
    fa = np.interp(grid, wl_a, fl_a)
    fb = np.interp(grid, wl_b, fl_b)
    return grid.tolist(), fa.tolist(), fb.tolist()

def subtract(a, b):
    return (np.array(a) - np.array(b)).tolist()

def ratio(a, b, eps=1e-12):
    b = np.array(b)
    return (np.array(a) / (b + eps)).tolist()
