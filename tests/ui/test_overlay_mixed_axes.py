import numpy as np
import pytest

from types import MethodType

from app.ui.main import OverlayIngestResult, OverlayTrace, _build_overlay_figure


def _build_overlay(**kwargs) -> OverlayTrace:
    trace = OverlayTrace(**kwargs)
    trace.to_dataframe = MethodType(OverlayIngestResult.to_dataframe, trace)
    trace.sample = MethodType(OverlayIngestResult.sample, trace)
    trace.to_vectors = MethodType(OverlayIngestResult.to_vectors, trace)
    trace.points = len(trace.wavelength_nm)
    return trace


@pytest.fixture
def bjd_offset_overlay() -> OverlayTrace:
    base_time = np.array([0.0, 1.0, 2.0], dtype=float)
    flux = np.array([1.0, 0.9, 1.1], dtype=float)
    offset = 2457000.0
    metadata = {
        "axis_kind": "time",
        "time_range": [0.0, 2.0],
        "data_time_range": [0.0, 2.0],
        "time_unit": "day",
        "time_original_unit": "BJD - 2457000, days",
        "time_offset": offset,
    }
    provenance = {
        "units": {
            "time_converted_to": "day",
            "time_original_unit": "BJD - 2457000, days",
            "time_offset": offset,
        }
    }
    return _build_overlay(
        trace_id="bjd",
        label="Offset light curve",
        wavelength_nm=tuple(base_time.tolist()),
        flux=tuple(flux.tolist()),
        axis_kind="time",
        metadata=metadata,
        provenance=provenance,
        flux_unit="e-/s",
    )


def test_mixed_axis_overlays_use_independent_viewports():
    wavelength_trace = _build_overlay(
        trace_id="spec",
        label="Spectral",
        wavelength_nm=tuple(np.linspace(500.0, 600.0, 50)),
        flux=tuple(np.linspace(0.0, 1.0, 50)),
    )
    time_trace = _build_overlay(
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
    spectral_trace = _build_overlay(
        trace_id="spec",
        label="Spectrum",
        wavelength_nm=(500.0, 510.0, 520.0),
        flux=(1.0, 0.9, 1.1),
    )
    image_trace = _build_overlay(
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


def test_time_axis_offset_rendering(bjd_offset_overlay: OverlayTrace):
    fig, axis_title = _build_overlay_figure(
        overlays=[bjd_offset_overlay],
        display_units="nm",
        display_mode="Flux (raw)",
        normalization_mode="none",
        viewport_by_kind={"time": (None, None)},
        reference=None,
        differential_mode="Off",
        version_tag="vtest",
    )

    assert axis_title == "Time (day) — ref BJD - 2457000, days"

    plotted_trace = fig.data[0]
    assert min(plotted_trace.x) == pytest.approx(0.0)
    assert max(plotted_trace.x) == pytest.approx(2.0)

    units_meta = bjd_offset_overlay.provenance.get("units", {})
    assert units_meta.get("time_offset") == pytest.approx(2457000.0)
