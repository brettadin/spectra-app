import numpy as np

from app.ui.main import OverlayTrace, _auto_viewport_range


def test_auto_viewport_trims_long_tail():
    wavelengths = np.linspace(500.0, 1500.0, 1000)
    flux = np.concatenate([np.ones(100), np.full(900, 1e-3)])

    overlay = OverlayTrace(
        trace_id="tail",
        label="Synthetic tail",
        wavelength_nm=tuple(float(v) for v in wavelengths),
        flux=tuple(float(v) for v in flux),
    )

    auto_range = _auto_viewport_range([overlay])
    assert auto_range is not None

    auto_low, auto_high = auto_range
    raw_low = float(np.min(wavelengths))
    raw_high = float(np.max(wavelengths))
    raw_span = raw_high - raw_low
    auto_span = auto_high - auto_low

    # Ensure the automatic window remains within the data bounds.
    assert raw_low <= auto_low <= raw_high
    assert raw_low <= auto_high <= raw_high

    # Long, low-flux tails should be trimmed to focus on the core signal.
    assert auto_span < raw_span * 0.6
