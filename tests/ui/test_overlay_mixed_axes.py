import numpy as np

from app.ui.main import OverlayTrace, _build_overlay_figure


def test_mixed_axis_overlays_use_independent_viewports():
    wavelength_trace = OverlayTrace(
        trace_id="spec",
        label="Spectral",
        wavelength_nm=tuple(np.linspace(500.0, 600.0, 50)),
        flux=tuple(np.linspace(0.0, 1.0, 50)),
    )
    time_trace = OverlayTrace(
        trace_id="time",
        label="Light curve",
        wavelength_nm=tuple(np.linspace(0.0, 10.0, 25)),
        flux=tuple(np.linspace(1.0, 0.5, 25)),
        axis_kind="time",
    )

    fig, axis_title = _build_overlay_figure(
        overlays=[wavelength_trace, time_trace],
        display_units="nm",
        display_mode="Flux (raw)",
        normalization_mode="none",
        viewport_by_kind={"wavelength": (510.0, 530.0), "time": (None, None)},
        reference=None,
        differential_mode="Off",
        version_tag="vtest",
        axis_viewport_by_kind={"wavelength": (510.0, 530.0)},
    )

    assert axis_title == "Mixed axes (time + wavelength)"
    assert fig.layout.xaxis.range is None

    spectral_trace, time_series_trace = fig.data
    assert min(spectral_trace.x) >= 510.0
    assert max(spectral_trace.x) <= 530.0
    assert min(time_series_trace.x) == 0.0
    assert max(time_series_trace.x) == 10.0


def test_build_overlay_figure_ignores_image_axes():
    spectral_trace = OverlayTrace(
        trace_id="spec",
        label="Spectrum",
        wavelength_nm=(500.0, 510.0, 520.0),
        flux=(1.0, 0.9, 1.1),
    )
    image_trace = OverlayTrace(
        trace_id="img",
        label="Image",
        wavelength_nm=tuple(),
        flux=tuple(),
        axis="image",
        axis_kind="image",
        image={"data": [[0.0, 1.0], [2.0, 3.0]], "shape": [2, 2]},
    )

    fig, axis_title = _build_overlay_figure(
        overlays=[spectral_trace, image_trace],
        display_units="nm",
        display_mode="Flux (raw)",
        normalization_mode="none",
        viewport_by_kind={"wavelength": (None, None)},
        reference=None,
        differential_mode="Off",
        version_tag="vtest",
    )

    assert axis_title == "Wavelength (nm)"
    assert len(fig.data) == 1
