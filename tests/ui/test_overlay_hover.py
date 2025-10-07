import pytest

from app.ui.main import OverlayTrace, _build_overlay_figure


def test_overlay_without_hover_uses_default_hover_fields():
    overlay = OverlayTrace(
        trace_id="test",
        label="Spectrum",
        wavelength_nm=(500.0, 600.0),
        flux=(1.0, 2.0),
    )

    fig, _ = _build_overlay_figure(
        overlays=[overlay],
        display_units="nm",
        display_mode="Flux (raw)",
        viewport_by_kind={"wavelength": (None, None)},
        reference=None,
        differential_mode="Off",
        version_tag="vtest",
    )

    assert len(fig.data) == 1
    trace = fig.data[0]

    assert trace.hoverinfo is None
    assert trace.hovertext is None

    assert list(trace.x) == [500.0, 600.0]
    assert list(trace.y) == [1.0, 2.0]


def test_overlay_normalized_display_scales_flux():
    overlay = OverlayTrace(
        trace_id="test-normalized",
        label="Spectrum",
        wavelength_nm=(500.0, 600.0),
        flux=(1.0, 2.0),
    )

    fig, _ = _build_overlay_figure(
        overlays=[overlay],
        display_units="nm",
        display_mode="Flux (normalized)",
        viewport_by_kind={"wavelength": (None, None)},
        reference=None,
        differential_mode="Off",
        version_tag="vtest",
    )

    assert len(fig.data) == 1
    y_values = fig.data[0].y
    assert max(y_values) == pytest.approx(1.0)
    assert list(y_values) == pytest.approx([0.5, 1.0])
