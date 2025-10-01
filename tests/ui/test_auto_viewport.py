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


def test_auto_viewport_filters_to_requested_axis_kind():
    spectral = OverlayTrace(
        trace_id="spec",
        label="Spectral",
        wavelength_nm=tuple(np.linspace(450.0, 650.0, 120)),
        flux=tuple(np.sin(np.linspace(0.0, np.pi, 120))),
    )
    time_series = OverlayTrace(
        trace_id="time",
        label="Photometry",
        wavelength_nm=tuple(np.linspace(0.0, 20.0, 50)),
        flux=tuple(np.linspace(0.0, 1.0, 50)),
        axis_kind="time",
    )

    auto_range = _auto_viewport_range([spectral, time_series], axis_kind="wavelength")
    assert auto_range is not None
    low, high = auto_range
    spectral_min = min(spectral.wavelength_nm)
    spectral_max = max(spectral.wavelength_nm)
    assert spectral_min <= low <= spectral_max
    assert spectral_min <= high <= spectral_max


def test_auto_viewport_for_time_axis():
    time_trace = OverlayTrace(
        trace_id="time",
        label="Time series",
        wavelength_nm=tuple(np.linspace(0.0, 10.0, 40)),
        flux=tuple(np.cos(np.linspace(0.0, 2.0, 40))),
        axis_kind="time",
    )

    auto_range = _auto_viewport_range([time_trace], axis_kind="time")
    assert auto_range is not None
    low, high = auto_range
    assert 0.0 <= low < 1.0
    assert 9.0 < high <= 10.0
